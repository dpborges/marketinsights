"""FastAPI application construction and ASGI entry point."""

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from redis import asyncio as redis_async
from starlette.middleware.trustedhost import TrustedHostMiddleware

from mi_api.config import APISettings, Environment
from mi_api.dependencies import DatabaseManager
from mi_api.errors import register_exception_handlers
from mi_api.middleware import RequestContextMiddleware
from mi_api.observability import configure_logging, get_logger
from mi_api.routers import build_api_router, health_router


def _lifespan(settings: APISettings) -> Any:
    # Run once around the application's lifetime: create shared database and Redis
    # resources before requests are served, then close them during shutdown.
    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
        logger = get_logger(__name__)
        app.state.database = (
            DatabaseManager(settings.database_url) if settings.database_url else None
        )
        app.state.redis = (
            redis_async.Redis.from_url(settings.redis_url, decode_responses=True)
            if settings.redis_url
            else None
        )
        logger.info("application_started", environment=settings.app_env.value)
        try:
            yield
        finally:
            if app.state.redis is not None:
                await app.state.redis.close()
            if app.state.database is not None:
                app.state.database.dispose()
            logger.info("application_stopped")

    return lifespan


def create_app(settings: APISettings | None = None) -> FastAPI:
    """Construct and configure an isolated FastAPI application."""

    resolved_settings = settings or APISettings()
    configure_logging(
        resolved_settings.log_level,
        json_logs=resolved_settings.app_env is Environment.PRODUCTION,
    )
    docs_url = "/docs" if resolved_settings.enable_docs else None
    openapi_url = "/openapi.json" if resolved_settings.enable_docs else None

    application = FastAPI(
        title=resolved_settings.app_name,
        description="Market Insights HTTP API",
        version=resolved_settings.app_version,
        debug=resolved_settings.debug,
        docs_url=docs_url,
        redoc_url=None,
        openapi_url=openapi_url,
        lifespan=_lifespan(resolved_settings),
    )
    application.state.settings = resolved_settings
    application.state.database = None
    application.state.redis = None

    application.include_router(health_router)
    application.include_router(build_api_router(), prefix=resolved_settings.api_v1_prefix)
    register_exception_handlers(application)

    application.add_middleware(GZipMiddleware, minimum_size=1000)
    if resolved_settings.cors_allowed_origins:
        application.add_middleware(
            CORSMiddleware,
            allow_origins=resolved_settings.cors_allowed_origins,
            allow_credentials="*" not in resolved_settings.cors_allowed_origins,
            allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
            allow_headers=["Authorization", "Content-Type", "X-Request-ID"],
        )
    application.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=resolved_settings.trusted_hosts,
    )
    application.add_middleware(RequestContextMiddleware)
    return application


app = create_app()
