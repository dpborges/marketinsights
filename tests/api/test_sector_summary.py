"""API contract tests for the sector summary endpoint."""

from collections.abc import AsyncIterator, Sequence
from typing import Any

import httpx
import pytest
from fastapi import FastAPI

from mi_api.config import APISettings, Environment
from mi_api.dependencies import get_sector_summary_service
from mi_api.main import create_app


class StubSectorSummaryService:
    """Record SDK calls while returning a valid provider-independent payload."""

    def __init__(self) -> None:
        self.calls: list[dict[str, Sequence[str] | None]] = []

    def build_sector_summary(
        self,
        symbols: Sequence[str] | None = None,
        period_codes: Sequence[str] | None = None,
    ) -> dict[str, Any]:
        self.calls.append({"symbols": symbols, "period_codes": period_codes})
        return {
            "provider": "test-provider",
            "status": "SUCCESS",
            "asOfDate": "2026-08-06",
            "benchmark": {"symbol": "SPY"},
            "requestedSectorCount": len(symbols or []),
            "successfulSectorCount": len(symbols or []),
            "failedSectorCount": 0,
            "sectors": [],
            "errors": [],
        }


@pytest.fixture
def sector_service() -> StubSectorSummaryService:
    return StubSectorSummaryService()


@pytest.fixture
def application(sector_service: StubSectorSummaryService) -> FastAPI:
    app = create_app(APISettings(app_env=Environment.TEST))
    app.dependency_overrides[get_sector_summary_service] = lambda: sector_service
    return app


@pytest.fixture
async def client(application: FastAPI) -> AsyncIterator[httpx.AsyncClient]:
    transport = httpx.ASGITransport(app=application, raise_app_exceptions=False)
    async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as api_client:
        yield api_client


@pytest.mark.asyncio
async def test_summary_uses_sdk_defaults_when_filters_are_omitted(
    client: httpx.AsyncClient,
    sector_service: StubSectorSummaryService,
) -> None:
    response = await client.get("/api/v1/sector/summary")

    assert response.status_code == 200
    assert sector_service.calls == [{"symbols": None, "period_codes": None}]
    assert response.json()["status"] == "SUCCESS"


@pytest.mark.asyncio
async def test_summary_passes_one_period_and_symbol_to_sdk(
    client: httpx.AsyncClient,
    sector_service: StubSectorSummaryService,
) -> None:
    response = await client.get(
        "/api/v1/sector/summary",
        params={"periods": "1D", "symbols": "XLK"},
    )

    assert response.status_code == 200
    assert sector_service.calls == [{"symbols": ["XLK"], "period_codes": ["1D"]}]


@pytest.mark.asyncio
async def test_summary_parses_normalizes_and_deduplicates_csv_filters(
    client: httpx.AsyncClient,
    sector_service: StubSectorSummaryService,
) -> None:
    response = await client.get(
        "/api/v1/sector/summary",
        params={"periods": "2w, 1m,2W,3m", "symbols": "xlf, XLK,xlf,xlv"},
    )

    assert response.status_code == 200
    assert sector_service.calls == [
        {
            "symbols": ["XLF", "XLK", "XLV"],
            "period_codes": ["2W", "1M", "3M"],
        }
    ]


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("parameter", "value", "invalid_value"),
    [
        ("periods", "2W,4M", "4M"),
        ("symbols", "XLK,SPY", "SPY"),
    ],
)
async def test_summary_rejects_unsupported_filter_values(
    client: httpx.AsyncClient,
    sector_service: StubSectorSummaryService,
    parameter: str,
    value: str,
    invalid_value: str,
) -> None:
    response = await client.get("/api/v1/sector/summary", params={parameter: value})

    assert response.status_code == 422
    error = response.json()["error"]
    assert error["code"] == "INVALID_QUERY_PARAMETER"
    assert invalid_value in error["message"]
    assert error["parameter"] == parameter
    assert error["allowedValues"]
    assert error["requestId"] == response.headers["X-Request-ID"]
    assert sector_service.calls == []


@pytest.mark.asyncio
@pytest.mark.parametrize(("parameter", "value"), [("periods", "2W,"), ("symbols", "")])
async def test_summary_rejects_empty_csv_items(
    client: httpx.AsyncClient,
    sector_service: StubSectorSummaryService,
    parameter: str,
    value: str,
) -> None:
    response = await client.get("/api/v1/sector/summary", params={parameter: value})

    assert response.status_code == 422
    assert response.json()["error"]["parameter"] == parameter
    assert sector_service.calls == []


def test_openapi_documents_csv_query_parameters(application: FastAPI) -> None:
    operation = application.openapi()["paths"]["/api/v1/sector/summary"]["get"]
    parameters = {parameter["name"]: parameter for parameter in operation["parameters"]}

    assert "Comma-separated" in parameters["periods"]["description"]
    assert "one trading session" in parameters["periods"]["description"]
    assert "Comma-separated" in parameters["symbols"]["description"]
