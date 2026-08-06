"""Tests for FastAPI construction, middleware, and core endpoints."""

from collections.abc import AsyncIterator

import httpx
import pytest
from fastapi import FastAPI, Query
from pydantic import SecretStr, ValidationError

from mi_api.config import APISettings, Environment
from mi_api.main import create_app


@pytest.fixture
def settings() -> APISettings:
    return APISettings(
        app_env=Environment.TEST,
        enable_docs=True,
        cors_allowed_origins=["https://client.example"],
    )


@pytest.fixture
def application(settings: APISettings) -> FastAPI:
    return create_app(settings)


@pytest.fixture
async def client(application: FastAPI) -> AsyncIterator[httpx.AsyncClient]:
    transport = httpx.ASGITransport(app=application, raise_app_exceptions=False)
    async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as test_client:
        yield test_client


def test_application_construction(application: FastAPI, settings: APISettings) -> None:
    assert application.title == settings.app_name
    assert application.version == settings.app_version
    assert application.docs_url == "/docs"
    assert application.openapi_url == "/openapi.json"


@pytest.mark.asyncio
async def test_liveness(client: httpx.AsyncClient) -> None:
    response = await client.get("/health/live")

    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
        "service": "market-insights-api",
        "version": "1.0.0",
    }


@pytest.mark.asyncio
async def test_readiness_without_required_dependencies(client: httpx.AsyncClient) -> None:
    response = await client.get("/health/ready")

    assert response.status_code == 200
    assert response.json()["status"] == "ok"
    assert response.json()["checks"] == {
        "postgresql": "not_configured",
        "redis": "not_configured",
    }


@pytest.mark.asyncio
async def test_readiness_reports_configured_dependency_failure(
    application: FastAPI, client: httpx.AsyncClient
) -> None:
    class UnavailableDatabase:
        def is_ready(self) -> bool:
            raise OSError("private database failure")

    application.state.database = UnavailableDatabase()
    response = await client.get("/health/ready")

    assert response.status_code == 503
    assert response.json()["status"] == "unavailable"
    assert response.json()["checks"]["postgresql"] == "unavailable"
    assert "private database failure" not in response.text


@pytest.mark.asyncio
async def test_system_information(client: httpx.AsyncClient) -> None:
    response = await client.get("/api/v1/system/info")

    assert response.status_code == 200
    assert response.json() == {
        "name": "market-insights-api",
        "version": "1.0.0",
        "environment": "test",
    }


@pytest.mark.asyncio
async def test_request_id_is_propagated(client: httpx.AsyncClient) -> None:
    response = await client.get("/health/live", headers={"X-Request-ID": "test-request-123"})

    assert response.headers["X-Request-ID"] == "test-request-123"


@pytest.mark.asyncio
async def test_validation_error_is_consistent(
    application: FastAPI, client: httpx.AsyncClient
) -> None:
    async def validated_endpoint(limit: int = Query(ge=1)) -> dict[str, int]:
        return {"limit": limit}

    application.add_api_route("/_test/validation", validated_endpoint, methods=["GET"])
    response = await client.get("/_test/validation", params={"limit": 0})

    assert response.status_code == 422
    body = response.json()["error"]
    assert body["code"] == "VALIDATION_ERROR"
    assert body["message"] == "The request could not be validated."
    assert body["requestId"] == response.headers["X-Request-ID"]
    assert body["details"]


@pytest.mark.asyncio
async def test_unexpected_error_is_sanitized(
    application: FastAPI, client: httpx.AsyncClient
) -> None:
    async def broken_endpoint() -> None:
        raise RuntimeError("sensitive internal detail")

    application.add_api_route("/_test/error", broken_endpoint, methods=["GET"])
    response = await client.get("/_test/error")

    assert response.status_code == 500
    assert response.json()["error"]["code"] == "INTERNAL_SERVER_ERROR"
    assert "sensitive" not in response.text


@pytest.mark.asyncio
async def test_not_found_error_is_consistent(client: httpx.AsyncClient) -> None:
    response = await client.get("/does-not-exist")

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "RESOURCE_NOT_FOUND"
    assert response.json()["error"]["requestId"] == response.headers["X-Request-ID"]


def test_production_disables_documentation() -> None:
    production_settings = APISettings(
        app_env=Environment.PRODUCTION,
        enable_docs=False,
        database_url="postgresql+psycopg://user:password@db.example/marketinsights",
        secret_key=SecretStr("a-secure-production-secret-with-32-characters"),
        trusted_hosts=["api.example.com"],
        cors_allowed_origins=["https://app.example.com"],
    )

    application = create_app(production_settings)

    assert application.docs_url is None
    assert application.openapi_url is None


def test_production_rejects_insecure_settings() -> None:
    with pytest.raises(ValidationError):
        APISettings(
            app_env=Environment.PRODUCTION,
            enable_docs=False,
            database_url="postgresql+psycopg://user:password@db.example/marketinsights",
            secret_key=SecretStr("short"),
            trusted_hosts=["*"],
            cors_allowed_origins=["*"],
        )


@pytest.mark.asyncio
async def test_cors_and_trusted_hosts(application: FastAPI) -> None:
    transport = httpx.ASGITransport(app=application, raise_app_exceptions=False)
    async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as test_client:
        preflight = await test_client.options(
            "/health/live",
            headers={
                "Origin": "https://client.example",
                "Access-Control-Request-Method": "GET",
            },
        )
        invalid_host = await test_client.get(
            "/health/live",
            headers={"Host": "untrusted.example"},
        )

    assert preflight.status_code == 200
    assert preflight.headers["access-control-allow-origin"] == "https://client.example"
    assert invalid_host.status_code == 400
