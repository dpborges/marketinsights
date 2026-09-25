"""Shared SDK batch validation, error translation, and result aggregation."""

import asyncio
from collections.abc import Awaitable, Callable
from typing import Any

from ..providers.common.exceptions import ProviderError
from .exceptions import MarketDataError


def normalize_symbols(symbols: str | list[str] | None, maximum: int = 10) -> list[str]:
    """Validate all input before I/O; preserve the order of unique normalized symbols."""
    requested = [symbols] if isinstance(symbols, str) else symbols
    if not isinstance(requested, list) or not requested:
        raise MarketDataError(
            "Provide a stock symbol or a non-empty list of symbols.",
            error_code="BAD_REQUEST",
            retryable=False,
        )
    normalized: list[str] = []
    for symbol in requested:
        if (
            not isinstance(symbol, str)
            or not symbol.strip()
            or "," in symbol
            or any(char.isspace() for char in symbol.strip())
        ):
            raise MarketDataError(
                "Each symbol must be a non-empty single stock symbol.",
                error_code="BAD_REQUEST",
                retryable=False,
            )
        value = symbol.strip().upper()
        if value not in normalized:
            normalized.append(value)
    if len(normalized) > maximum:
        raise MarketDataError(
            f"exceeded maximum of {maximum} symbols per request",
            error_code="BAD_REQUEST",
            retryable=False,
        )
    return normalized


def translate_provider_error(error: ProviderError) -> MarketDataError:
    """Retain diagnostic metadata while translating across the SDK boundary."""
    return MarketDataError(
        message=error.message,
        error_code=error.error_code,
        provider=error.provider,
        provider_status_code=error.status_code,
        retryable=error.retryable,
    )


def item_error(symbol: str, error: MarketDataError) -> dict[str, Any]:
    """Serialize an expected item failure without provider diagnostic fields."""
    return {
        "symbol": symbol,
        "code": error.error_code,
        "message": error.message,
        "retryable": error.retryable,
    }


async def collect_batch(
    symbols: str | list[str] | None,
    fetch: Callable[[str], Awaitable[dict[str, Any]]],
    result_key: str,
) -> dict[str, Any]:
    """Fetch up to ten unique symbols concurrently and retain input order.

    All timeouts raise an SDK timeout. All unavailable/timeout failures raise
    SDK unavailability. Other expected failures remain item errors, including
    when none succeed. Unexpected exceptions propagate after all calls finish.
    The caller supplies one domain record per symbol and its result property.
    """
    requested = normalize_symbols(symbols)

    async def retrieve(symbol: str) -> dict[str, Any] | MarketDataError:
        try:
            return await fetch(symbol)
        except ProviderError as exc:
            return translate_provider_error(exc)
        except MarketDataError as exc:
            return exc

    outcomes = await asyncio.gather(
        *(retrieve(symbol) for symbol in requested),
        return_exceptions=True,
    )
    for outcome in outcomes:
        if isinstance(outcome, BaseException) and not isinstance(outcome, MarketDataError):
            raise outcome
    failures = [outcome for outcome in outcomes if isinstance(outcome, MarketDataError)]
    if len(failures) == len(requested):
        codes = {error.error_code for error in failures}
        if codes <= {"PROVIDER_TIMEOUT", "PROVIDER_UNAVAILABLE"}:
            code = "PROVIDER_TIMEOUT" if codes == {"PROVIDER_TIMEOUT"} else "PROVIDER_UNAVAILABLE"
            cause = next(error for error in failures if error.error_code == code)
            raise MarketDataError(
                message=(
                    "Market data provider timed out for the entire operation."
                    if code == "PROVIDER_TIMEOUT"
                    else "Market data provider is unavailable."
                ),
                error_code=code,
                provider=cause.provider,
                provider_status_code=cause.provider_status_code,
                retryable=True,
            ) from cause
    records = [outcome for outcome in outcomes if isinstance(outcome, dict)]
    errors = [
        item_error(symbol, outcome)
        for symbol, outcome in zip(requested, outcomes, strict=True)
        if isinstance(outcome, MarketDataError)
    ]
    return {
        result_key: records,
        "errors": errors,
        "summary": {
            "requested": len(requested),
            "successful": len(records),
            "failed": len(errors),
        },
    }
