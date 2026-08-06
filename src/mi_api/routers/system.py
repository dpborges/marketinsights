"""Versioned, non-sensitive service metadata."""

from typing import Annotated

from fastapi import APIRouter, Depends

from mi_api.config import APISettings
from mi_api.dependencies import get_settings
from mi_api.schemas.system import SystemInfoResponse

router = APIRouter(prefix="/system", tags=["system"])


@router.get(
    "/info",
    response_model=SystemInfoResponse,
    summary="Get service information",
)
async def system_info(
    settings: Annotated[APISettings, Depends(get_settings)],
) -> SystemInfoResponse:
    """Return public application metadata without infrastructure details."""

    return SystemInfoResponse(
        name=settings.app_name,
        version=settings.app_version,
        environment=settings.app_env,
    )
