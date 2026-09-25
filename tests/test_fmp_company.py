"""Company profile adapter and manual runner coverage without live API calls."""

import json
from pathlib import Path
from unittest.mock import AsyncMock

import httpx
import pytest

from mi_sdk.providers.common.exceptions import ProviderError
from mi_sdk.providers.fmp import fmp_adapter_run, fmp_company_run
from mi_sdk.providers.fmp.fmp_company import FMPCompanyAdapter


@pytest.fixture
def http_get(monkeypatch: pytest.MonkeyPatch) -> AsyncMock:
    get = AsyncMock()
    monkeypatch.setattr(httpx.AsyncClient, "get", get)
    return get


@pytest.mark.parametrize(
    "payload",
    [
        [{"symbol": "AAPL", "companyName": "Apple", "extra": {"value": None}}],
        [],
        {"unmapped": [1, "two", None]},
    ],
)
async def test_raw_response(http_get: AsyncMock, payload: object) -> None:
    http_get.return_value = httpx.Response(
        200, json=payload, request=httpx.Request("GET", "https://example.test")
    )
    assert await FMPCompanyAdapter(api_key="secret").get_profile(" aapl ") == payload
    http_get.assert_awaited_once_with(
        "https://financialmodelingprep.com/stable/profile",
        params={"symbol": "AAPL", "apikey": "secret"},
    )


@pytest.mark.parametrize(
    "status,code",
    [
        (401, "INVALID_API_KEY"),
        (402, "FORBIDDEN_PLAN_LIMIT"),
        (403, "FORBIDDEN_PLAN_LIMIT"),
        (429, "RATE_LIMIT_EXCEEDED"),
        (500, "PROVIDER_UNAVAILABLE"),
    ],
)
async def test_http_errors(http_get: AsyncMock, status: int, code: str) -> None:
    http_get.return_value = httpx.Response(
        status, request=httpx.Request("GET", "https://example.test?apikey=secret")
    )
    with pytest.raises(ProviderError) as caught:
        await FMPCompanyAdapter(api_key="secret").get_profile("AAPL")
    assert "secret" not in str(caught.value)
    assert caught.value.error_code == code
    assert caught.value.status_code == status
    assert caught.value.provider == "FMP"
    assert caught.value.retryable == (status == 429 or status >= 500)


async def test_transport_error(http_get: AsyncMock) -> None:
    http_get.side_effect = httpx.ReadTimeout("secret")
    with pytest.raises(ProviderError, match="timed out"):
        await FMPCompanyAdapter(api_key="secret").get_profile("AAPL")


async def test_invalid_json(http_get: AsyncMock) -> None:
    http_get.return_value = httpx.Response(
        200, text="not JSON", request=httpx.Request("GET", "https://example.test")
    )
    with pytest.raises(ProviderError, match="invalid JSON"):
        await FMPCompanyAdapter(api_key="secret").get_profile("AAPL")


@pytest.mark.parametrize("symbol", ["", " ", "AAPL,NVDA", "AAPL NVDA", None, ["AAPL"]])
async def test_invalid_symbol(http_get: AsyncMock, symbol: str) -> None:
    with pytest.raises(ProviderError) as caught:
        await FMPCompanyAdapter(api_key="secret").get_profile(symbol)
    assert caught.value.error_code == "BAD_REQUEST"
    assert caught.value.provider == "FMP"
    assert caught.value.status_code is None
    assert caught.value.retryable is False
    http_get.assert_not_awaited()


