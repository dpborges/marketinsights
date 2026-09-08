"""Run: ./.venv/Scripts/python.exe -m pytest tests/test_fmp_analyst.py -q."""

import json
from unittest.mock import AsyncMock

import httpx
import pytest

from mi_sdk.domain.exceptions import (
    AuthenticationError,
    AuthorizationError,
    ConfigurationError,
    DataValidationError,
    ProviderUnavailableError,
    RateLimitError,
)
from mi_sdk.providers.fmp import fmp_analyst_run
from mi_sdk.providers.fmp.fmp_analyst import FMPAnalystAdapter


@pytest.fixture
def http_get(monkeypatch: pytest.MonkeyPatch) -> AsyncMock:
    get = AsyncMock()
    monkeypatch.setattr(httpx.AsyncClient, "get", get)
    return get


def response(payload: object, status: int = 200) -> httpx.Response:
    return httpx.Response(
        status, json=payload, request=httpx.Request("GET", "https://example.test?apikey=secret")
    )


@pytest.mark.parametrize(
    "method,fields,key,expected",
    [
        (
            "get_analyst_consensus",
            {"strongBuy": 12, "buy": 28, "hold": 7, "sell": 1, "strongSell": 0},
            "analystConsensus",
            {"strongBuy": 12, "buy": 28, "hold": 7, "sell": 1, "strongSell": 0},
        ),
        (
            "get_analyst_targets",
            {"targetHigh": 250, "targetLow": 140, "targetMedian": 205, "targetConsensus": 207.35},
            "priceTarget",
            {"high": 250.0, "low": 140.0, "median": 205.0, "consensus": 207.35},
        ),
    ],
)
async def test_single_symbol_mapping(
    http_get: AsyncMock, method: str, fields: dict, key: str, expected: dict
) -> None:
    http_get.return_value = response([{"symbol": "NVDA", **fields}])
    result = await getattr(FMPAnalystAdapter(api_key="secret"), method)(symbol=" nvda ")
    assert result == {"symbol": "NVDA", key: expected}
    assert http_get.await_count == 1
    assert http_get.await_args.kwargs["params"]["symbol"] == "NVDA"
    endpoint = "grades-consensus" if key == "analystConsensus" else "price-target-consensus"
    assert http_get.await_args.args[0].endswith(endpoint)


@pytest.mark.parametrize(
    "status,error",
    [
        (401, AuthenticationError),
        (402, AuthorizationError),
        (403, AuthorizationError),
        (429, RateLimitError),
        (500, ProviderUnavailableError),
    ],
)
async def test_http_errors(http_get: AsyncMock, status: int, error: type[Exception]) -> None:
    http_get.return_value = response({}, status)
    with pytest.raises(error) as caught:
        await FMPAnalystAdapter(api_key="secret").get_analyst_targets("NVDA")
    assert "secret" not in str(caught.value)


@pytest.mark.parametrize(
    "payload",
    [
        [],
        {},
        [{"symbol": "OTHER"}],
        [{"symbol": "NVDA"}],
        [{"symbol": "NVDA", "targetHigh": None}],
        [{"symbol": "NVDA", "targetHigh": -1}],
    ],
)
async def test_invalid_payload(http_get: AsyncMock, payload: object) -> None:
    http_get.return_value = response(payload)
    with pytest.raises(DataValidationError):
        await FMPAnalystAdapter(api_key="secret").get_analyst_targets("NVDA")


@pytest.mark.parametrize("symbols", [[], ["NVDA"], None, "", " ", "NVDA,AAPL", "NVDA AAPL"])
@pytest.mark.parametrize("method", ["get_analyst_consensus", "get_analyst_targets"])
async def test_invalid_symbols(http_get: AsyncMock, symbols: object, method: str) -> None:
    with pytest.raises(DataValidationError):
        await getattr(FMPAnalystAdapter(api_key="secret"), method)(symbols)
    http_get.assert_not_awaited()


async def test_transport_failure(http_get: AsyncMock) -> None:
    http_get.side_effect = httpx.ReadTimeout("secret")
    with pytest.raises(ProviderUnavailableError, match="Unable to connect"):
        await FMPAnalystAdapter(api_key="secret").get_analyst_consensus("NVDA")


async def test_invalid_json(http_get: AsyncMock) -> None:
    http_get.return_value = httpx.Response(
        200, text="not JSON", request=httpx.Request("GET", "https://example.test")
    )
    with pytest.raises(DataValidationError, match="invalid JSON"):
        await FMPAnalystAdapter(api_key="secret").get_analyst_consensus("NVDA")


def test_env_configuration(monkeypatch: pytest.MonkeyPatch, tmp_path) -> None:
    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("MARKET_FMP_API_KEY", raising=False)
    with pytest.raises(ConfigurationError):
        FMPAnalystAdapter()
    (tmp_path / ".env").write_text("MARKET_FMP_API_KEY=test-key\n")
    assert FMPAnalystAdapter()._api_key == "test-key"


@pytest.mark.parametrize("interactive", [False, True])
def test_runner(monkeypatch: pytest.MonkeyPatch, capsys, interactive: bool) -> None:
    targets = AsyncMock(return_value={"symbol": "NVDA", "priceTarget": {"high": 250}})
    monkeypatch.setenv("MARKET_FMP_API_KEY", "test-key")
    monkeypatch.setattr(FMPAnalystAdapter, "get_analyst_targets", targets)
    answers = iter(["get_analyst_targets", "NVDA"])
    monkeypatch.setattr("builtins.input", lambda _: next(answers))
    assert fmp_analyst_run.main([] if interactive else ["get_analyst_targets", "NVDA"]) == 0
    targets.assert_awaited_once_with("NVDA")
    output = capsys.readouterr().out
    assert '"symbol": "NVDA"' in output
    if interactive:
        assert "get_analyst_consensus" in output
    else:
        assert json.loads(output)["symbol"] == "NVDA"


def test_runner_error(capsys) -> None:
    assert fmp_analyst_run.main(["unknown", "NVDA"]) == 1
    assert "UnsupportedOperationError" in capsys.readouterr().out


@pytest.mark.parametrize("method", ["get_analyst_consensus", "get_analyst_targets"])
@pytest.mark.parametrize("args", [["NVDA,AAPL"], ["NVDA", "AAPL"]])
def test_runner_rejects_multiple_symbols(monkeypatch, capsys, http_get, method, args) -> None:
    monkeypatch.setenv("MARKET_FMP_API_KEY", "test-key")
    assert fmp_analyst_run.main([method, *args]) == 1
    assert "DataValidationError" in capsys.readouterr().out
    http_get.assert_not_awaited()
