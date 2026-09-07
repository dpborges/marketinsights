"""Run from the repository root in Git Bash:

    MSYS_NO_PATHCONV=1 API_V1_PREFIX=/api/v1 ./.venv/Scripts/python.exe -m pytest tests/api/test_sector_leadership.py -q


Uses the real leadership and summary SDKs with mocked historical prices.
"""

from collections.abc import AsyncIterator
from unittest.mock import Mock

import httpx
import pytest
from fastapi import FastAPI

from mi_api.config import APISettings, Environment
from mi_api.dependencies import get_sector_leadership_service
from mi_api.main import create_app
from mi_sdk.domain.exceptions import (
    AuthenticationError,
    DataValidationError,
    ProviderUnavailableError,
)
from mi_sdk.services.sector_leadership_service import SectorLeadershipService
from mi_sdk.services.sector_summary_service import DEFAULT_SECTOR_SYMBOLS, SectorSummaryService


@pytest.fixture
def adapter() -> Mock:
    adapter = Mock()
    adapter.get_historical_prices.return_value = {
        "prices": [
            {
                "symbol": symbol,
                "current": {"date": "2026-09-04", "adjustedClose": 120.0 - index},
                "lookback": {"date": "2026-06-04", "adjustedClose": 100.0},
            }
            for index, symbol in enumerate([*DEFAULT_SECTOR_SYMBOLS, "SPY"])
        ],
        "errors": [],
    }
    return adapter


@pytest.fixture
def application(adapter: Mock) -> FastAPI:
    app = create_app(APISettings(app_env=Environment.TEST))
    service = SectorLeadershipService(SectorSummaryService(adapter))
    app.dependency_overrides[get_sector_leadership_service] = lambda: service
    return app


@pytest.fixture
async def client(application: FastAPI) -> AsyncIterator[httpx.AsyncClient]:
    transport = httpx.ASGITransport(app=application, raise_app_exceptions=False)
    async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
        yield client


@pytest.mark.parametrize("top_n", [3, 5])
@pytest.mark.parametrize("periods", [None, "2W,1M,3M", "3m, 2w,1M,2W"])
async def test_leadership_returns_requested_count(
    client: httpx.AsyncClient, adapter: Mock, top_n: int, periods: str | None
) -> None:
    params = {"top_n": str(top_n)}
    if periods is not None:
        params["periods"] = periods
    response = await client.get("/api/v1/sector/leadership", params=params)
    assert response.status_code == 200
    payload = response.json()
    assert set(payload) == {
        "benchmark",
        "asOfDate",
        "requestedSectorCount",
        "successfulSectorCount",
        "failedSectorCount",
        "sectors",
        "errors",
    }
    assert payload["benchmark"] == "SPY"
    assert payload["requestedSectorCount"] == payload["successfulSectorCount"] == 11
    assert payload["failedSectorCount"] == 0
    assert payload["errors"] == []
    assert [sector["symbol"] for sector in payload["sectors"]] == DEFAULT_SECTOR_SYMBOLS[:top_n]
    assert [sector["relativeStrengthRank"] for sector in payload["sectors"]] == list(
        range(1, top_n + 1)
    )
    for sector in payload["sectors"]:
        assert sector["outperformedBenchmark"] is True
        assert sector["interpretation"]["status"] == "strong_established_leader"
        assert sector["interpretation"]["supports_entry"] is True
        assert sector["interpretation"]["reason"]
    assert [
        call.kwargs["lookback_periods"] for call in adapter.get_historical_prices.call_args_list
    ] == [10, 21, 63]


async def test_leadership_defaults_to_five(client: httpx.AsyncClient) -> None:
    response = await client.get("/api/v1/sector/leadership")
    assert response.status_code == 200
    assert len(response.json()["sectors"]) == 5


