"""Tests for the sector summary CLI."""

from __future__ import annotations

from typer.testing import CliRunner

from mi_sdk.cli import sector_service_cli
from mi_sdk.factory import ServiceFactory


class StubSectorSummaryService:
    def __init__(self) -> None:
        self.calls: list[tuple[list[str] | None, list[str] | None]] = []

    def build_sector_summary(self, symbols=None, period_codes=None):
        self.calls.append((symbols, period_codes))
        return {
            "provider": "FMP",
            "status": "SUCCESS",
            "asOfDate": "2026-07-16",
            "period": {"periodCode": "2W", "requestedTradingDays": 10},
            "benchmark": {"symbol": "SPY", "returnPct": 3.2},
            "requestedSectorCount": 1,
            "successfulSectorCount": 1,
            "failedSectorCount": 0,
            "sectors": [
                {
                    "symbol": "XLK",
                    "sectorCode": "TECHNOLOGY",
                    "sectorName": "Technology",
                    "performance": {"returnPct": 5.9},
                    "relativeStrength": {"excessReturnPct": 2.7, "outperformedBenchmark": True},
                    "ranking": {"returnRank": 1, "relativeStrengthRank": 1},
                }
            ],
            "errors": [],
        }


def test_sector_summary_cli_uses_default_period_and_symbols(monkeypatch):
    service = StubSectorSummaryService()

    monkeypatch.setattr(
        ServiceFactory,
        "create_sector_summary_service",
        lambda self: service,
    )

    runner = CliRunner()
    result = runner.invoke(sector_service_cli.app, ["sector", "summary"])

    assert result.exit_code == 0
    assert "XLK" in result.output
    assert service.calls[0] == (None, None)


def test_sector_summary_cli_supports_periods_and_symbols(monkeypatch):
    service = StubSectorSummaryService()

    monkeypatch.setattr(
        ServiceFactory,
        "create_sector_summary_service",
        lambda self: service,
    )

    runner = CliRunner()
    result = runner.invoke(
        sector_service_cli.app,
        ["sector", "summary", "--periods", "1D,2W", "--symbols", "XLK,XLE,XLU"],
    )

    assert result.exit_code == 0
    assert "XLK" in result.output
    assert service.calls[0] == (["XLK", "XLE", "XLU"], ["1D", "2W"])
