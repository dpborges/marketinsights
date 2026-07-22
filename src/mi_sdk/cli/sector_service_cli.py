"""CLI for sector performance and sector summary using Typer + Rich."""

from __future__ import annotations

import asyncio
from typing import Optional

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from ..config.settings import SDKSettings
from ..domain.exceptions import SdkError
from ..domain.models.sector_performance import SectorPerformanceRequest
from ..factory import ServiceFactory

app = typer.Typer(help="Market Insights CLI")
sector_app = typer.Typer(help="Sector-related commands")
app.add_typer(sector_app, name="sector")
console = Console()


def _run_sector_performance(symbols: Optional[str]) -> None:
    """Render sector performance for the provided symbol list."""
    syms = (
        [s.strip().upper() for s in symbols.split(",")] if symbols else DEFAULT_SYMBOLS
    )

    settings = SDKSettings()

    try:
        factory = ServiceFactory(settings)
        service = factory.create_sector_performance_service()

        request = SectorPerformanceRequest(symbols=syms)
        response = asyncio.run(service.get_sector_performance(request))

        table = Table(title="Sector Performance")
        table.add_column("Symbol")
        table.add_column("Sector")
        table.add_column("Price", justify="right")
        table.add_column("Change", justify="right")
        table.add_column("Change %", justify="right")

        for performance in response.performances:
            table.add_row(
                performance.symbol,
                performance.sector,
                f"{performance.price:.2f}",
                f"{performance.change:.2f}",
                f"{performance.change_percent:.2f}%",
            )

        console.print(table)

    except SdkError as exc:
        console.print(f"[bold red]SDK Error:[/bold red] {exc}")
        raise typer.Exit(code=1) from exc
    except Exception as exc:  # pragma: no cover - simple runtime error path
        console.print(f"[bold red]Error:[/bold red] {exc}")
        raise typer.Exit(code=2) from exc


@app.callback(invoke_without_command=True)
def main(
    ctx: typer.Context,
    symbols: Optional[str] = typer.Option(
        None, "--symbols", "-s", help="Comma-separated list of ETF symbols"
    ),
) -> None:
    """Show sector performance when invoked without a subcommand."""
    if ctx.invoked_subcommand is not None:
        return
    _run_sector_performance(symbols=symbols)

# Default SPDR sector ETF tickers
DEFAULT_SYMBOLS = [
    "XLK",
    "XLF",
    "XLV",
    "XLY",
    "XLI",
    "XLC",
    "XLE",
    "XLU",
    "XLP",
    "XLB",
    "XLRE",
]


@app.command("sector-performance")
def sector_performance(
    symbols: Optional[str] = typer.Option(
        None, "--symbols", "-s", help="Comma-separated list of ETF symbols"
    )
) -> None:
    """Show sector performance for SPDR ETF tickers."""
    _run_sector_performance(symbols=symbols)


@sector_app.command("summary")
def sector_summary(
    periods: Optional[str] = typer.Option(
        None,
        "--periods",
        "-p",
        help="Comma-separated periods: 1D, 2W, 1M, 3M, 6M, YTD, 1Y, 3Y, 5Y. Also accepts lowercase and friendly forms such as 6m, year to date, 1 year, 3 year, and 5 year.",
    ),
    symbols: Optional[str] = typer.Option(
        None,
        "--symbols",
        "-s",
        help="Comma-separated list of ETF symbols",
    ),
) -> None:
    """Show sector summaries using the SDK summary service."""

    parsed_periods = [value.strip().upper() for value in periods.split(",")] if periods else None
    parsed_symbols = [value.strip().upper() for value in symbols.split(",")] if symbols else None

    settings = SDKSettings()

    try:
        factory = ServiceFactory(settings)
        service = factory.create_sector_summary_service()
        response = service.build_sector_summary(
            symbols=parsed_symbols,
            period_codes=parsed_periods,
        )

        console.print(
            Panel.fit(
                f"[bold]Provider:[/bold] {response.get('provider', 'FMP')}\n"
                f"[bold]As of:[/bold] {response.get('asOfDate', 'N/A')}"
            )
        )

        benchmark = response.get("benchmark", {})
        benchmark_return = benchmark.get("returnPct", 0.0)
        console.print(
            f"[bold]Benchmark[/bold]: {benchmark.get('symbol', 'SPY')} -> {benchmark_return:.2f}%"
        )

        table = Table(title="Sector Summary")
        table.add_column("Symbol")
        table.add_column("Sector")
        table.add_column("Return %")
        table.add_column("Excess Return %")
        table.add_column("Rank")

        for sector in response.get("sectors", []):
            performance = sector.get("performance", {})
            relative_strength = sector.get("relativeStrength", {})
            ranking = sector.get("ranking", {})
            table.add_row(
                sector.get("symbol", "-"),
                sector.get("sectorName", "-"),
                f"{performance.get('returnPct', 0.0):.2f}",
                f"{relative_strength.get('excessReturnPct', 0.0):.2f}",
                str(ranking.get("relativeStrengthRank", "-")),
            )

        console.print(table)

    except SdkError as exc:
        console.print(f"[bold red]SDK Error:[/bold red] {exc}")
        raise typer.Exit(code=1) from exc
    except Exception as exc:  # pragma: no cover - simple runtime error path
        console.print(f"[bold red]Error:[/bold red] {exc}")
        raise typer.Exit(code=2) from exc


if __name__ == "__main__":
    app()
