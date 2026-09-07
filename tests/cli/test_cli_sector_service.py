"""Tests for the sector performance CLI"""

from typer.testing import CliRunner

from mi_sdk.domain.models.sector_performance import (
    SectorPerformance,
    SectorPerformanceResponse,
)
from mi_sdk.factory import ServiceFactory


class FakeService:
    async def get_sector_performance(self, request):
        performances = [
            SectorPerformance(
                symbol="XLK",
                sector="Technology",
                price=100.0,
                change=1.0,
                change_percent=1.0,
            )
        ]
        return SectorPerformanceResponse(performances=performances)


def test_cli_sector_performance_default(monkeypatch):
    """CLI prints default sector performance table"""
    from mi_sdk.cli import sector_service_cli

    monkeypatch.setattr(ServiceFactory, "create_sector_performance_service", lambda self: FakeService())

    runner = CliRunner()
    result = runner.invoke(sector_service_cli.app, [])

    assert result.exit_code == 0
    assert "XLK" in result.output
    assert "Technology" in result.output


def test_cli_sector_performance_custom_symbols(monkeypatch):
    """CLI accepts --symbols option and prints given symbols"""
    from mi_sdk.cli import sector_service_cli

    monkeypatch.setattr(ServiceFactory, "create_sector_performance_service", lambda self: FakeService())

    runner = CliRunner()
    result = runner.invoke(sector_service_cli.app, ["--symbols", "XLK,XLV"])

    assert result.exit_code == 0
    assert "XLK" in result.output
