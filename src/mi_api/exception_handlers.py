from fastapi import Request
from fastapi.responses import JSONResponse

from mi_sdk.services.exceptions import MarketDataError


def map_error_to_http_status(error_code: str) -> int:
    return {
        # MI/client errors
        "BAD_REQUEST": 400,
        "INVALID_QUERY_PARAMETER": 400,
        "INVALID_API_KEY": 401,
        "FORBIDDEN_PLAN_LIMIT": 403,
        "SYMBOL_NOT_FOUND": 404,
        "RATE_LIMIT_EXCEEDED": 503,
        # Provider errors
        "PROVIDER_UNAUTHORIZED": 502,
        "PROVIDER_TIMEOUT": 504,
        "PROVIDER_UNAVAILABLE": 503,
        "PROVIDER_ERROR": 502,
    }.get(error_code, 500)


async def market_data_error_handler(
    request: Request,
    exc: MarketDataError,
):
    status_code = map_error_to_http_status(exc.error_code)
    # The default REST policy overrides upstream retry hints for these failures.
    non_retryable = {
        "BAD_REQUEST",
        "INVALID_QUERY_PARAMETER",
        "INVALID_API_KEY",
        "PROVIDER_UNAVAILABLE",
        "PROVIDER_TIMEOUT",
    }

    return JSONResponse(
        status_code=status_code,
        content={
            "error": {
                "code": exc.error_code,
                "message": exc.message,
                "retryable": False if exc.error_code in non_retryable else exc.retryable,
            }
        },
    )
