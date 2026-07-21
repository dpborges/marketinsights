"""Tests for the sector summary service.

Run from the project root with:
    pytest tests/test_sector_summary_service.py -q
"""

from __future__ import annotations

from typing import Any

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


def test_build_summary_supports_multiple_periods() -> None:
    adapter = StubAdapter(
        {
            "SPY": {"current": 100.0, "lookback": 97.0},
            "XLK": {"current": 95.0, "lookback": 90.0},
        }
    )
    service = SectorSummaryService(adapter=adapter)

    result = service.build_sector_summary(symbols=["XLK"], period_codes=["2W", "1M"])

    assert result["benchmark"]["periods"][0]["periodCode"] == "2W"
    assert result["benchmark"]["periods"][1]["periodCode"] == "1M"
    assert result["sectors"][0]["symbol"] == "XLK"
    assert len(result["sectors"][0]["periods"]) == 2