@pytest.mark.parametrize("top_n", ["0", "1", "4", "6", "-3", "3.0", "abc", "", "true"])
async def test_leadership_rejects_invalid_top_n(
    client: httpx.AsyncClient, adapter: Mock, top_n: str
) -> None:
    response = await client.get("/api/v1/sector/leadership", params={"top_n": top_n})
    assert response.status_code == 422
    error = response.json()["error"]
    assert error["message"] == "Invald top_n value. Only 3 and 5 are supported"
    assert error["parameter"] == "top_n"
    assert error["allowedValues"] == ["3", "5"]
    adapter.get_historical_prices.assert_not_called()


@pytest.mark.parametrize("periods", ["", "2W,", "2W,1M", "1D", "2W,1M,6M", "UNKNOWN"])
async def test_leadership_rejects_invalid_periods(
    client: httpx.AsyncClient, adapter: Mock, periods: str
) -> None:
    response = await client.get("/api/v1/sector/leadership", params={"periods": periods})
    assert response.status_code == 422
    assert response.json()["error"]["parameter"] == "periods"
    adapter.get_historical_prices.assert_not_called()


async def test_leadership_preserves_partial_errors(
    client: httpx.AsyncClient, adapter: Mock
) -> None:
    error = {"symbol": "XLY", "code": "MISSING_PRICE", "message": "Price unavailable"}
    adapter.get_historical_prices.return_value["errors"] = [error]
    # An observation missing in the second period still leaves the first period
    # present for the summary service's sorting step.
    normal = adapter.get_historical_prices.return_value
    partial = {"prices": [p for p in normal["prices"] if p["symbol"] != "XLY"], "errors": [error]}
    adapter.get_historical_prices.side_effect = [normal, partial, normal]
    response = await client.get("/api/v1/sector/leadership?top_n=3")
    assert response.status_code == 200
    payload = response.json()
    assert payload["successfulSectorCount"] == 10
    assert payload["failedSectorCount"] == 1
    assert error in payload["errors"]
    assert len(payload["sectors"]) == 3


@pytest.mark.parametrize(
    ("exception", "status", "code"),
    [
        (ProviderUnavailableError, 503, "SERVICE_UNAVAILABLE"),
        (DataValidationError, 422, "DOMAIN_VALIDATION_ERROR"),
        (AuthenticationError, 401, "AUTHENTICATION_ERROR"),
    ],
)
async def test_leadership_wraps_sdk_failures(
    client: httpx.AsyncClient, adapter: Mock, exception: type[Exception], status: int, code: str
) -> None:
    adapter.get_historical_prices.side_effect = exception("private provider detail")
    response = await client.get("/api/v1/sector/leadership")
    assert response.status_code == status
    payload = response.json()
    assert payload["sectors"] == []
    assert payload["successfulSectorCount"] == 0
    assert payload["failedSectorCount"] == 11
    assert payload["errors"][0]["code"] == code
    assert payload["errors"][0]["requestId"] == response.headers["X-Request-ID"]
    assert "private provider detail" not in response.text


async def test_leadership_unexpected_failure_is_sanitized(
    client: httpx.AsyncClient, adapter: Mock
) -> None:
    adapter.get_historical_prices.side_effect = RuntimeError("private provider detail")
    response = await client.get("/api/v1/sector/leadership")
    assert response.status_code == 500
    assert response.json()["error"]["code"] == "INTERNAL_SERVER_ERROR"
    assert "private provider detail" not in response.text


def test_leadership_openapi(application: FastAPI) -> None:
    operation = application.openapi()["paths"]["/api/v1/sector/leadership"]["get"]
    parameters = {p["name"]: p["schema"] for p in operation["parameters"]}
    assert set(parameters) == {"periods", "top_n"}
    assert parameters["top_n"]["default"] == "5"
    assert parameters["top_n"]["enum"] == ["3", "5"]
    assert operation["responses"]["200"]["content"]["application/json"]["schema"]["$ref"].endswith(
        "SectorLeadershipResponse"
    )
