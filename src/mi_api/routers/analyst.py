"""Analyst API endpoints accepting one to ten comma-separated symbols.

GET /api/v1/analyst/consensus?symbols=NVDA returns ratings and recommendations.
GET /api/v1/analyst/targets?symbols=AAPL,META returns flat price-target records.
Per-symbol SDK errors remain in the response's errors list with HTTP 200.
Missing symbols and requests exceeding ten symbols return HTTP 400.
"""

from typing import Annotated

from fastapi import APIRouter, Depends

from mi_api.dependencies.analyst import get_analyst_service, get_analyst_symbols
from mi_api.schemas.analyst import AnalystConsensusResponse, AnalystTargetsResponse
from mi_api.schemas.errors import ErrorEnvelope
from mi_sdk.services.analyst_service import AnalystService

router = APIRouter(
    prefix="/analyst",
    tags=["analyst"],
    responses={
        400: {"model": ErrorEnvelope, "description": "Invalid symbols query"},
        503: {"model": ErrorEnvelope, "description": "Required service unavailable"},
    },
)


@router.get("/consensus", response_model=AnalystConsensusResponse, summary="Get analyst consensus")
async def analyst_consensus(
    symbols: Annotated[list[str], Depends(get_analyst_symbols)],
    service: Annotated[AnalystService, Depends(get_analyst_service)],
) -> AnalystConsensusResponse:
    """Return analyst counts and overall recommendations, retaining per-symbol errors."""
    return AnalystConsensusResponse.model_validate(await service.get_consensus(symbols))


@router.get("/targets", response_model=AnalystTargetsResponse, summary="Get analyst price targets")
async def analyst_targets(
    symbols: Annotated[list[str], Depends(get_analyst_symbols)],
    service: Annotated[AnalystService, Depends(get_analyst_service)],
) -> AnalystTargetsResponse:
    """Return high, low, median, and consensus targets, retaining per-symbol errors."""
    return AnalystTargetsResponse.model_validate(await service.get_targets(symbols))
