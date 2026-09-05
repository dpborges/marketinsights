"""Sector summary service.

This service builds a provider-agnostic sector summary for SPDR sector ETFs and the
SPY benchmark by delegating price retrieval to an injected adapter.

Service parameters:
- symbols: optional list of SPDR ETF symbols. When omitted, the service uses all
  supported sector ETFs.
- period_codes: optional list of supported period codes. When omitted, the service
  uses a single default period of "2W".
- sort_by: optional sort metric, either "performance" or "relative_strength".
- sort_direction: optional sort direction, either "asc" or "desc".

If no parameters are provided, the service returns a summary for all SPDR ETFs for
the 2-week period, sorted by relative strength in descending order.
"""

from __future__ import annotations

import re
from collections.abc import Sequence
from datetime import date
from typing import Any

from ..domain.exceptions import DataValidationError

DEFAULT_SECTOR_SYMBOLS = [
    "XLB",
    "XLC",
    "XLE",
    "XLF",
    "XLI",
    "XLK",
    "XLP",
    "XLRE",
    "XLU",
    "XLV",
    "XLY",
]

SECTOR_METADATA = {
    "XLB": {"sectorCode": "MATERIALS", "sectorName": "Materials"},
    "XLC": {"sectorCode": "COMMUNICATION_SERVICES", "sectorName": "Communication Services"},
    "XLE": {"sectorCode": "ENERGY", "sectorName": "Energy"},
    "XLF": {"sectorCode": "FINANCIALS", "sectorName": "Financials"},
    "XLI": {"sectorCode": "INDUSTRIALS", "sectorName": "Industrials"},
    "XLK": {"sectorCode": "TECHNOLOGY", "sectorName": "Technology"},
    "XLP": {"sectorCode": "CONSUMER_STAPLES", "sectorName": "Consumer Staples"},
    "XLRE": {"sectorCode": "REAL_ESTATE", "sectorName": "Real Estate"},
    "XLU": {"sectorCode": "UTILITIES", "sectorName": "Utilities"},
    "XLV": {"sectorCode": "HEALTH_CARE", "sectorName": "Health Care"},
    "XLY": {"sectorCode": "CONSUMER_DISCRETIONARY", "sectorName": "Consumer Discretionary"},
}

SUPPORTED_PERIODS = {
    "1D": {"tradingDays": 1, "label": "1D"},
    "2W": {"tradingDays": 10, "label": "2W"},
    "1M": {"tradingDays": 21, "label": "1M"},
    "3M": {"tradingDays": 63, "label": "3M"},
    "6M": {"tradingDays": 126, "label": "6M"},
    "YTD": {"tradingDays": 252, "label": "YTD"},
    "1Y": {"tradingDays": 252, "label": "1Y"},
    "3Y": {"tradingDays": 756, "label": "3Y"},
    "5Y": {"tradingDays": 1260, "label": "5Y"},
}

PERIOD_ALIASES = {
    "1D": "1D",
    "1DAY": "1D",
    "TODAY": "1D",
    "2W": "2W",
    "2WK": "2W",
    "2WEEK": "2W",
    "2WEEKS": "2W",
    "1M": "1M",
    "1MO": "1M",
    "1MONTH": "1M",
    "1MONTHS": "1M",
    "3M": "3M",
    "3MO": "3M",
    "3MONTH": "3M",
    "3MONTHS": "3M",
    "6M": "6M",
    "6MO": "6M",
    "6MONTH": "6M",
    "6MONTHS": "6M",
    "YTD": "YTD",
    "YEARTODATE": "YTD",
    "1Y": "1Y",
    "1YR": "1Y",
    "1YEAR": "1Y",
    "1YEARS": "1Y",
    "3Y": "3Y",
    "3YR": "3Y",
    "3YEAR": "3Y",
    "3YEARS": "3Y",
    "5Y": "5Y",
    "5YR": "5Y",
    "5YEAR": "5Y",
    "5YEARS": "5Y",
}

SUPPORTED_SORT_FIELDS = ("performance", "relative_strength")
SUPPORTED_SORT_DIRECTIONS = ("asc", "desc")


