"""Interactive company profile validation; optionally pass get_profile AAPL."""
# Run from the repository root in PowerShell:
# $env:PYTHONPATH = 'src'; ./.venv/Scripts/python.exe -m mi_sdk.providers.fmp.fmp_company_run
# Append get_profile AAPL for a non-interactive request.
# Run from the repository root using gitbash:
# PYTHONPATH=src python -m mi_sdk.providers.fmp.fmp_company_run

import asyncio
import json
import sys
from collections.abc import Sequence

from ..common.exceptions import ProviderError
from .fmp_company import FMPCompanyAdapter

METHODS = {"get_profile": "Full company profile (raw provider JSON)"}


async def _run(symbol: str) -> None:
    result = await FMPCompanyAdapter().get_profile(symbol)
    print(json.dumps({"data": result, "error": {}}, indent=2))


def main(argv: Sequence[str] | None = None) -> int:
    """Print responses or errors to stdout and return a process exit code."""
    args = list(sys.argv[1:] if argv is None else argv)
    try:
        if not args:
            print("Available methods (required parameter: one stock symbol):")
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
        if len(args) != 2:
            raise ProviderError(
                "Expected METHOD SYMBOL, e.g. get_profile AAPL",
                provider="FMP",
                error_code="BAD_REQUEST",
            )
        asyncio.run(_run(args[1]))
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
