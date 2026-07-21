"""Command-line runner for FMPAdapter services."""

from __future__ import annotations

import json
import sys
from typing import Any

from dotenv import load_dotenv

from .fmp_adapter import FMPAdapter
from ...domain.exceptions import (
    ConfigurationError,
    DataValidationError,
    SdkError,
    UnsupportedOperationError,
)

SERVICE_METHODS = {
    "get_historical_prices": "Get historical pricing for SPDR sector ETFs and SPY",
}


def _prompt(text: str) -> str:
    try:
        return input(text).strip()
    except EOFError:
        raise ConfigurationError("Input was closed before parameters were provided.")


def _prompt_for_historical_prices() -> dict[str, Any]:
    print("Enter symbols as comma-separated values, e.g. XLK,XLV,SPY")
    raw_symbols = _prompt("Symbols: ")
    print("Enter as_of_date in YYYY-MM-DD format, e.g. 2026-07-16")
    raw_date = _prompt("As of date: ")
    print("Enter lookback_periods as a whole number, e.g. 1")
    raw_lookback = _prompt("Lookback periods: ")

    symbols = [s.strip().upper() for s in raw_symbols.split(",") if s.strip()]
    try:
        lookback = int(raw_lookback)
    except ValueError as exc:
        raise DataValidationError("lookback_periods must be a whole number.") from exc

    return {
        "symbols": symbols,
        "as_of_date": raw_date,
        "lookback_periods": lookback,
    }


def _print_services() -> None:
    print("Available FMP services:")
    for name, description in SERVICE_METHODS.items():
        print(f"  - {name}: {description}")


def _run_service(method_name: str, parameters: dict[str, Any]) -> None:
    adapter = FMPAdapter()
    if method_name == "get_historical_prices":
        response = adapter.get_historical_prices(
            symbols=parameters["symbols"],
            as_of_date=parameters["as_of_date"],
            lookback_periods=parameters["lookback_periods"],
        )
        print(json.dumps(response, indent=2))
    else:
        raise UnsupportedOperationError(f"Unknown service: {method_name}")


def main(argv: list[str] | None = None) -> None:
    """Run an FMPAdapter service from the command line.

    Exact syntax:
    python -m mi_sdk.providers.fmp.fmp_adapter_run
    python -m mi_sdk.providers.fmp.fmp_adapter_run get_historical_prices XLK,XLV,SPY 2026-07-16 1
    """

    argv = list(argv) if argv is not None else sys.argv[1:]
    load_dotenv()

    if len(argv) == 0:
        _print_services()
        method = _prompt("Choose a service: ")
        if method not in SERVICE_METHODS:
            raise UnsupportedOperationError(f"Unknown service: {method}")
        if method == "get_historical_prices":
            params = _prompt_for_historical_prices()
            _run_service(method, params)
        return

    method = argv[0]
    if method == "get_historical_prices":
        if len(argv) != 4:
            raise DataValidationError(
                "Expected arguments: get_historical_prices SYMBOLS as_of_date lookback_periods"
            )
        params = {
            "symbols": [s.strip().upper() for s in argv[1].split(",") if s.strip()],
            "as_of_date": argv[2],
            "lookback_periods": int(argv[3]),
        }
        _run_service(method, params)
        return

    raise UnsupportedOperationError(f"Unknown service: {method}")


if __name__ == "__main__":
    try:
        main()
    except SdkError as error:
        print(f"SDK Error: {type(error).__name__}: {error}")
        sys.exit(1)
    except Exception as error:
        print(f"Error: {type(error).__name__}: {error}")
        sys.exit(2)
