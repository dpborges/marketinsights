"""Interactive company profile and historical pricing validation."""
# Run from the repository root in PowerShell:
# $env:PYTHONPATH = 'src'; ./.venv/Scripts/python.exe -m mi_sdk.providers.fmp.fmp_company_run
# Append get_profile AAPL for a non-interactive request.
# Or append get_historical_pricing NVDA 2026-03-01 2026-09-28.
# Run from the repository root using gitbash:
# PYTHONPATH=src ./.venv/Scripts/python.exe -m mi_sdk.providers.fmp.fmp_company_run

import asyncio
import json
import sys
from collections.abc import Sequence

from ..common.exceptions import ProviderError
from .fmp_company import FMPCompanyAdapter

METHODS = {
    "get_profile": "Full company profile; parameters: SYMBOL (e.g. AAPL)",
    "get_historical_pricing": (
        "Daily historical pricing; parameters: SYMBOL FROM_DATE TO_DATE "
        "(e.g. NVDA 2026-03-01 2026-09-28)"
    ),
}


async def _run(method: str, parameters: list[str]) -> None:
    adapter = FMPCompanyAdapter()
    if method == "get_profile":
        result = await adapter.get_profile(parameters[0])
    else:
        result = await adapter.get_historical_pricing(*parameters)
    print(json.dumps({"data": result, "error": {}}, indent=2))


def main(argv: Sequence[str] | None = None) -> int:
    """Print responses or errors to stdout and return a process exit code."""
    args = list(sys.argv[1:] if argv is None else argv)
    try:
        if not args:
            print("Available methods:")
            for method, description in METHODS.items():
                print(f"  {method}: {description}")
            args = [input("Method: ").strip()]
        if args[0] not in METHODS:
            raise ProviderError(
                f"Unknown method. Choose: {', '.join(METHODS)}",
                provider="FMP",
                error_code="BAD_REQUEST",
            )
        if len(args) == 1:
            args.append(input("Symbol (e.g. AAPL): ").strip())
            if args[0] == "get_historical_pricing":
                args.append(input("from_date (YYYY-MM-DD, e.g. 2026-03-01): ").strip())
                args.append(input("to_date (YYYY-MM-DD, e.g. 2026-09-28): ").strip())
        expected = 2 if args[0] == "get_profile" else 4
        if len(args) != expected:
            raise ProviderError(
                f"Expected parameters for {args[0]}: {METHODS[args[0]]}",
                provider="FMP",
                error_code="BAD_REQUEST",
            )
        asyncio.run(_run(args[0], args[1:]))
        return 0
    except ProviderError as exc:
        print(
            json.dumps(
                {
                    "data": None,
                    "error": {
                        "message": exc.message,
                        "provider": exc.provider,
                        "error_code": exc.error_code,
                        "status_code": exc.status_code,
                        "retryable": exc.retryable,
                    },
                },
                indent=2,
            )
        )
        return 1
    except (EOFError, KeyboardInterrupt):
        print("Input cancelled before the request completed.")
        return 1
    except Exception:
        print("Error: company request could not be completed.")
        return 2


if __name__ == "__main__":
    sys.exit(main())
