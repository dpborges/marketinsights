"""Interactive and argument-driven runner; see fmp_analyst.py for Git Bash commands."""

import asyncio
import json
import sys
from collections.abc import Sequence

from ...domain.exceptions import DataValidationError, SdkError, UnsupportedOperationError
from .fmp_analyst import FMPAnalystAdapter

METHODS = {
    "get_analyst_consensus": "Analyst recommendation counts",
    "get_analyst_targets": "High, low, median, and consensus price targets",
}


async def _run(method: str, symbol: str) -> None:
    adapter = FMPAnalystAdapter()
    if method == "get_analyst_consensus":
        result = await adapter.get_analyst_consensus(symbol)
    else:
        result = await adapter.get_analyst_targets(symbol)
    print(json.dumps(result, indent=2, allow_nan=False))


def main(argv: Sequence[str] | None = None) -> int:
    """Print responses/errors to stdout; return zero on success, nonzero on failure."""
    args = list(sys.argv[1:] if argv is None else argv)
    try:
        if not args:
            print("Available methods (required parameter: one stock symbol):")
            for method, description in METHODS.items():
                print(f"  {method}: {description}")
            args = [input("Method: ").strip()]
        if args[0] not in METHODS:
            raise UnsupportedOperationError(f"Unknown method. Choose: {', '.join(METHODS)}")
        if len(args) == 1:
            args.append(input("Symbol (e.g. NVDA): ").strip())
        if len(args) != 2:
            raise DataValidationError("Expected METHOD SYMBOL, e.g. get_analyst_targets NVDA")
        asyncio.run(_run(args[0], args[1]))
        return 0
    except SdkError as exc:
        print(f"SDK Error: {type(exc).__name__}: {exc}")
        return 1
    except (EOFError, KeyboardInterrupt):
        print("Input cancelled before the request completed.")
        return 1
    except Exception:
        print("Error: analyst request could not be completed.")
        return 2


if __name__ == "__main__":
    sys.exit(main())
