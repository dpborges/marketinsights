"""Tests for the sector summary service.

Run from the project root with:
    python -m pytest tests/test_sector_summary_service.py -q
"""

from __future__ import annotations

from typing import Any

import pytest

from mi_sdk.domain.exceptions import DataValidationError
from mi_sdk.services.sector_summary_service import SectorSummaryService


class StubAdapter:
    """Simple adapter stub for service tests."""

    def __init__(self, prices: dict[str, dict[str, Any]]) -> None:
        self._prices = prices
        self.calls: list[tuple[list[str], str, int]] = []

    def get_historical_prices(
        self,
        symbols: list[str],
        as_of_date: str,
        lookback_periods: int,
    ) -> dict[str, Any]:
        self.calls.append((symbols, as_of_date, lookback_periods))
        return {
            "provider": "FMP",
            "status": "SUCCESS",
            "requestedSymbolCount": len(symbols),
            "successfulSymbolCount": len(symbols),
            "failedSymbolCount": 0,
            "prices": [
                {
                    "symbol": symbol,
                    "current": {
                        "date": as_of_date,
                        "adjustedClose": payload["current"],
                    },
                    "lookback": {
                        "date": "2026-07-02",
                        "adjustedClose": payload["lookback"],
                    },
                }
                for symbol, payload in self._prices.items()
                if symbol in symbols
            ],
        }


def test_build_summary_uses_default_symbols_and_period() -> None:
    adapter = StubAdapter(
        {
            "SPY": {"current": 100.0, "lookback": 97.0},
            "XLB": {"current": 90.0, "lookback": 85.0},
            "XLC": {"current": 91.0, "lookback": 86.0},
            "XLE": {"current": 92.0, "lookback": 87.0},
            "XLF": {"current": 93.0, "lookback": 88.0},
            "XLI": {"current": 94.0, "lookback": 89.0},
            "XLK": {"current": 95.0, "lookback": 90.0},
            "XLP": {"current": 96.0, "lookback": 91.0},
            "XLRE": {"current": 97.0, "lookback": 92.0},
            "XLU": {"current": 98.0, "lookback": 93.0},
            "XLV": {"current": 99.0, "lookback": 94.0},
            "XLY": {"current": 100.0, "lookback": 95.0},
        }
    )
    service = SectorSummaryService(adapter=adapter)

    result = service.build_sector_summary()

    assert result["requestedSectorCount"] == 11
    assert result["successfulSectorCount"] == 11
    assert result["benchmark"]["symbol"] == "SPY"
    assert result["period"]["periodCode"] == "2W"
    assert result["sectors"][0]["ranking"]["relativeStrengthRank"] == 1
    assert result["sectors"][0]["symbol"] == "XLB"


def test_build_summary_supports_multiple_periods() -> None:
    adapter = StubAdapter(
        {
            "SPY": {"current": 100.0, "lookback": 97.0},
            "XLK": {"current": 95.0, "lookback": 90.0},
        }
    )
    service = SectorSummaryService(adapter=adapter)

    result = service.build_sector_summary(
        symbols=["XLK"],
        period_codes=["2W", "1M"],
        sort_by="performance",
        sort_direction="asc",
    )

    assert result["benchmark"]["periods"][0]["periodCode"] == "2W"
    assert result["benchmark"]["periods"][1]["periodCode"] == "1M"
    assert result["sectors"][0]["symbol"] == "XLK"
    assert len(result["sectors"][0]["periods"]) == 2


def test_build_summary_normalizes_alias_period_codes() -> None:
    adapter = StubAdapter(
        {
            "SPY": {"current": 100.0, "lookback": 97.0},
            "XLK": {"current": 95.0, "lookback": 90.0},
        }
    )
    service = SectorSummaryService(adapter=adapter)

    result = service.build_sector_summary(
        symbols=["XLK"], period_codes=["6m", "year to date", "1 year"]
    )

    assert [period["periodCode"] for period in result["benchmark"]["periods"]] == [
        "6M",
        "YTD",
        "1Y",
    ]


def test_build_summary_sorts_by_performance_ascending() -> None:
    adapter = StubAdapter(
        {
            "SPY": {"current": 100.0, "lookback": 100.0},
            "XLK": {"current": 110.0, "lookback": 100.0},
            "XLE": {"current": 95.0, "lookback": 100.0},
            "XLV": {"current": 105.0, "lookback": 100.0},
        }
    )
    service = SectorSummaryService(adapter=adapter)

    result = service.build_sector_summary(
        symbols=["XLK", "XLE", "XLV"],
        period_codes=["2W"],
        sort_by="performance",
        sort_direction="asc",
    )

    assert [sector["symbol"] for sector in result["sectors"]] == ["XLE", "XLV", "XLK"]


@pytest.mark.parametrize(
    ("parameter", "value"),
    [("sort_by", "return"), ("sort_direction", "up")],
)
def test_build_summary_rejects_invalid_sort_options(parameter: str, value: str) -> None:
    service = SectorSummaryService(adapter=StubAdapter({}))

    with pytest.raises(DataValidationError, match=parameter):
        service.build_sector_summary(**{parameter: value})
