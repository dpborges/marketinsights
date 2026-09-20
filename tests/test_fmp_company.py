"""Company profile adapter and manual runner coverage without live API calls."""

from pathlib import Path
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
    http_get.return_value = httpx.Response(
        status, request=httpx.Request("GET", "https://example.test?apikey=secret")
    )
    with pytest.raises(error) as caught:
        await FMPCompanyAdapter(api_key="secret").get_profile("AAPL")
    assert "secret" not in str(caught.value)


async def test_transport_error(http_get: AsyncMock) -> None:
    http_get.side_effect = httpx.ReadTimeout("secret")
    with pytest.raises(ProviderUnavailableError, match="Unable to connect"):
        await FMPCompanyAdapter(api_key="secret").get_profile("AAPL")


async def test_invalid_json(http_get: AsyncMock) -> None:
    http_get.return_value = httpx.Response(
        200, text="not JSON", request=httpx.Request("GET", "https://example.test")
    )
    with pytest.raises(DataValidationError, match="invalid JSON"):
        await FMPCompanyAdapter(api_key="secret").get_profile("AAPL")


@pytest.mark.parametrize("symbol", ["", " ", "AAPL,NVDA", "AAPL NVDA", None, ["AAPL"]])
async def test_invalid_symbol(http_get: AsyncMock, symbol: str) -> None:
    with pytest.raises(DataValidationError):
        await FMPCompanyAdapter(api_key="secret").get_profile(symbol)
    http_get.assert_not_awaited()


def test_configuration(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("MARKET_FMP_API_KEY", raising=False)
    with pytest.raises(ConfigurationError):
        FMPCompanyAdapter()
    (tmp_path / ".env").write_text("MARKET_FMP_API_KEY=dotenv-key\n")
    assert FMPCompanyAdapter()._api_key == "dotenv-key"
    monkeypatch.setenv("MARKET_FMP_API_KEY", "environment-key")
    assert FMPCompanyAdapter()._api_key == "environment-key"
    assert FMPCompanyAdapter(api_key="explicit-key")._api_key == "explicit-key"
    with pytest.raises(ConfigurationError):
        FMPCompanyAdapter(api_key=" ")


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
    assert "SDK Error" in captured.out
    assert not captured.err


def test_runner_provider_error(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.setenv("MARKET_FMP_API_KEY", "test-key")
    monkeypatch.setattr(
        FMPCompanyAdapter, "get_profile", AsyncMock(side_effect=RateLimitError("Try later."))
    )
    assert fmp_company_run.main(["get_profile", "AAPL"]) == 1
    assert "RateLimitError: Try later." in capsys.readouterr().out
