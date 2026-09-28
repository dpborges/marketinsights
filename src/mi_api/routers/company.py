"""Company endpoints accepting up to ten unique comma-separated symbols.

GET /api/v1/company/profile?symbols=META,MSFT returns full company profiles.
GET /api/v1/company/summary?symbols=META returns selected company fields.
Both preserve SDK companies, errors, and summary. Item failures return HTTP 200;
invalid queries return 400; operation-wide outages/timeouts return 503/504.
"""

from typing import Annotated

from fastapi import APIRouter, Depends

from mi_api.dependencies.company import get_company_service, get_company_symbols
from mi_api.schemas.company import (
    CompanyOperationErrorResponse,
    CompanyProfileResponse,
    CompanySummaryResponse,
)
from mi_api.schemas.errors import ErrorEnvelope
from mi_sdk.services.company_service import CompanyService

router = APIRouter(
    prefix="/company",
    tags=["company"],
    responses={
        400: {"model": ErrorEnvelope, "description": "Invalid symbols query"},
        503: {"model": CompanyOperationErrorResponse, "description": "Market data unavailable"},
        504: {
            "model": CompanyOperationErrorResponse,
            "description": "Market data request timed out",
        },
    },
)


@router.get("/profile", response_model=CompanyProfileResponse, summary="Get company profiles")
async def company_profile(
    symbols: Annotated[list[str], Depends(get_company_symbols)],
    service: Annotated[CompanyService, Depends(get_company_service)],
) -> CompanyProfileResponse:
    """Return full SDK profiles, retaining all provider-supplied profile fields."""
    return CompanyProfileResponse.model_validate(await service.get_profile(symbols))


@router.get("/summary", response_model=CompanySummaryResponse, summary="Get company summaries")
async def company_summary(
    symbols: Annotated[list[str], Depends(get_company_symbols)],
    service: Annotated[CompanyService, Depends(get_company_service)],
) -> CompanySummaryResponse:
    """Return symbol, name, price, sector, and industry with batch diagnostics."""
    return CompanySummaryResponse.model_validate(await service.get_summary(symbols))
