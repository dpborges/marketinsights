"""Historical pricing request validation and interactive runner coverage.
   gitbash command line syntax: 
   .venv/Scripts/python.exe -m pytest tests/test_fmp_company_history.py
"""

# Run from the repository root in Git Bash:
# .venv/Scripts/python.exe -m pytest tests/test_fmp_company_history.py

import json
from typing import Any
from unittest.mock import AsyncMock

import httpx
import pytest

from mi_sdk.providers.common.exceptions import ProviderError
from mi_sdk.providers.fmp import fmp_company_run
from mi_sdk.providers.fmp.fmp_company import FMPCompanyAdapter


@pytest.mark.parametrize("payload", [[], [{"date": "2024-02-29", "close": 12, "extra": None}]])
async def test_history_raw_response(monkeypatch: pytest.MonkeyPatch, payload: object) -> None:
    get = AsyncMock(
        return_value=httpx.Response(
            200, json=payload, request=httpx.Request("GET", "https://example.test")
        )
    )
    monkeypatch.setattr(httpx.AsyncClient, "get", get)
    result = await FMPCompanyAdapter(api_key="secret").get_historical_pricing(
        " nvda ", "2024-02-29", "2024-02-29"
    )
    assert result == payload
    get.assert_awaited_once_with(
        "https://financialmodelingprep.com/stable/historical-price-eod/full",
        params={"symbol": "NVDA", "from": "2024-02-29", "to": "2024-02-29", "apikey": "secret"},
    )


@pytest.mark.parametrize(
    "dates",
    [
        (),
        ("2026-03-01",),
        (None, "2026-09-28"),
        ("", ""),
        ("2026-02-29", "2026-03-01"),
        ("2026-04-31", "2026-05-01"),
        ("2026-3-01", "2026-09-28"),
        ("20260301", "2026-09-28"),
        ("2026-03-01", "2026-13-01"),
        ("2026-09-28", "2026-03-01"),
        ("0000-01-01", "2026-03-01"),
        (123, "2026-03-01"),
    ],
)
async def test_history_invalid_dates(
    monkeypatch: pytest.MonkeyPatch, dates: tuple[Any, ...]
) -> None:
    get = AsyncMock()
    monkeypatch.setattr(httpx.AsyncClient, "get", get)
    with pytest.raises(ProviderError) as caught:
        await FMPCompanyAdapter(api_key="secret").get_historical_pricing("NVDA", *dates)
    assert caught.value.error_code == "BAD_REQUEST"
    assert caught.value.retryable is False
    get.assert_not_awaited()


@pytest.mark.parametrize("symbol", ["", "NVDA,AAPL", "NVDA AAPL"])
async def test_history_invalid_symbol(monkeypatch: pytest.MonkeyPatch, symbol: str) -> None:
    get = AsyncMock()
    monkeypatch.setattr(httpx.AsyncClient, "get", get)
    with pytest.raises(ProviderError):
        await FMPCompanyAdapter(api_key="secret").get_historical_pricing(
            symbol, "2026-03-01", "2026-09-28"
        )
    get.assert_not_awaited()


@pytest.mark.parametrize(
    "status,code",
    [
        (401, "INVALID_API_KEY"),
        (403, "FORBIDDEN_PLAN_LIMIT"),
        (429, "RATE_LIMIT_EXCEEDED"),
        (503, "PROVIDER_UNAVAILABLE"),
    ],
)
async def test_history_http_errors(monkeypatch: pytest.MonkeyPatch, status: int, code: str) -> None:
    monkeypatch.setattr(
        httpx.AsyncClient,
        "get",
        AsyncMock(
            return_value=httpx.Response(
                status, request=httpx.Request("GET", "https://example.test?apikey=secret")
            )
        ),
    )
    with pytest.raises(ProviderError) as caught:
        await FMPCompanyAdapter(api_key="secret").get_historical_pricing(
            "NVDA", "2026-03-01", "2026-09-28"
        )
    assert caught.value.error_code == code
    assert caught.value.status_code == status
    assert "secret" not in str(caught.value)


@pytest.mark.parametrize("interactive", [True, False])
def test_history_runner(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str], interactive: bool
) -> None:
    monkeypatch.setenv("MARKET_FMP_API_KEY", "secret")
    get = AsyncMock(return_value=[{"symbol": "NVDA", "close": 12}])
    monkeypatch.setattr(FMPCompanyAdapter, "get_historical_pricing", get)
    args = ["get_historical_pricing", "NVDA", "2026-03-01", "2026-09-28"]
    answers = iter(args)
    prompts: list[str] = []

    def answer(prompt: str) -> str:
        prompts.append(prompt)
        return next(answers)

    monkeypatch.setattr("builtins.input", answer)
    assert fmp_company_run.main([] if interactive else args) == 0
    get.assert_awaited_once_with(*args[1:])
    output = capsys.readouterr().out
    assert json.loads(output[output.index("{") :])["data"][0]["close"] == 12
    if interactive:
        assert "get_profile" in output and "get_historical_pricing" in output
        assert "YYYY-MM-DD" in prompts[2] and "e.g." in prompts[3]


@pytest.mark.parametrize("dates", [[], ["2026-03-01"], ["2026-02-29", "2026-03-01"]])
def test_history_runner_errors(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str], dates: list[str]
) -> None:
    monkeypatch.setenv("MARKET_FMP_API_KEY", "secret")
    assert fmp_company_run.main(["get_historical_pricing", "NVDA", *dates]) == 1
    captured = capsys.readouterr()
    payload = json.loads(captured.out)
    assert payload["data"] is None
    assert payload["error"]["error_code"] == "BAD_REQUEST"
    assert payload["error"]["provider"] == "FMP"
    assert payload["error"]["retryable"] is False
    assert not captured.err
