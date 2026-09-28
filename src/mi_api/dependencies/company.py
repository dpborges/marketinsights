"""Company query validation and configured SDK dependency."""

from typing import Annotated

from fastapi import Depends, Query

from mi_api.errors import APIError
from mi_sdk.config.settings import SDKSettings
from mi_sdk.factory import ServiceFactory
from mi_sdk.services.company_service import CompanyService


def get_company_symbols(
    symbols: Annotated[
        str | None,
        Query(
            description="One to ten comma-separated stock symbols.", examples=["NVDA", "AAPL,META"]
        ),
    ] = None,
) -> list[str]:
    """Validate before constructing the provider, including when no key is configured."""
    if symbols is None or not symbols.strip():
        raise APIError("INVALID_QUERY_PARAMETER", "No symbols provided", 400, parameter="symbols")
    items = [symbol.strip().upper() for symbol in symbols.split(",")]
    items = list(dict.fromkeys(items))
    if len(items) > 10:
        raise APIError(
            "INVALID_QUERY_PARAMETER", "10 symbol request limit exceeded", 400, parameter="symbols"
        )
    if any(not item or any(char.isspace() for char in item) for item in items):
        raise APIError(
            "INVALID_QUERY_PARAMETER",
            "Each symbol must be a non-empty single stock symbol",
            400,
            parameter="symbols",
        )
    return items


def get_company_service(
    symbols: Annotated[list[str], Depends(get_company_symbols)],
) -> CompanyService:
    """Construct the service only after symbol validation succeeds."""
    return ServiceFactory(SDKSettings()).create_company_service()
