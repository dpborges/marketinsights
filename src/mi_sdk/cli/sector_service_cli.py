"""CLI for sector performance using Typer + Rich"""

from __future__ import annotations

import asyncio
from typing import Optional

import typer
from rich.console import Console
from rich.table import Table

from ..config.settings import SDKSettings
from ..factory import ServiceFactory
from ..domain.models.sector_performance import SectorPerformanceRequest
from ..domain.exceptions import SdkError

app = typer.Typer(help="Market Insights CLI")
console = Console()

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
    """Show sector performance for SPDR ETF tickers.

    If `--symbols` is omitted, the command will display the default SPDR tickers.
    """

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

        for p in response.performances:
            table.add_row(
                p.symbol,
                p.sector,
                f"{p.price:.2f}",
                f"{p.change:.2f}",
                f"{p.change_percent:.2f}%",
            )

        console.print(table)

    except SdkError as e:
        console.print(f"[bold red]SDK Error:[/bold red] {e}")
        raise typer.Exit(code=1)
    except Exception as e:  # pragma: no cover - simple runtime error path
        console.print(f"[bold red]Error:[/bold red] {e}")
        raise typer.Exit(code=2)


if __name__ == "__main__":
    app()
