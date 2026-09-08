"""Sector leadership anchored on 1M relative strength against SPY.

The asynchronous summary SDK owns data retrieval. Only sectors with all three
periods qualify. Counts describe coverage before truncation to ``top_n``.
Same-period return rank breaks strength ties (lower ranks are better), followed
by the number of pairwise period wins within the remaining tied group, then symbol.
Counting wins also produces a stable order when pairwise preferences form a cycle.
"""

from __future__ import annotations

from collections.abc import Sequence
from itertools import groupby
from typing import Any, Protocol

from ..domain.exceptions import DataValidationError

LEADERSHIP_PERIODS = ("2W", "1M", "3M")


class SectorSummarySource(Protocol):
    """Summary dependency, implemented by SectorSummaryService."""

    async def build_sector_summary(
        self,
        symbols: Sequence[str] | None = None,
        period_codes: Sequence[str] | None = None,
        sort_by: str = "relative_strength",
        sort_direction: str = "desc",
    ) -> dict[str, Any]: ...


def interpret_sector_leadership(rank_2w: int, rank_1m: int, rank_3m: int, top_n: int = 5) -> str:
    """Classify all eight combinations of momentum, anchor, and confirmation."""
    pattern = (rank_2w <= top_n, rank_1m <= top_n, rank_3m <= top_n)
    return {
        (True, True, True): "strong_established_leader",
        (True, True, False): "emerging_leader",
        (False, True, True): "leader_losing_momentum",
        (True, False, False): "early_rotation_candidate",
        (False, False, False): "weak_sector",
    }.get(pattern, "mixed_transitional")


class SectorLeadershipService:
    """Select the top N sectors using the 1M anchor and three-period context."""

    def __init__(self, summary_service: SectorSummarySource) -> None:
        self.summary_service = summary_service

    async def build_sector_leadership(
        self, periods: Sequence[str] | str | None = None, top_n: int = 5
    ) -> dict[str, Any]:
        """Return leadership; periods must contain exactly 2W, 1M, and 3M.

        Output ranks, returnRank, and outperformedBenchmark refer to 1M.
        Only established and emerging leaders support entry. SDK exceptions
        propagate unchanged; partial summary errors are retained in the response.
        """
        if isinstance(top_n, bool) or not isinstance(top_n, int) or not 1 <= top_n <= 11:
            raise DataValidationError("top_n must be an integer between 1 and 11")
        requested = LEADERSHIP_PERIODS if periods is None else periods
        if isinstance(requested, str):
            requested = requested.split(",")
        if (
            any(not isinstance(period, str) for period in requested)
            or len(requested) != 3
            or {period.strip().upper() for period in requested} != set(LEADERSHIP_PERIODS)
        ):
            raise DataValidationError("periods must contain exactly 2W, 1M, and 3M")

        summary = await self.summary_service.build_sector_summary(
            period_codes=list(LEADERSHIP_PERIODS),
            sort_by="relative_strength",
            sort_direction="desc",
        )
        errors = list(summary.get("errors", []))
        sectors = summary["sectors"]
        period_data = {
            sector["symbol"]: {item["periodCode"]: item for item in sector["periods"]}
            for sector in sectors
        }
        complete = []
        for sector in sectors:
            missing = set(LEADERSHIP_PERIODS) - period_data[sector["symbol"]].keys()
            if missing:
                errors.append(
                    {
                        "symbol": sector["symbol"],
                        "code": "INCOMPLETE_PERIOD_DATA",
                        "message": f"Missing leadership periods: {', '.join(sorted(missing))}",
                    }
                )
            else:
                complete.append(sector)

        ranks: dict[str, dict[str, int]] = {}
        for period in LEADERSHIP_PERIODS:
            # Rank every available observation so missing confirmation data does
            # not artificially promote other sectors into a period's top N.
            available = [symbol for symbol, data in period_data.items() if period in data]

            def primary_key(symbol: str, period: str = period) -> tuple[float, int]:
                data = period_data[symbol][period]
                return (-data["relativeStrength"]["excessReturnPct"], data["ranking"]["returnRank"])

            ordered: list[str] = []
            for _, group in groupby(sorted(available, key=primary_key), key=primary_key):
                tied = list(group)

                def wins(symbol: str, tied: list[str] = tied) -> int:
                    return sum(
                        period_data[symbol][code]["ranking"]["returnRank"]
                        < period_data[other][code]["ranking"]["returnRank"]
                        for other in tied
                        if other != symbol
                        for code in LEADERSHIP_PERIODS
                        if code in period_data[symbol] and code in period_data[other]
                    )

                ordered.extend(sorted(tied, key=lambda symbol: (-wins(symbol), symbol)))
            ranks[period] = {symbol: rank for rank, symbol in enumerate(ordered, start=1)}

        complete.sort(key=lambda sector: ranks["1M"][sector["symbol"]])
        result_sectors = []
        for sector in complete[:top_n]:
            symbol = sector["symbol"]
            status = interpret_sector_leadership(
                *(ranks[period][symbol] for period in LEADERSHIP_PERIODS), top_n=top_n
            )
            anchor = period_data[symbol]["1M"]
            positions = ", ".join(
                f"{period}: {ranks[period][symbol]}" for period in LEADERSHIP_PERIODS
            )
            result_sectors.append(
                {
                    "symbol": symbol,
                    "sector": sector["sectorName"],
                    "relativeStrengthRank": ranks["1M"][symbol],
                    "returnRank": anchor["ranking"]["returnRank"],
                    "outperformedBenchmark": anchor["relativeStrength"]["outperformedBenchmark"],
                    "interpretation": {
                        "status": status,
                        "supports_entry": status
                        in {"strong_established_leader", "emerging_leader"},
                        "reason": f"Relative strength ranks ({positions}); top {top_n} cutoff.",
                    },
                }
            )
        requested_count = summary["requestedSectorCount"]
        return {
            "benchmark": summary["benchmark"]["symbol"],
            "asOfDate": summary["asOfDate"],
            "requestedSectorCount": requested_count,
            "successfulSectorCount": len(complete),
            "failedSectorCount": requested_count - len(complete),
            "sectors": result_sectors,
            "errors": errors,
        }
