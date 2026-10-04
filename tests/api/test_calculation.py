"""Run: .venv/Scripts/python.exe -m pytest tests/api/test_calculation.py --no-cov"""

from collections.abc import AsyncIterator
from unittest.mock import AsyncMock, Mock

import httpx
import pytest
from fastapi import FastAPI

from mi_api.config import APISettings, Environment
from mi_api.dependencies.calculation import get_calculation_service
from mi_api.main import create_app
from mi_sdk.services.calculation_service import CalculationService
from mi_sdk.services.exceptions import MarketDataError


@pytest.fixture
def service() -> AsyncMock:
    source = AsyncMock(spec=CalculationService)
    source.get_stop_loss.side_effect = lambda symbols, horizons: {
        "companies": [
            {
                "symbol": symbol,
                "currentPrice": 100.0,
                "horizons": {
                    horizon: {
                        "stopLoss": {
                            "price": 90.123456789,
                            "downsidePct": 9.876543211,
                            "method": "SUPPORT_ATR",
                        },
                        "support": {"price": 95.0, "strength": 0.8, "touches": 3},
                        "volatility": {
                            "atr": 2.0,
                            "atrPeriod": 14,
                            "atrTimeframe": "WEEKLY" if horizon == "LONG" else "DAILY",
                            "bufferMultiplier": 2.0,
                        },
                    }
                    for horizon in horizons
                },
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
    app.dependency_overrides[get_calculation_service] = lambda: service
    return app


@pytest.fixture
async def client(application: FastAPI) -> AsyncIterator[httpx.AsyncClient]:
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=application, raise_app_exceptions=False),
        base_url="http://testserver",
    ) as api_client:
        yield api_client


@pytest.mark.parametrize(
    "symbols,horizons,expected_symbols,expected_horizons",
    [
        ("META", "SHORT,MEDIUM", ["META"], ["SHORT", "MEDIUM"]),
        ("IBM", "short,medium", ["IBM"], ["SHORT", "MEDIUM"]),
        ("AAPL", "short", ["AAPL"], ["SHORT"]),
        (",META,APPL", "SHORT,medium,LONG", ["META", "APPL"], ["SHORT", "MEDIUM", "LONG"]),
        (" meta ,META,,msft, ", " short ,SHORT,long ", ["META", "MSFT"], ["SHORT", "LONG"]),
        (",".join(f"SYM{i}" for i in range(10)), None, [f"SYM{i}" for i in range(10)], ["SHORT"]),
        (",".join(["META"] * 11), None, ["META"], ["SHORT"]),
    ],
)
async def test_success(
    client: httpx.AsyncClient,
    service: AsyncMock,
    symbols: str,
    horizons: str | None,
    expected_symbols: list[str],
    expected_horizons: list[str],
) -> None:
    params = {"symbols": symbols}
    if horizons is not None:
        params["horizons"] = horizons
    response = await client.get("/api/v1/calculation/stop-loss", params=params)
    assert response.status_code == 200
    assert response.json() == service.get_stop_loss.side_effect(expected_symbols, expected_horizons)
    service.get_stop_loss.assert_awaited_once_with(expected_symbols, expected_horizons)


@pytest.mark.parametrize(
    "params,parameter,message",
    [
        ({}, "symbols", "No symbols provided"),
        ({"symbols": ""}, "symbols", "No symbols provided"),
        ({"symbols": " , , "}, "symbols", "No symbols provided"),
        (
            {"symbols": ",".join(f"SYM{i}" for i in range(11))},
            "symbols",
            "10 symbol request limit exceeded",
        ),
        ({"symbols": "ME TA"}, "symbols", "Each symbol must be a single stock symbol"),
        ({"symbols": "META", "horizons": ""}, "horizons", "No horizons provided"),
        ({"symbols": "META", "horizons": " , "}, "horizons", "No horizons provided"),
        (
            {"symbols": "META", "horizons": "short,invalid"},
            "horizons",
            "Invalid horizon value provided",
        ),
        ({"symbols": "META", "horizons": "short,"}, "horizons", "Invalid horizon value provided"),
    ],
)
async def test_validation_before_construction(
    client: httpx.AsyncClient,
    application: FastAPI,
    monkeypatch: pytest.MonkeyPatch,
    params: dict[str, str],
    parameter: str,
    message: str,
) -> None:
    application.dependency_overrides.clear()
    factory = Mock(side_effect=AssertionError("Must validate before construction"))
    monkeypatch.setattr("mi_api.dependencies.calculation.ServiceFactory", factory)
    response = await client.get("/api/v1/calculation/stop-loss", params=params)
    assert response.status_code == 400
    error = response.json()["error"]
    assert error["message"] == message
    assert error["parameter"] == parameter
    assert error["retryable"] is False
    factory.assert_not_called()


@pytest.mark.parametrize("all_failed", [False, True])
async def test_item_failures(
    client: httpx.AsyncClient,
    service: AsyncMock,
    all_failed: bool,
) -> None:
    failed = ["META", "IBM"] if all_failed else ["IBM"]
    payload = service.get_stop_loss.side_effect([] if all_failed else ["META"], ["SHORT"])
    payload["errors"] = [
        {"symbol": symbol, "code": "SYMBOL_NOT_FOUND", "message": "Not found", "retryable": False}
        for symbol in failed
    ]
    payload["summary"] = {"requested": 2, "successful": 2 - len(failed), "failed": len(failed)}
    service.get_stop_loss.side_effect = None
    service.get_stop_loss.return_value = payload
    response = await client.get("/api/v1/calculation/stop-loss?symbols=META,IBM")
    assert response.status_code == 200
    assert response.json() == payload


@pytest.mark.parametrize(
    "code,status",
    [
        ("BAD_REQUEST", 400),
        ("INVALID_API_KEY", 401),
        ("FORBIDDEN_PLAN_LIMIT", 403),
        ("SYMBOL_NOT_FOUND", 404),
        ("PROVIDER_UNAUTHORIZED", 502),
        ("PROVIDER_ERROR", 502),
        ("RATE_LIMIT_EXCEEDED", 503),
        ("PROVIDER_UNAVAILABLE", 503),
        ("PROVIDER_TIMEOUT", 504),
        ("UNKNOWN_ERROR", 500),
    ],
)
async def test_sdk_exception_mapping(
    client: httpx.AsyncClient,
    service: AsyncMock,
    code: str,
    status: int,
) -> None:
    service.get_stop_loss.side_effect = MarketDataError(
        "Operation failed",
        code,
        provider="private-provider",
        retryable=True,
    )
    response = await client.get("/api/v1/calculation/stop-loss?symbols=META")
    assert response.status_code == status
    assert response.json()["error"]["code"] == code
    assert "private-provider" not in response.text


async def test_invalid_response(client: httpx.AsyncClient, service: AsyncMock) -> None:
    service.get_stop_loss.side_effect = None
    service.get_stop_loss.return_value = {
        "companies": [{}],
        "errors": [],
        "summary": {"requested": 1, "successful": 1, "failed": 0},
    }
    assert (await client.get("/api/v1/calculation/stop-loss?symbols=META")).status_code == 500


async def test_dependency_wiring(
    client: httpx.AsyncClient,
    application: FastAPI,
    service: AsyncMock,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    application.dependency_overrides.clear()
    factory = Mock()
    factory.return_value.create_calculation_service.return_value = service
    monkeypatch.setattr("mi_api.dependencies.calculation.ServiceFactory", factory)
    assert (await client.get("/api/v1/calculation/stop-loss?symbols=META")).status_code == 200
    factory.return_value.create_calculation_service.assert_called_once_with()
    service.get_stop_loss.assert_awaited_once_with(["META"], ["SHORT"])


async def test_openapi(client: httpx.AsyncClient) -> None:
    schema = (await client.get("/openapi.json")).json()
    operation = schema["paths"]["/api/v1/calculation/stop-loss"]["get"]
    assert operation["tags"] == ["calculation"]
    assert {"200", "400", "503", "504"} <= set(operation["responses"])
    assert {p["name"] for p in operation["parameters"]} == {"symbols", "horizons"}
    assert (await client.get("/docs")).status_code == 200
