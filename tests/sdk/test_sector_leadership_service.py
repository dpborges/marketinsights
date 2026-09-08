"""Run in Git Bash: ./.venv/Scripts/python.exe -m pytest tests/sdk/test_sector_leadership_service.py -q."""

from copy import deepcopy
from typing import Any
from unittest.mock import AsyncMock

import pytest

from mi_sdk.domain.exceptions import DataValidationError, ProviderUnavailableError
from mi_sdk.services.sector_leadership_service import (
    SectorLeadershipService,
    interpret_sector_leadership,
)
from mi_sdk.services.sector_summary_service import DEFAULT_SECTOR_SYMBOLS, SECTOR_METADATA


def summary_fixture() -> dict[str, Any]:
    """Provide distinct momentum and confirmation, plus an anchor strength tie."""
    orders = {
        "2W": ["XLK", "XLC", "XLE", "XLU", "XLV", "XLB", "XLF", "XLI", "XLP", "XLRE", "XLY"],
        "1M": ["XLK", "XLC", "XLI", "XLF", "XLB", "XLE", "XLP", "XLRE", "XLU", "XLV", "XLY"],
        "3M": ["XLK", "XLI", "XLB", "XLU", "XLV", "XLE", "XLF", "XLC", "XLP", "XLRE", "XLY"],
    }
    sectors = []
    for symbol in DEFAULT_SECTOR_SYMBOLS:
        periods = []
        for code, order in orders.items():
            rank = order.index(symbol) + 1
            strength = 12 - rank
            if code == "1M" and symbol == "XLC":
                strength = 11
            periods.append(
                {
                    "periodCode": code,
                    "relativeStrength": {
                        "excessReturnPct": strength,
                        "outperformedBenchmark": True,
                    },
                    "ranking": {"returnRank": rank, "relativeStrengthRank": 1},
                }
            )
        sectors.append(
            {
                "symbol": symbol,
                "sectorName": SECTOR_METADATA[symbol]["sectorName"],
                "periods": periods,
            }
        )
    return {
        "benchmark": {"symbol": "SPY"},
        "asOfDate": "2026-09-06",
        "requestedSectorCount": 11,
        "sectors": sectors,
        "errors": [],
    }


async def test_sector_leadership_top_three() -> None:
    source = AsyncMock()
    source.build_sector_summary.return_value = summary_fixture()
    service = SectorLeadershipService(source)
    result = await service.build_sector_leadership(periods="2W,1M,3M", top_n=3)
    source.build_sector_summary.assert_awaited_once_with(
        period_codes=["2W", "1M", "3M"], sort_by="relative_strength", sort_direction="desc"
    )
    assert result["benchmark"] == "SPY"
    assert result["asOfDate"] == "2026-09-06"
    assert (
        result["requestedSectorCount"],
        result["successfulSectorCount"],
        result["failedSectorCount"],
    ) == (11, 11, 0)
    assert [s["symbol"] for s in result["sectors"]] == ["XLK", "XLC", "XLI"]
    assert [s["relativeStrengthRank"] for s in result["sectors"]] == [1, 2, 3]
    assert [s["interpretation"]["status"] for s in result["sectors"]] == [
        "strong_established_leader",
        "emerging_leader",
        "leader_losing_momentum",
    ]
    assert [s["interpretation"]["supports_entry"] for s in result["sectors"]] == [True, True, False]
    assert result["sectors"][2]["returnRank"] == 3
    assert result["sectors"][0]["sector"] == "Technology"
    assert result["errors"] == []
    for periods, top_n in [("2W,1M", 3), ("2W,1M,3M", 0), ("2W,1M,3M", True)]:
        with pytest.raises(DataValidationError):
            await service.build_sector_leadership(periods=periods, top_n=top_n)
    source.build_sector_summary.side_effect = ProviderUnavailableError("Unavailable")
    with pytest.raises(ProviderUnavailableError):
        await service.build_sector_leadership(top_n=3)


async def test_sector_leadership_top_five() -> None:
    source = AsyncMock()
    payload = summary_fixture()
    source.build_sector_summary.return_value = payload
    service = SectorLeadershipService(source)
    result = await service.build_sector_leadership(periods=["2W", "1M", "3M"], top_n=5)
    source.build_sector_summary.assert_awaited_once_with(
        period_codes=["2W", "1M", "3M"], sort_by="relative_strength", sort_direction="desc"
    )
    assert [s["symbol"] for s in result["sectors"]] == ["XLK", "XLC", "XLI", "XLF", "XLB"]
    assert [s["relativeStrengthRank"] for s in result["sectors"]] == [1, 2, 3, 4, 5]
    assert result["sectors"][3]["interpretation"]["status"] == "mixed_transitional"
    assert interpret_sector_leadership(1, 6, 6) == "early_rotation_candidate"
    assert interpret_sector_leadership(6, 6, 6) == "weak_sector"
    assert interpret_sector_leadership(1, 6, 1) == "mixed_transitional"
    assert interpret_sector_leadership(6, 6, 1) == "mixed_transitional"

    # Force same-period return ties: XLK wins on the other periods.
    for sector in payload["sectors"]:
        if sector["symbol"] == "XLC":
            sector["periods"][1]["ranking"]["returnRank"] = 1
    assert (await service.build_sector_leadership())["sectors"][0]["symbol"] == "XLK"
    # Equal return ranks across all periods leave alphabetical order as fallback.
    for sector in payload["sectors"]:
        if sector["symbol"] in {"XLK", "XLC"}:
            for period in sector["periods"]:
                period["ranking"]["returnRank"] = 1
    payload["sectors"].reverse()
    assert (await service.build_sector_leadership())["sectors"][0]["symbol"] == "XLC"

    partial = deepcopy(payload)
    partial["sectors"][0]["periods"].pop()
    partial["errors"] = [{"symbol": partial["sectors"][0]["symbol"], "message": "Missing prices"}]
    source.build_sector_summary.return_value = partial
    result = await service.build_sector_leadership(top_n=5)
    assert len(result["sectors"]) == 5
    assert result["successfulSectorCount"] == 10
    assert result["failedSectorCount"] == 1
    assert result["errors"][0] == partial["errors"][0]
    assert len(partial["errors"]) == 1
