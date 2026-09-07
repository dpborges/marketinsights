"""Sector API services.

sector_summary: GET /api/v1/sector/summary for sector performance versus SPY.
sector_leadership: GET /api/v1/sector/leadership for the top 3 or 5 leaders,
using 1M as anchor, 2W as momentum, and 3M as confirmation.
"""

from typing import Annotated

from fastapi import APIRouter, Depends, Query

from mi_api.dependencies import get_sector_leadership_service, get_sector_summary_service
from mi_api.errors import InvalidQueryParameterError, SectorLeadershipSdkError
from mi_api.schemas.errors import ErrorEnvelope
from mi_api.schemas.sector import SectorLeadershipResponse, SectorSummaryResponse
from mi_sdk.domain.exceptions import SdkError
from mi_sdk.services.sector_leadership_service import LEADERSHIP_PERIODS, SectorLeadershipService
from mi_sdk.services.sector_summary_service import (
    DEFAULT_SECTOR_SYMBOLS,
    SUPPORTED_PERIODS,
    SUPPORTED_SORT_DIRECTIONS,
    SUPPORTED_SORT_FIELDS,
    SectorSummaryService,
)

router = APIRouter(prefix="/sector", tags=["sector"])

SUPPORTED_PERIOD_CODES = tuple(SUPPORTED_PERIODS)
SUPPORTED_SYMBOLS = tuple(DEFAULT_SECTOR_SYMBOLS)


def _parse_sort_parameter(value: str, *, parameter: str, allowed_values: tuple[str, ...]) -> str:
    normalized = value.strip().lower()
    if normalized not in allowed_values:
        raise InvalidQueryParameterError(
            f"Unsupported {parameter}: {value}", parameter, allowed_values
        )
    return normalized


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
        "supported sector ETFs. Sorting defaults to relative strength descending. "
        "For multiple periods, sectors are sorted using the first requested period."
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
    sort_by: Annotated[
        str,
        Query(
            description=(
                "Sort sectors by performance (returnPct) or relative_strength "
                "(excessReturnPct). Case-insensitive; uses the first requested period."
            ),
            json_schema_extra={"enum": list(SUPPORTED_SORT_FIELDS)},
        ),
    ] = "relative_strength",
    sort_direction: Annotated[
        str,
        Query(
            description="Sort direction: asc or desc (case-insensitive).",
            json_schema_extra={"enum": list(SUPPORTED_SORT_DIRECTIONS)},
        ),
    ] = "desc",
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
        sort_by=_parse_sort_parameter(
            sort_by, parameter="sort_by", allowed_values=SUPPORTED_SORT_FIELDS
        ),
        sort_direction=_parse_sort_parameter(
            sort_direction,
            parameter="sort_direction",
            allowed_values=SUPPORTED_SORT_DIRECTIONS,
        ),
    )
    return SectorSummaryResponse.model_validate(result)


@router.get(
    "/leadership",
    response_model=SectorLeadershipResponse,
    response_model_by_alias=True,
    summary="Get sector leadership",
    description=(
        "Return the top 3 or 5 sectors ranked by 1M relative strength against SPY. "
        "Leadership requires exactly 2W, 1M, and 3M; omitted periods use these defaults. "
        "Partial SDK errors remain in errors. Fatal SDK errors use the same response "
        "shape with an empty sectors list and a non-success HTTP status."
    ),
    responses={
        **{
            code: {"model": SectorLeadershipResponse, "description": "SDK workflow failed"}
            for code in (401, 403, 404, 503)
        },
        422: {
            "model": ErrorEnvelope | SectorLeadershipResponse,
            "description": "Invalid query parameter or SDK data validation failure",
        },
    },
)
def sector_leadership(
    service: Annotated[SectorLeadershipService, Depends(get_sector_leadership_service)],
    periods: Annotated[
        str | None,
        Query(
            description="Comma-separated leadership periods: exactly 2W, 1M, 3M.",
            examples=["2W,1M,3M"],
        ),
    ] = None,
    top_n: Annotated[
        str,
        Query(
            description="Number of sector leaders: 3 or 5; defaults to 5.",
            json_schema_extra={"enum": ["3", "5"]},
        ),
    ] = "5",
) -> SectorLeadershipResponse:
    """Validate leadership filters and delegate ranking to the SDK."""
    if top_n not in {"3", "5"}:
        raise InvalidQueryParameterError(
            "Invald top_n value. Only 3 and 5 are supported", "top_n", ("3", "5")
        )
    period_codes = _parse_csv_parameter(
        periods, parameter="periods", allowed_values=LEADERSHIP_PERIODS
    )
    if period_codes is None:
        period_codes = list(LEADERSHIP_PERIODS)
    if set(period_codes) != set(LEADERSHIP_PERIODS):
        raise InvalidQueryParameterError(
            "Leadership requires exactly 2W, 1M, and 3M.", "periods", LEADERSHIP_PERIODS
        )
    try:
        result = service.build_sector_leadership(periods=period_codes, top_n=int(top_n))
    except SdkError as exc:
        raise SectorLeadershipSdkError(exc) from exc
    return SectorLeadershipResponse.model_validate(result)
