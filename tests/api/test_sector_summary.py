"""API contract tests for the sector summary endpoint."""

from collections.abc import AsyncIterator, Sequence
from typing import Any
from unittest.mock import Mock

import httpx
import pytest
from fastapi import FastAPI

from mi_api.config import APISettings, Environment
from mi_api.dependencies import get_sector_summary_service
from mi_api.main import create_app
from mi_sdk.services.sector_summary_service import SectorSummaryService


class StubSectorSummaryService:
    """Record SDK calls while returning a valid provider-independent payload."""

    def __init__(self) -> None:
        self.calls: list[dict[str, Sequence[str] | None]] = []

    def build_sector_summary(
        self,
        symbols: Sequence[str] | None = None,
        period_codes: Sequence[str] | None = None,
        sort_by: str = "relative_strength",
        sort_direction: str = "desc",
    ) -> dict[str, Any]:
        self.calls.append(
            {
                "symbols": symbols,
                "period_codes": period_codes,
                "sort_by": sort_by,
                "sort_direction": sort_direction,
            }
        )
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
    assert sector_service.calls == [
        {
            "symbols": None,
            "period_codes": None,
            "sort_by": "relative_strength",
            "sort_direction": "desc",
        }
    ]
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
    assert sector_service.calls == [
        {
            "symbols": ["XLK"],
            "period_codes": ["1D"],
            "sort_by": "relative_strength",
            "sort_direction": "desc",
        }
    ]


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
            "sort_by": "relative_strength",
            "sort_direction": "desc",
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


@pytest.mark.asyncio
@pytest.mark.parametrize("sort_by", ["performance", "relative_strength"])
@pytest.mark.parametrize("sort_direction", ["asc", "desc"])
async def test_summary_passes_normalized_sort_options(
    client: httpx.AsyncClient,
    sector_service: StubSectorSummaryService,
    sort_by: str,
    sort_direction: str,
) -> None:
    response = await client.get(
        "/api/v1/sector/summary",
        params={
            "periods": "2W,1M",
            "symbols": "XLK,XLF",
            "sort_by": f" {sort_by.upper()} ",
            "sort_direction": f" {sort_direction.upper()} ",
        },
    )
    assert response.status_code == 200
    assert sector_service.calls == [
        {
            "symbols": ["XLK", "XLF"],
            "period_codes": ["2W", "1M"],
            "sort_by": sort_by,
            "sort_direction": sort_direction,
        }
    ]
    assert set(response.json()) == {
        "provider",
        "status",
        "asOfDate",
        "benchmark",
        "requestedSectorCount",
        "successfulSectorCount",
        "failedSectorCount",
        "sectors",
        "errors",
    }


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("parameter", "value", "allowed"),
    [
        ("sort_by", value, ["performance", "relative_strength"])
        for value in ["", " ", "return", "performance,relative_strength"]
    ]
    + [("sort_direction", value, ["asc", "desc"]) for value in ["", " ", "up", "asc,desc"]],
)
async def test_summary_rejects_invalid_sort_options(
    client: httpx.AsyncClient,
    sector_service: StubSectorSummaryService,
    parameter: str,
    value: str,
    allowed: list[str],
) -> None:
    response = await client.get("/api/v1/sector/summary", params={parameter: value})
    assert response.status_code == 422
    error = response.json()["error"]
    assert error["code"] == "INVALID_QUERY_PARAMETER"
    assert error["parameter"] == parameter
    assert error["allowedValues"] == allowed
    assert sector_service.calls == []


def test_openapi_documents_sort_options(application: FastAPI) -> None:
    parameters = {
        item["name"]: item["schema"]
        for item in application.openapi()["paths"]["/api/v1/sector/summary"]["get"]["parameters"]
    }
    assert set(parameters) == {"periods", "symbols", "sort_by", "sort_direction"}
    assert parameters["sort_by"]["enum"] == ["performance", "relative_strength"]
    assert parameters["sort_by"]["default"] == "relative_strength"
    assert parameters["sort_direction"]["enum"] == ["asc", "desc"]
    assert parameters["sort_direction"]["default"] == "desc"


@pytest.mark.asyncio
@pytest.mark.parametrize("periods", ["2W", "1M,2W"])
@pytest.mark.parametrize("sort_by", ["performance", "relative_strength"])
async def test_summary_sorts_sdk_results_without_changing_payload(
    client: httpx.AsyncClient,
    application: FastAPI,
    periods: str,
    sort_by: str,
) -> None:
    adapter = Mock()
    adapter.get_historical_prices.return_value = {
        "prices": [
            {
                "symbol": symbol,
                "current": {"date": "2026-08-06", "adjustedClose": price},
                "lookback": {"date": "2026-07-23", "adjustedClose": 100.0},
            }
            for symbol, price in [("SPY", 102.0), ("XLK", 110.0), ("XLF", 95.0)]
        ],
        "errors": [],
    }
    service = SectorSummaryService(adapter)
    application.dependency_overrides[get_sector_summary_service] = lambda: service
    params = {"periods": periods, "symbols": "XLK,XLF", "sort_by": sort_by}
    ascending = await client.get(
        "/api/v1/sector/summary", params={**params, "sort_direction": "asc"}
    )
    descending = await client.get(
        "/api/v1/sector/summary", params={**params, "sort_direction": "desc"}
    )
    assert ascending.status_code == descending.status_code == 200
    asc_payload, desc_payload = ascending.json(), descending.json()
    assert [item["symbol"] for item in asc_payload["sectors"]] == ["XLF", "XLK"]
    assert [item["symbol"] for item in desc_payload["sectors"]] == ["XLK", "XLF"]
    asc_payload["sectors"].reverse()
    assert asc_payload == desc_payload
    if "," in periods:
        assert [item["periodCode"] for item in asc_payload["sectors"][0]["periods"]] == ["1M", "2W"]
