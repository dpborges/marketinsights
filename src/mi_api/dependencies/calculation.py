"""Calculation query validation and configured SDK dependency."""

from typing import Annotated

from fastapi import Depends, Query

from mi_api.errors import APIError
from mi_sdk.config.settings import SDKSettings
from mi_sdk.domain.models.stop_loss import InvestmentHorizon
from mi_sdk.factory import ServiceFactory
from mi_sdk.services.calculation_service import CalculationService


def get_calculation_symbols(
    symbols: Annotated[
        str | None,
        Query(
            description="One to ten unique comma-separated stock symbols; empty entries ignored."
        ),
    ] = None,
) -> list[str]:
    """Normalize symbols while preserving request order."""
    items = list(
        dict.fromkeys(
            value.strip().upper() for value in (symbols or "").split(",") if value.strip()
        )
    )
    if not items:
        raise APIError("INVALID_QUERY_PARAMETER", "No symbols provided", 400, parameter="symbols")
    if len(items) > 10:
        raise APIError(
            "INVALID_QUERY_PARAMETER", "10 symbol request limit exceeded", 400, parameter="symbols"
        )
    if any(any(char.isspace() for char in item) for item in items):
        raise APIError(
            "INVALID_QUERY_PARAMETER",
            "Each symbol must be a single stock symbol",
            400,
            parameter="symbols",
        )
    return items


def get_calculation_horizons(
    horizons: Annotated[
        str | None,
        Query(
            description="Comma-separated SHORT, MEDIUM, LONG (case-insensitive); defaults to SHORT."
        ),
    ] = None,
) -> list[str]:
    """Distinguish omitted horizons from explicitly empty lists."""
    if horizons is None:
        return ["SHORT"]
    items = [value.strip().upper() for value in horizons.split(",")]
    if not any(items):
        raise APIError("INVALID_QUERY_PARAMETER", "No horizons provided", 400, parameter="horizons")
    allowed = [h.value for h in InvestmentHorizon]
    if any(value not in allowed for value in items):
        raise APIError(
            "INVALID_QUERY_PARAMETER",
            "Invalid horizon value provided",
            400,
            parameter="horizons",
            allowed_values=allowed,
        )
    return list(dict.fromkeys(items))


def get_calculation_service(
    symbols: Annotated[list[str], Depends(get_calculation_symbols)],
    horizons: Annotated[list[str], Depends(get_calculation_horizons)],
) -> CalculationService:
    """Construct the service only after both query parameters validate."""
    return ServiceFactory(SDKSettings()).create_calculation_service()
