"""Run: .venv/Scripts/python.exe -m pytest tests/api/test_company.py --no-cov"""

from collections.abc import AsyncIterator
from unittest.mock import AsyncMock, Mock

import httpx
import pytest
from fastapi import FastAPI

from mi_api.config import APISettings, Environment
from mi_api.dependencies.company import get_company_service
from mi_api.main import create_app
from mi_sdk.services.company_service import CompanyService
from mi_sdk.services.exceptions import MarketDataError


@pytest.fixture
def service() -> AsyncMock:
    source = AsyncMock(spec=CompanyService)
    source.get_profile.side_effect = lambda symbols: {
        "companies": [
            {
                "symbol": symbol,
                "companyName": symbol,
                "price": 100,
                "extra": {"nested": [None, True, 12]},
            }
            for symbol in symbols
        ],
        "errors": [],
        "summary": {"requested": len(symbols), "successful": len(symbols), "failed": 0},
    }
    source.get_summary.side_effect = lambda symbols: {
        "companies": [
            {
                "symbol": symbol,
                "name": symbol,
                "price": 100,
                "sector": "Technology",
                "industry": None,
            }
            for symbol in symbols
        ],
        "errors": [],
        "summary": {"requested": len(symbols), "successful": len(symbols), "failed": 0},
    }
    return source


@pytest.fixture
def application(service: AsyncMock) -> FastAPI:
    app = create_app(APISettings(app_env=Environment.TEST))
    app.dependency_overrides[get_company_service] = lambda: service
    return app


@pytest.fixture
async def client(application: FastAPI) -> AsyncIterator[httpx.AsyncClient]:
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=application, raise_app_exceptions=False),
        base_url="http://testserver",
    ) as api_client:
        yield api_client


@pytest.mark.parametrize("endpoint", ["profile", "summary"])
@pytest.mark.parametrize("symbols", ["META", "META,MSFT", ",".join(f"SYM{i}" for i in range(10))])
async def test_success(
    client: httpx.AsyncClient, service: AsyncMock, endpoint: str, symbols: str
) -> None:
    response = await client.get(f"/api/v1/company/{endpoint}", params={"symbols": symbols})
    method = getattr(service, f"get_{endpoint}")
    assert response.status_code == 200
    assert response.json() == method.side_effect(symbols.split(","))
    method.assert_awaited_once_with(symbols.split(","))


@pytest.mark.parametrize("endpoint", ["profile", "summary"])
@pytest.mark.parametrize(
    "symbols,message",
    [
        (None, "No symbols provided"),
        ("", "No symbols provided"),
        ("  ", "No symbols provided"),
        (",".join(f"SYM{i}" for i in range(11)), "10 symbol request limit exceeded"),
        ("META,", "Each symbol must be a non-empty single stock symbol"),
        ("ME TA", "Each symbol must be a non-empty single stock symbol"),
    ],
)
async def test_validation_before_construction(
    client: httpx.AsyncClient,
    application: FastAPI,
    monkeypatch: pytest.MonkeyPatch,
    endpoint: str,
    symbols: str | None,
    message: str,
) -> None:
    application.dependency_overrides.clear()
    factory = Mock(side_effect=AssertionError("Must validate before constructing service"))
    monkeypatch.setattr("mi_api.dependencies.company.ServiceFactory", factory)
    response = await client.get(
        f"/api/v1/company/{endpoint}",
        params={} if symbols is None else {"symbols": symbols},
    )
    assert response.status_code == 400
    assert response.json()["error"]["message"] == message
    assert response.json()["error"]["code"] == "INVALID_QUERY_PARAMETER"
    assert response.json()["error"]["retryable"] is False
    factory.assert_not_called()


