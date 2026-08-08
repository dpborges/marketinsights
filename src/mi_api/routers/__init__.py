"""API router composition."""

from fastapi import APIRouter

from .health import router as health_router
from .sector import router as sector_router
from .system import router as system_router


def build_api_router() -> APIRouter:
    """Compose versioned routers."""

    router = APIRouter()
    router.include_router(sector_router)
    router.include_router(system_router)
    return router


__all__ = ["build_api_router", "health_router"]
