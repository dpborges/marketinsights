"""Sector-related API endpoints."""

from typing import Annotated

from fastapi import APIRouter, Depends, Query

from mi_api.dependencies import get_sector_summary_service
from mi_api.errors import InvalidQueryParameterError
from mi_api.schemas.sector import SectorSummaryResponse
from mi_sdk.services.sector_summary_service import (
    DEFAULT_SECTOR_SYMBOLS,
    SUPPORTED_PERIODS,
    SectorSummaryService,
)

router = APIRouter(prefix="/sector", tags=["sector"])

SUPPORTED_PERIOD_CODES = tuple(SUPPORTED_PERIODS)
SUPPORTED_SYMBOLS = tuple(DEFAULT_SECTOR_SYMBOLS)


def _parse_csv_parameter(
    value: str | None,
    *,
    parameter: str,
    allowed_values: tuple[str, ...],
) -> list[str] | None:
    if value is None:
        return None

    items = value.split(",")
    if any(not item.strip() for item in items):
        raise InvalidQueryParameterError(
            f"The {parameter} parameter contains an empty value.",
            parameter,
            allowed_values,
        )

    normalized = [item.strip().upper() for item in items]
    invalid = [item for item in normalized if item not in allowed_values]
    if invalid:
        noun = "period code" if parameter == "periods" else "symbol"
        raise InvalidQueryParameterError(
            f"Unsupported {noun}: {invalid[0]}",
            parameter,
            allowed_values,
        )

    return list(dict.fromkeys(normalized))


@router.get(
    "/summary",
    response_model=SectorSummaryResponse,
    response_model_by_alias=True,
    response_model_exclude_none=True,
    summary="Get a sector performance summary",
    description=(
        "Return SPDR sector ETF performance relative to SPY. Filters are optional, "
        "case-insensitive, comma-separated lists. The 1D period means one trading "
        "session. When omitted, periods defaults to 2W and symbols defaults to all "
        "supported sector ETFs."
    ),
)
def sector_summary(
    service: Annotated[SectorSummaryService, Depends(get_sector_summary_service)],
    periods: Annotated[
        str | None,
        Query(
            description=(
                "Comma-separated period codes: 1D, 2W, 1M, 3M, 6M, YTD, 1Y, 3Y, 5Y. "
                "1D represents one trading session."
            ),
            examples=["2W,1M,3M"],
        ),
    ] = None,
    symbols: Annotated[
        str | None,
        Query(
            description=(
                "Comma-separated SPDR ETF symbols: XLB, XLC, XLE, XLF, XLI, XLK, "
                "XLP, XLRE, XLU, XLV, XLY."
            ),
            examples=["XLF,XLK,XLV"],
        ),
    ] = None,
) -> SectorSummaryResponse:
    """Validate filters and delegate sector-summary construction to the SDK."""

    period_codes = _parse_csv_parameter(
        periods,
        parameter="periods",
        allowed_values=SUPPORTED_PERIOD_CODES,
    )
    sector_symbols = _parse_csv_parameter(
        symbols,
        parameter="symbols",
        allowed_values=SUPPORTED_SYMBOLS,
    )
    result = service.build_sector_summary(
        symbols=sector_symbols,
        period_codes=period_codes,
    )
    return SectorSummaryResponse.model_validate(result)