@pytest.mark.parametrize("endpoint", ["profile", "summary"])
async def test_normalize_deduplicate(
    client: httpx.AsyncClient, service: AsyncMock, endpoint: str
) -> None:
    response = await client.get(
        f"/api/v1/company/{endpoint}",
        params={"symbols": ",".join([" meta ", "META"] * 6 + ["msft"])},
    )
    assert response.status_code == 200
    getattr(service, f"get_{endpoint}").assert_awaited_once_with(["META", "MSFT"])
    assert response.json()["summary"] == {"requested": 2, "successful": 2, "failed": 0}


@pytest.mark.parametrize("endpoint", ["profile", "summary"])
@pytest.mark.parametrize("all_failed", [False, True])
async def test_item_failures(
    client: httpx.AsyncClient, service: AsyncMock, endpoint: str, all_failed: bool
) -> None:
    method = getattr(service, f"get_{endpoint}")
    payload = method.side_effect([] if all_failed else ["META"])
    failed = ["META", "MSFT"] if all_failed else ["MSFT"]
    payload["errors"] = [
        {"symbol": symbol, "code": "SYMBOL_NOT_FOUND", "message": "Not found.", "retryable": False}
        for symbol in failed
    ]
    payload["summary"] = {"requested": 2, "successful": 2 - len(failed), "failed": len(failed)}
    method.side_effect = None
    method.return_value = payload
    response = await client.get(f"/api/v1/company/{endpoint}?symbols=META,MSFT")
    assert response.status_code == 200
    assert response.json() == payload


@pytest.mark.parametrize("endpoint", ["profile", "summary"])
@pytest.mark.parametrize(
    "code,status",
    [
        ("PROVIDER_UNAVAILABLE", 503),
        ("PROVIDER_TIMEOUT", 504),
        ("BAD_REQUEST", 400),
        ("INVALID_QUERY_PARAMETER", 400),
        ("INVALID_API_KEY", 401),
    ],
)
async def test_operation_error(
    client: httpx.AsyncClient, service: AsyncMock, endpoint: str, code: str, status: int
) -> None:
    getattr(service, f"get_{endpoint}").side_effect = MarketDataError(
        "Unable to process request.",
        code,
        provider="private-provider",
        provider_status_code=503,
        retryable=code != "BAD_REQUEST",
    )
    response = await client.get(f"/api/v1/company/{endpoint}?symbols=META")
    assert response.status_code == status
    assert response.json() == {
        "error": {
            "code": code,
            "message": "Unable to process request.",
            "retryable": False,
        }
    }


@pytest.mark.parametrize("endpoint", ["profile", "summary"])
async def test_invalid_response(
    client: httpx.AsyncClient, service: AsyncMock, endpoint: str
) -> None:
    method = getattr(service, f"get_{endpoint}")
    method.side_effect = None
    method.return_value = {
        "companies": [{}],
        "errors": [],
        "summary": {"requested": 1, "successful": 1, "failed": 0},
    }
    assert (await client.get(f"/api/v1/company/{endpoint}?symbols=META")).status_code == 500


async def test_dependency_wiring(
    client: httpx.AsyncClient,
    application: FastAPI,
    service: AsyncMock,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    application.dependency_overrides.clear()
    factory = Mock()
    factory.return_value.create_company_service.return_value = service
    monkeypatch.setattr("mi_api.dependencies.company.ServiceFactory", factory)
    response = await client.get("/api/v1/company/profile?symbols=META")
    assert response.status_code == 200
    factory.return_value.create_company_service.assert_called_once_with()
    service.get_profile.assert_awaited_once_with(["META"])


async def test_openapi(client: httpx.AsyncClient) -> None:
    schema = (await client.get("/openapi.json")).json()
    for endpoint in ("profile", "summary"):
        operation = schema["paths"][f"/api/v1/company/{endpoint}"]["get"]
        assert operation["tags"] == ["company"]
        assert {"200", "400", "503", "504"} <= set(operation["responses"])
        assert operation["parameters"][0]["name"] == "symbols"
    assert (await client.get("/docs")).status_code == 200
