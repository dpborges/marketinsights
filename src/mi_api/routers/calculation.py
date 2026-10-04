"""Calculation API for up to ten unique comma-separated stock symbols.

GET /api/v1/calculation/stop-loss?symbols=META&horizons=SHORT,MEDIUM
returns the SDK's companies, errors, and summary unchanged. Horizons are
case-insensitive and default to SHORT when omitted. Empty symbol entries are
ignored. Invalid queries return 400; item failures return 200; operation-wide
outages/timeouts use the central SDK exception handler (503/504).
"""

from typing import Annotated

from fastapi import APIRouter, Depends

from mi_api.dependencies.calculation import (
    get_calculation_horizons,
    get_calculation_service,
    get_calculation_symbols,
)
from mi_api.schemas.calculation import StopLossResponse
from mi_api.schemas.company import CompanyOperationErrorResponse
from mi_api.schemas.errors import ErrorEnvelope
from mi_sdk.services.calculation_service import CalculationService

router = APIRouter(
    prefix="/calculation",
    tags=["calculation"],
    responses={
        400: {"model": ErrorEnvelope, "description": "Invalid symbols or horizons query"},
        503: {"model": CompanyOperationErrorResponse, "description": "Market data unavailable"},
        504: {
            "model": CompanyOperationErrorResponse,
            "description": "Market data request timed out",
        },
    },
)


@router.get("/stop-loss", response_model=StopLossResponse, summary="Calculate stop-loss prices")
async def stop_loss(
    symbols: Annotated[list[str], Depends(get_calculation_symbols)],
    horizons: Annotated[list[str], Depends(get_calculation_horizons)],
    service: Annotated[CalculationService, Depends(get_calculation_service)],
) -> StopLossResponse:
    """Return stop-loss calculations for each requested symbol and investment horizon."""
    return StopLossResponse.model_validate(await service.get_stop_loss(symbols, horizons))
