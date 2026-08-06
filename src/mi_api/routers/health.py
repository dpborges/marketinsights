"""Process liveness and dependency readiness routes."""

from typing import Annotated, Any

import anyio
from fastapi import APIRouter, Depends, Request, status
from fastapi.responses import JSONResponse

from mi_api.config import APISettings
from mi_api.dependencies import DatabaseManager, get_settings
from mi_api.observability import get_logger
from mi_api.schemas.health import HealthResponse, ReadinessResponse

router = APIRouter(prefix="/health", tags=["health"])
logger = get_logger(__name__)


@router.get(
    "/live",
    response_model=HealthResponse,
    summary="Check process liveness",
)
async def liveness(
    settings: Annotated[APISettings, Depends(get_settings)],
) -> HealthResponse:
    """Return immediately when the application process is alive."""

    return HealthResponse(service=settings.app_name, version=settings.app_version)


@router.get(
    "/ready",
    response_model=ReadinessResponse,
    responses={status.HTTP_503_SERVICE_UNAVAILABLE: {"model": ReadinessResponse}},
    summary="Check required dependencies",
)
async def readiness(
    request: Request,
    settings: Annotated[APISettings, Depends(get_settings)],
) -> ReadinessResponse | JSONResponse:
    """Check configured PostgreSQL and required Redis connectivity."""

    checks: dict[str, Any] = {}
    ready = True

    database: DatabaseManager | None = request.app.state.database
    if database is None:
        checks["postgresql"] = "not_configured"
    else:
        try:
            await anyio.to_thread.run_sync(database.is_ready)
            checks["postgresql"] = "ok"
        except Exception as exc:
            logger.warning("readiness_check_failed", dependency="postgresql", exc_info=exc)
            checks["postgresql"] = "unavailable"
            ready = False

    redis_client: Any = request.app.state.redis
    if not settings.redis_required:
        checks["redis"] = "not_configured"
    elif redis_client is None:
        checks["redis"] = "unavailable"
        ready = False
    else:
        try:
            await redis_client.ping()
            checks["redis"] = "ok"
        except Exception as exc:
            logger.warning("readiness_check_failed", dependency="redis", exc_info=exc)
            checks["redis"] = "unavailable"
            ready = False

    response = ReadinessResponse(
        status="ok" if ready else "unavailable",
        service=settings.app_name,
        version=settings.app_version,
        checks=checks,
    )
    if ready:
        return response
    return JSONResponse(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        content=response.model_dump(),
    )