class SectorSummaryService:
    """Build sector performance summaries from historical price data."""

    def __init__(self, adapter: Any) -> None:
        self.adapter = adapter

    def build_sector_summary(
        self,
        symbols: Sequence[str] | None = None,
        period_codes: Sequence[str] | None = None,
        sort_by: str = "relative_strength",
        sort_direction: str = "desc",
    ) -> dict[str, Any]:
        """Build a sector summary for the requested symbols and periods."""

        requested_symbols = self._normalize_symbols(symbols)
        requested_periods = self._normalize_periods(period_codes)
        normalized_sort_by = self._normalize_sort_by(sort_by)
        normalized_sort_direction = self._normalize_sort_direction(sort_direction)
        as_of_date = date.today().isoformat()

        errors: list[dict[str, Any]] = []
        benchmark_periods: list[dict[str, Any]] = []
        sector_periods: dict[str, list[dict[str, Any]]] = {
            symbol: [] for symbol in requested_symbols
        }
        last_prices: dict[str, Any] = {}

        for period_code in requested_periods:
            period_config = SUPPORTED_PERIODS[period_code]
            response = self.adapter.get_historical_prices(
                [*requested_symbols, "SPY"],
                as_of_date=as_of_date,
                lookback_periods=period_config["tradingDays"],
            )

            prices = {price_item["symbol"]: price_item for price_item in response.get("prices", [])}
            last_prices = prices
            errors.extend(response.get("errors", []))

            benchmark_price = prices.get("SPY")
            if benchmark_price is None:
                raise DataValidationError("The benchmark symbol SPY is required")

            benchmark_return_pct = self._calculate_return_pct(
                benchmark_price["current"]["adjustedClose"],
                benchmark_price["lookback"]["adjustedClose"],
            )
            benchmark_periods.append(
                {
                    "periodCode": period_code,
                    "requestedTradingDays": period_config["tradingDays"],
                    "currentDate": benchmark_price["current"]["date"],
                    "lookbackDate": benchmark_price["lookback"]["date"],
                    "performance": {"returnPct": round(benchmark_return_pct, 4)},
                }
            )

            per_period_summaries: list[dict[str, Any]] = []
            for symbol in requested_symbols:
                symbol_price = prices.get(symbol)
                if symbol_price is None:
                    continue

                sector_return_pct = self._calculate_return_pct(
                    symbol_price["current"]["adjustedClose"],
                    symbol_price["lookback"]["adjustedClose"],
                )
                absolute_change = (
                    symbol_price["current"]["adjustedClose"]
                    - symbol_price["lookback"]["adjustedClose"]
                )
                excess_return_pct = sector_return_pct - benchmark_return_pct
                summary = {
                    "periodCode": period_code,
                    "symbol": symbol,
                    "current": {
                        "date": symbol_price["current"]["date"],
                        "adjustedClose": symbol_price["current"]["adjustedClose"],
                    },
                    "lookback": {
                        "date": symbol_price["lookback"]["date"],
                        "adjustedClose": symbol_price["lookback"]["adjustedClose"],
                    },
                    "performance": {
                        "absoluteChange": round(absolute_change, 4),
                        "returnPct": round(sector_return_pct, 4),
                    },
                    "relativeStrength": {
                        "excessReturnPct": round(excess_return_pct, 4),
                        "outperformedBenchmark": excess_return_pct > 0,
                    },
                }
                per_period_summaries.append(summary)

            ranked_period_summaries = sorted(
                per_period_summaries,
                key=lambda item: item["relativeStrength"]["excessReturnPct"],
                reverse=True,
            )
            return_ranks = self._assign_ranks(
                ranked_period_summaries,
                "performance",
                "returnPct",
            )
            strength_ranks = self._assign_ranks(
                ranked_period_summaries,
                "relativeStrength",
                "excessReturnPct",
            )

            for summary, return_rank, strength_rank in zip(
                ranked_period_summaries,
                return_ranks,
                strength_ranks,
                strict=True,
            ):
                summary["ranking"] = {
                    "returnRank": return_rank,
                    "relativeStrengthRank": strength_rank,
                }

            ranked_period_summaries.sort(key=lambda item: item["ranking"]["relativeStrengthRank"])

            for summary in ranked_period_summaries:
                sector_periods[summary["symbol"]].append(summary)

        sectors_payload: list[dict[str, Any]] = []
        for symbol in requested_symbols:
            sector_period_summary = sector_periods[symbol]
            metadata = SECTOR_METADATA[symbol]
            if len(requested_periods) == 1:
                first_summary = sector_period_summary[0]
                sectors_payload.append(
                    {
                        "symbol": symbol,
                        "sectorCode": metadata["sectorCode"],
                        "sectorName": metadata["sectorName"],
                        "current": first_summary["current"],
                        "lookback": first_summary["lookback"],
                        "performance": first_summary["performance"],
                        "relativeStrength": first_summary["relativeStrength"],
                        "ranking": first_summary["ranking"],
                    }
                )
            else:
                sectors_payload.append(
                    {
                        "symbol": symbol,
                        "sectorCode": metadata["sectorCode"],
                        "sectorName": metadata["sectorName"],
                        "periods": [
                            {
                                "periodCode": item["periodCode"],
                                "performance": item["performance"],
                                "relativeStrength": item["relativeStrength"],
                                "ranking": item["ranking"],
                            }
                            for item in sector_period_summary
                        ],
                    }
                )

        sectors_payload.sort(
            key=lambda item: self._sort_value(item, normalized_sort_by),
            reverse=normalized_sort_direction == "desc",
        )

        if len(requested_periods) == 1:
            return {
                "provider": "FMP",
                "status": "SUCCESS" if not errors else "PARTIAL_SUCCESS",
                "asOfDate": as_of_date,
                "period": {
                    "periodCode": requested_periods[0],
                    "requestedTradingDays": SUPPORTED_PERIODS[requested_periods[0]]["tradingDays"],
                    "currentDate": as_of_date,
                    "lookbackDate": benchmark_periods[0]["lookbackDate"],
                },
                "benchmark": {
                    "symbol": "SPY",
                    "currentAdjustedClose": round(
                        self._get_benchmark_price(prices=last_prices, key="current"),
                        4,
                    ),
                    "lookbackAdjustedClose": round(
                        self._get_benchmark_price(prices=last_prices, key="lookback"),
                        4,
                    ),
                    "absoluteChange": round(
                        self._get_benchmark_price(prices=last_prices, key="current")
                        - self._get_benchmark_price(prices=last_prices, key="lookback"),
                        4,
                    ),
                    "returnPct": round(
                        self._calculate_return_pct(
                            self._get_benchmark_price(prices=last_prices, key="current"),
                            self._get_benchmark_price(prices=last_prices, key="lookback"),
                        ),
                        4,
                    ),
                },
                "requestedSectorCount": len(requested_symbols),
                "successfulSectorCount": len(requested_symbols),
                "failedSectorCount": len(errors),
                "sectors": sectors_payload,
                "errors": errors,
            }

        return {
            "provider": "FMP",
            "status": "SUCCESS" if not errors else "PARTIAL_SUCCESS",
            "asOfDate": as_of_date,
            "benchmark": {
                "symbol": "SPY",
                "periods": benchmark_periods,
            },
            "requestedSectorCount": len(requested_symbols),
            "successfulSectorCount": len(requested_symbols),
            "failedSectorCount": len(errors),
            "sectors": sectors_payload,
            "errors": errors,
        }

    def _sort_value(self, sector: dict[str, Any], sort_by: str) -> float:
        """Return the selected metric, using the first period for multi-period output."""

        summary = sector["periods"][0] if "periods" in sector else sector
        if sort_by == "performance":
            return float(summary["performance"]["returnPct"])
        return float(summary["relativeStrength"]["excessReturnPct"])

    def _get_benchmark_price(self, prices: dict[str, Any], key: str) -> float:
        benchmark_price = prices.get("SPY")
        if benchmark_price is None:
            return 0.0
        return float(benchmark_price[key]["adjustedClose"])

    def _normalize_symbols(self, symbols: Sequence[str] | None) -> list[str]:
        if not symbols:
            return list(DEFAULT_SECTOR_SYMBOLS)

        normalized = [symbol.upper() for symbol in symbols]
        invalid_symbols = [symbol for symbol in normalized if symbol not in SECTOR_METADATA]
        if invalid_symbols:
            raise DataValidationError(f"Unsupported sector symbols: {', '.join(invalid_symbols)}")
        return normalized

    def _normalize_periods(self, period_codes: Sequence[str] | None) -> list[str]:
        if not period_codes:
            return ["2W"]

        normalized: list[str] = []
        invalid_periods: list[str] = []
        for period_code in period_codes:
            key = re.sub(r"[\s_-]+", "", period_code.strip()).upper()
            candidate = PERIOD_ALIASES.get(key)
            if candidate is None:
                invalid_periods.append(period_code)
                continue
            normalized.append(candidate)

        if invalid_periods:
            raise DataValidationError(f"Unsupported period codes: {', '.join(invalid_periods)}")
        return normalized

    def _normalize_sort_by(self, sort_by: str) -> str:
        if not isinstance(sort_by, str):
            raise DataValidationError("sort_by must be either 'performance' or 'relative_strength'")
        normalized = sort_by.strip().lower()
        if normalized not in SUPPORTED_SORT_FIELDS:
            raise DataValidationError("sort_by must be either 'performance' or 'relative_strength'")
        return normalized

    def _normalize_sort_direction(self, sort_direction: str) -> str:
        if not isinstance(sort_direction, str):
            raise DataValidationError("sort_direction must be either 'asc' or 'desc'")
        normalized = sort_direction.strip().lower()
        if normalized not in SUPPORTED_SORT_DIRECTIONS:
            raise DataValidationError("sort_direction must be either 'asc' or 'desc'")
        return normalized

    def _assign_ranks(
        self,
        items: list[dict[str, Any]],
        nested_key: str,
        metric_key: str,
    ) -> list[int]:
        ordered = sorted(
            items,
            key=lambda item: item[nested_key][metric_key],
            reverse=True,
        )
        rankings: list[int] = []
        for _ in ordered:
            rankings.append(len(rankings) + 1)
        return rankings

    def _calculate_return_pct(self, current: float, lookback: float) -> float:
        if lookback == 0:
            return 0.0
        return ((current - lookback) / lookback) * 100.0