def test_configuration(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("MARKET_FMP_API_KEY", raising=False)
    with pytest.raises(ProviderError) as caught:
        FMPCompanyAdapter()
    assert caught.value.error_code == "CONFIGURATION_ERROR"
    (tmp_path / ".env").write_text("MARKET_FMP_API_KEY=dotenv-key\n")
    assert FMPCompanyAdapter()._api_key == "dotenv-key"
    monkeypatch.setenv("MARKET_FMP_API_KEY", "environment-key")
    assert FMPCompanyAdapter()._api_key == "environment-key"
    assert FMPCompanyAdapter(api_key="explicit-key")._api_key == "explicit-key"
    with pytest.raises(ProviderError) as caught:
        FMPCompanyAdapter(api_key=" ")
    assert caught.value.error_code == "CONFIGURATION_ERROR"


@pytest.mark.parametrize("interactive", [True, False])
@pytest.mark.parametrize("shared", [True, False])
def test_runners(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    interactive: bool,
    shared: bool,
) -> None:
    get_profile = AsyncMock(return_value=[{"symbol": "AAPL"}])
    monkeypatch.setattr(FMPCompanyAdapter, "get_profile", get_profile)
    monkeypatch.setenv("MARKET_FMP_API_KEY", "test-key")
    answers = iter(["get_profile", "AAPL"])
    prompts: list[str] = []

    def answer(prompt: str) -> str:
        prompts.append(prompt)
        return next(answers)

    monkeypatch.setattr("builtins.input", answer)
    runner = fmp_adapter_run if shared else fmp_company_run
    runner.main([] if interactive else ["get_profile", "AAPL"])
    get_profile.assert_awaited_once_with("AAPL")
    output = capsys.readouterr().out
    assert '"symbol": "AAPL"' in output
    if interactive:
        assert "get_profile" in output
        assert "e.g. AAPL" in prompts[-1]


@pytest.mark.parametrize("args", [["unknown"], ["get_profile", "AAPL", "NVDA"]])
def test_runner_usage_errors(args: list[str], capsys: pytest.CaptureFixture[str]) -> None:
    assert fmp_company_run.main(args) == 1
    captured = capsys.readouterr()
    assert json.loads(captured.out)["error"]["error_code"] == "BAD_REQUEST"
    assert not captured.err


def test_runner_provider_error(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.setenv("MARKET_FMP_API_KEY", "test-key")
    monkeypatch.setattr(
        FMPCompanyAdapter,
        "get_profile",
        AsyncMock(side_effect=ProviderError("Try later.", "FMP", "RATE_LIMIT_EXCEEDED", 429, True)),
    )
    assert fmp_company_run.main(["get_profile", "AAPL"]) == 1
    assert json.loads(capsys.readouterr().out) == {
        "data": None,
        "error": {
            "message": "Try later.",
            "provider": "FMP",
            "error_code": "RATE_LIMIT_EXCEEDED",
            "status_code": 429,
            "retryable": True,
        },
    }


async def test_provider_error_payload(http_get: AsyncMock) -> None:
    http_get.return_value = httpx.Response(
        200,
        json={"Error Message": "secret"},
        request=httpx.Request("GET", "https://example.test"),
    )
    with pytest.raises(ProviderError) as caught:
        await FMPCompanyAdapter(api_key="secret").get_profile("AAPL")
    assert caught.value.error_code == "PROVIDER_ERROR"
    assert "secret" not in str(caught.value)


def test_runner_success(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setenv("MARKET_FMP_API_KEY", "test-key")
    monkeypatch.setattr(FMPCompanyAdapter, "get_profile", AsyncMock(return_value=[]))
    assert fmp_company_run.main(["get_profile", "AAPL"]) == 0
    assert json.loads(capsys.readouterr().out) == {"data": [], "error": {}}


@pytest.mark.parametrize("interactive", [True, False])
def test_runner_empty_symbol(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    http_get: AsyncMock,
    interactive: bool,
) -> None:
    monkeypatch.setenv("MARKET_FMP_API_KEY", "test-key")
    answers = iter(["get_profile", ""])
    monkeypatch.setattr("builtins.input", lambda prompt: next(answers))
    assert fmp_company_run.main([] if interactive else ["get_profile", ""]) == 1
    output = capsys.readouterr().out
    payload = json.loads(output[output.index("{") :])
    assert payload == {
        "data": None,
        "error": {
            "message": "Provide one non-empty stock symbol as a string.",
            "provider": "FMP",
            "error_code": "BAD_REQUEST",
            "status_code": None,
            "retryable": False,
        },
    }
    http_get.assert_not_awaited()


def test_runner_missing_api_key(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("MARKET_FMP_API_KEY", raising=False)
    assert fmp_company_run.main(["get_profile", "AAPL"]) == 1
    error = json.loads(capsys.readouterr().out)["error"]
    assert error["error_code"] == "CONFIGURATION_ERROR"
    assert error["provider"] == "FMP"
