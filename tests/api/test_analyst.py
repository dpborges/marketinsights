"""Run: .venv/Scripts/python.exe -m pytest tests/api/test_analyst.py --no-cov"""

from collections.abc import AsyncIterator
from unittest.mock import AsyncMock

import httpx
import pytest
from fastapi import FastAPI

from mi_api.config import APISettings, Environment
from mi_api.dependencies.analyst import get_analyst_service
from mi_api.main import create_app
from mi_sdk.domain.exceptions import ConfigurationError
from mi_sdk.services.analyst_service import AnalystService


@pytest.fixture
def service() -> AsyncMock:
    source = AsyncMock(spec=AnalystService)
    source.get_consensus.side_effect = lambda symbols: {
        "consensus": [
            {
                "symbol": symbol,
                "strongBuy": 2,
                "buy": 58,
                "hold": 16,
                "sell": 3,
                "strongSell": 0,
                "recommendation": "buy",
            }
            for symbol in symbols
        ],
        "errors": [],
    }
    source.get_targets.side_effect = lambda symbols: {
        "priceTargets": [
            {"symbol": symbol, "high": 400.0, "low": 245.0, "median": 360.0, "consensus": 339.35}
            for symbol in symbols
        ],
        "errors": [],
    }
    return source


@pytest.fixture
def application(service: AsyncMock) -> FastAPI:
    app = create_app(APISettings(app_env=Environment.TEST))
    app.dependency_overrides[get_analyst_service] = lambda: service
    return app


@pytest.fixture
async def client(application: FastAPI) -> AsyncIterator[httpx.AsyncClient]:
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=application, raise_app_exceptions=False),
        base_url="http://testserver",
    ) as api_client:
        yield api_client


@pytest.mark.parametrize("endpoint,key", [("consensus", "consensus"), ("targets", "priceTargets")])
@pytest.mark.parametrize("symbols", ["NVDA", "NVDA,META,AAPL,IBM", ",".join(["NVDA"] * 10)])
async def test_success(
    client: httpx.AsyncClient, service: AsyncMock, endpoint: str, key: str, symbols: str
) -> None:
    response = await client.get(f"/api/v1/analyst/{endpoint}", params={"symbols": symbols})
    assert response.status_code == 200
    method = getattr(service, f"get_{endpoint}")
    method.assert_awaited_once_with(symbols.split(","))
    assert response.json() == method.side_effect(symbols.split(","))
    assert len(response.json()[key]) == len(symbols.split(","))


@pytest.mark.parametrize("endpoint", ["consensus", "targets"])
@pytest.mark.parametrize(
    "symbols,message",
    [
        (None, "No symbols provided"),
        ("", "No symbols provided"),
        ("  ", "No symbols provided"),
        (",".join(["NVDA"] * 11), "10 symbol request limit exceeded"),
        ("NVDA,", "Each symbol must be a non-empty single stock symbol"),
    ],
)
async def test_invalid_query_before_construction(
    client: httpx.AsyncClient,
    application: FastAPI,
    endpoint: str,
    symbols: str | None,
    message: str,
) -> None:
    # Use the real dependency to ensure validation precedes provider construction.
    application.dependency_overrides.clear()
    response = await client.get(
        f"/api/v1/analyst/{endpoint}", params={} if symbols is None else {"symbols": symbols}
    )
    assert response.status_code == 400
    assert response.json()["error"]["message"] == message
    assert response.json()["error"]["parameter"] == "symbols"


@pytest.mark.parametrize("endpoint,key", [("consensus", "consensus"), ("targets", "priceTargets")])
@pytest.mark.parametrize("all_failed", [False, True])
async def test_sdk_errors_retained(
    client: httpx.AsyncClient, service: AsyncMock, endpoint: str, key: str, all_failed: bool
) -> None:
    method = getattr(service, f"get_{endpoint}")
    payload = method.side_effect([] if all_failed else ["NVDA"])
    payload["errors"] = [{"symbol": "META", "code": "RateLimitError", "message": "Rate limited."}]
    method.side_effect = None
    method.return_value = payload
    response = await client.get(f"/api/v1/analyst/{endpoint}?symbols=NVDA,META")
    assert response.status_code == 200
    assert response.json() == payload


async def test_normalization(client: httpx.AsyncClient, service: AsyncMock) -> None:
    response = await client.get("/api/v1/analyst/consensus", params={"symbols": " nvda , meta "})
    assert response.status_code == 200
    service.get_consensus.assert_awaited_once_with(["NVDA", "META"])


async def test_fatal_sdk_error(client: httpx.AsyncClient, service: AsyncMock) -> None:
    service.get_consensus.side_effect = ConfigurationError("private configuration")
    response = await client.get("/api/v1/analyst/consensus?symbols=NVDA")
    assert response.status_code == 503
    assert "private configuration" not in response.text


async def test_invalid_response_rejected(client: httpx.AsyncClient, service: AsyncMock) -> None:
    service.get_targets.side_effect = None
    service.get_targets.return_value = {"priceTargets": [{"symbol": "NVDA"}], "errors": []}
    response = await client.get("/api/v1/analyst/targets?symbols=NVDA")
    assert response.status_code == 500


async def test_openapi(client: httpx.AsyncClient) -> None:
    response = await client.get("/openapi.json")
    paths = response.json()["paths"]
    for endpoint in ("consensus", "targets"):
        operation = paths[f"/api/v1/analyst/{endpoint}"]["get"]
        assert operation["tags"] == ["analyst"]
        assert "400" in operation["responses"]
        assert operation["parameters"][0]["name"] == "symbols"
    assert (await client.get("/docs")).status_code == 200


def test_factory_configures_adapter() -> None:
    from mi_sdk.config.settings import MarketProviderSettings, SDKSettings
    from mi_sdk.factory import ServiceFactory
    from mi_sdk.providers.fmp.fmp_analyst import FMPAnalystAdapter

    settings = SDKSettings(
        _env_file=None,
        provider="fmp",
        providers=MarketProviderSettings(_env_file=None, fmp_api_key="test-key", request_timeout=7),
    )
    service = ServiceFactory(settings).create_analyst_service()
    assert isinstance(service, AnalystService)
    assert isinstance(service.adapter, FMPAnalystAdapter)
    assert service.adapter.timeout == 7
    settings.provider = "unsupported"
    with pytest.raises(ConfigurationError):
        ServiceFactory(settings).create_analyst_service()
    settings.provider = "fmp"
    settings.providers.fmp_api_key = None
    with pytest.raises(ConfigurationError):
        ServiceFactory(settings).create_analyst_service()
