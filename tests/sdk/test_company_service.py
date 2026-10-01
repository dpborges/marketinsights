"""Run: .venv/Scripts/python.exe -m pytest tests/sdk/test_company_service.py"""

import asyncio
from datetime import date
from typing import Any
from unittest.mock import AsyncMock

import pytest

from mi_sdk import CompanyService, MarketDataError, ServiceFactory
from mi_sdk.config.settings import MarketProviderSettings, SDKSettings
from mi_sdk.interfaces.adapters import CompanyAdapter
from mi_sdk.providers.common.exceptions import ProviderError
from mi_sdk.providers.fmp.fmp_company import FMPCompanyAdapter
from mi_sdk.services.batch_result_handler import collect_batch


async def test_historical_pricing_ibm_month(adapter: AsyncMock, monkeypatch: Any) -> None:
    class Today(date):
        @classmethod
        def today(cls) -> "Today":
            return cls(2026, 9, 30)

    monkeypatch.setattr("mi_sdk.services.company_service.date", Today)
    rows = [{"symbol": "IBM", "date": "2026-09-30", "close": 250.0}]
    adapter.get_historical_pricing.return_value = rows
    result = await CompanyService(adapter).get_historical_pricing("IBM", lookback_period="1M")
    adapter.get_historical_pricing.assert_awaited_once_with("IBM", "2026-08-30", "2026-09-30")
    assert result == {"requestedTradingDays": 1, "priceData": rows, "errors": []}


async def test_historical_pricing_csco_dates(adapter: AsyncMock) -> None:
    rows = [
        {"symbol": "CSCO", "date": "2026-09-30", "close": 70.0, "volume": 100},
        {"symbol": "CSCO", "date": "2026-09-29", "close": 69.0, "volume": 200},
    ]
    adapter.get_historical_pricing.return_value = {"data": rows}
    result = await CompanyService(adapter).get_historical_pricing(
        "CSCO", from_date="2026-08-30", to_date="2026-09-30"
    )
    adapter.get_historical_pricing.assert_awaited_once_with("CSCO", "2026-08-30", "2026-09-30")
    assert result == {"requestedTradingDays": 2, "priceData": rows, "errors": []}


@pytest.mark.parametrize(
    "period,expected",
    [
        ("1D", "2026-09-30"),
        ("2D", "2026-09-29"),
        ("3D", "2026-09-28"),
        ("4D", "2026-09-27"),
        ("5D", "2026-09-26"),
        ("1W", "2026-09-23"),
        ("2W", "2026-09-16"),
        ("1M", "2026-08-30"),
        ("3M", "2026-06-30"),
        ("6M", "2026-03-30"),
        ("9M", "2025-12-30"),
        ("12M", "2025-09-30"),
        ("18M", "2025-03-30"),
        ("1Y", "2025-09-30"),
        ("2Y", "2024-09-30"),
        ("3Y", "2023-09-30"),
        ("4Y", "2022-09-30"),
        ("5Y", "2021-09-30"),
    ],
)
def test_historical_period_dates(period: str, expected: str) -> None:
    assert (
        CompanyService.convert_period_code_to_from_date(period, as_of_date=date(2026, 9, 30))
        == expected
    )


@pytest.mark.parametrize(
    "anchor,period,expected",
    [
        (date(2026, 3, 31), "1M", "2026-02-28"),
        (date(2024, 3, 31), "1M", "2024-02-29"),
        (date(2024, 2, 29), "1Y", "2023-02-28"),
    ],
)
def test_historical_period_month_end(anchor: date, period: str, expected: str) -> None:
    assert CompanyService.convert_period_code_to_from_date(period, as_of_date=anchor) == expected


@pytest.mark.parametrize(
    "kwargs",
    [
        {},
        {"from_date": "2026-09-01"},
        {"to_date": "2026-09-30"},
        {"lookback_period": "7D"},
        {"lookback_period": ""},
        {"lookback_period": 1},
        {"lookback_period": "1M", "from_date": "2026-09-01"},
        {"lookback_period": "1M", "to_date": "2026-09-30"},
        {"from_date": "2026-02-30", "to_date": "2026-09-30"},
        {"from_date": "2026-9-01", "to_date": "2026-09-30"},
        {"from_date": "2026-10-01", "to_date": "2026-09-30"},
    ],
)
async def test_historical_invalid_dates(adapter: AsyncMock, kwargs: dict[str, Any]) -> None:
    with pytest.raises(MarketDataError) as caught:
        await CompanyService(adapter).get_historical_pricing("IBM", **kwargs)
    assert caught.value.error_code == "BAD_REQUEST"
    adapter.get_historical_pricing.assert_not_awaited()


@pytest.mark.parametrize("symbol", [None, "", "IBM,CSCO", ["IBM"], "I BM"])
async def test_historical_invalid_symbol(adapter: AsyncMock, symbol: Any) -> None:
    with pytest.raises(MarketDataError) as caught:
        await CompanyService(adapter).get_historical_pricing(symbol, lookback_period="1M")
    assert caught.value.error_code == "BAD_REQUEST"
    adapter.get_historical_pricing.assert_not_awaited()


async def test_historical_provider_failure(adapter: AsyncMock) -> None:
    error = ProviderError("Timed out", "FMP", "PROVIDER_TIMEOUT", 504, True)
    adapter.get_historical_pricing.side_effect = error
    with pytest.raises(MarketDataError) as caught:
        await CompanyService(adapter).get_historical_pricing("IBM", lookback_period="1M")
    assert caught.value.error_code == error.error_code
    assert caught.value.provider == error.provider
    assert caught.value.provider_status_code == 504
    assert caught.value.retryable is True
    assert caught.value.__cause__ is error


@pytest.mark.parametrize("payload", [[], {"data": []}])
async def test_historical_empty_prices(adapter: AsyncMock, payload: Any) -> None:
    adapter.get_historical_pricing.return_value = payload
    assert await CompanyService(adapter).get_historical_pricing("IBM", lookback_period="1D") == {
        "requestedTradingDays": 0,
        "priceData": [],
        "errors": [],
    }


@pytest.mark.parametrize("payload", [None, {}, {"data": None}, [1]])
async def test_historical_invalid_response(adapter: AsyncMock, payload: Any) -> None:
    adapter.get_historical_pricing.return_value = payload
    with pytest.raises(MarketDataError) as caught:
        await CompanyService(adapter).get_historical_pricing("IBM", lookback_period="1M")
    assert caught.value.error_code == "PROVIDER_ERROR"


def profile(symbol: str) -> dict[str, Any]:
    return {
        "symbol": symbol,
        "companyName": f"{symbol} Company",
        "price": 100,
        "sector": "Technology",
        "industry": "Semiconductors",
        "extra": {"unchanged": [1, None]},
    }


@pytest.fixture
def adapter() -> AsyncMock:
    source = AsyncMock(spec=CompanyAdapter)
    source.get_profile.side_effect = lambda symbol: [profile(symbol)]
    return source


@pytest.mark.parametrize("symbols", ["IBM", ["NVDA", "META"]])
async def test_get_profile(adapter: AsyncMock, symbols: str | list[str]) -> None:
    requested = [symbols] if isinstance(symbols, str) else symbols
    result = await CompanyService(adapter).get_profile(symbols)
    assert result == {
        "companies": [profile(symbol) for symbol in requested],
        "errors": [],
        "summary": {"requested": len(requested), "successful": len(requested), "failed": 0},
    }


@pytest.mark.parametrize("symbols", ["IBM", ["NVDA", "META", "AAPL", "IBM", "AVGO"]])
async def test_get_summary(adapter: AsyncMock, symbols: str | list[str]) -> None:
    requested = [symbols] if isinstance(symbols, str) else symbols
    result = await CompanyService(adapter).get_summary(symbols)
    assert result == {
        "companies": [
            {
                "symbol": symbol,
                "name": f"{symbol} Company",
                "price": 100,
                "sector": "Technology",
                "industry": "Semiconductors",
            }
            for symbol in requested
        ],
        "errors": [],
        "summary": {"requested": len(requested), "successful": len(requested), "failed": 0},
    }


@pytest.mark.parametrize("method", ["get_profile", "get_summary"])
async def test_missing_symbols(adapter: AsyncMock, method: str) -> None:
    with pytest.raises(MarketDataError) as caught:
        await getattr(CompanyService(adapter), method)()
    assert caught.value.error_code == "BAD_REQUEST"
    assert caught.value.retryable is False
    adapter.get_profile.assert_not_awaited()


@pytest.mark.parametrize("method", ["get_profile", "get_summary"])
@pytest.mark.parametrize(
    "symbols", [None, "", "  ", [], ["IBM", ""], [None], 5, "NVDA,META", ["N VDA"]]
)
async def test_invalid_input(adapter: AsyncMock, method: str, symbols: Any) -> None:
    with pytest.raises(MarketDataError) as caught:
        await getattr(CompanyService(adapter), method)(symbols)
    assert caught.value.error_code == "BAD_REQUEST"
    assert caught.value.retryable is False
    adapter.get_profile.assert_not_awaited()


@pytest.mark.parametrize("method", ["get_profile", "get_summary"])
async def test_limit_and_deduplication(adapter: AsyncMock, method: str) -> None:
    operation = getattr(CompanyService(adapter), method)
    with pytest.raises(MarketDataError, match="^exceeded maximum of 10 symbols per request$"):
        await operation([f"SYM{i}" for i in range(11)])
    adapter.get_profile.assert_not_awaited()
    result = await operation([" ibm ", "IBM"] * 6 + [f"SYM{i}" for i in range(9)])
    assert result["summary"] == {"requested": 10, "successful": 10, "failed": 0}
    assert [call.args[0] for call in adapter.get_profile.await_args_list] == [
        "IBM",
        *[f"SYM{i}" for i in range(9)],
    ]


@pytest.mark.parametrize("method", ["get_profile", "get_summary"])
async def test_concurrent_partial_failures(adapter: AsyncMock, method: str) -> None:
    started: list[str] = []
    completed: list[str] = []
    ready = asyncio.Event()
    symbols = [f"SYM{i}" for i in range(10)]

    async def fetch(symbol: str) -> list[dict[str, Any]]:
        started.append(symbol)
        if len(started) == 10:
            ready.set()
        await asyncio.wait_for(ready.wait(), timeout=2)
        completed.append(symbol)
        if symbol == "SYM2":
            raise ProviderError("Not found.", "FMP", "SYMBOL_NOT_FOUND", 404, False)
        if symbol == "SYM8":
            raise ProviderError("Timed out.", "FMP", "PROVIDER_TIMEOUT", None, True)
        return [profile(symbol)]

    adapter.get_profile.side_effect = fetch
    result = await getattr(CompanyService(adapter), method)(symbols)
    assert len(completed) == 10
    assert [row["symbol"] for row in result["companies"]] == [
        symbol for symbol in symbols if symbol not in ("SYM2", "SYM8")
    ]
    assert result["summary"] == {"requested": 10, "successful": 8, "failed": 2}
    assert result["errors"] == [
        {"symbol": "SYM2", "code": "SYMBOL_NOT_FOUND", "message": "Not found.", "retryable": False},
        {"symbol": "SYM8", "code": "PROVIDER_TIMEOUT", "message": "Timed out.", "retryable": True},
    ]


@pytest.mark.parametrize("method", ["get_profile", "get_summary"])
async def test_all_not_found(adapter: AsyncMock, method: str) -> None:
    adapter.get_profile.side_effect = None
    adapter.get_profile.return_value = []
    result = await getattr(CompanyService(adapter), method)(["BAD1", "BAD2"])
    assert result["companies"] == []
    assert result["summary"] == {"requested": 2, "successful": 0, "failed": 2}
    assert result["errors"] == [
        {
            "symbol": symbol,
            "code": "SYMBOL_NOT_FOUND",
            "message": f"Symbol {symbol} was not found.",
            "retryable": False,
        }
        for symbol in ["BAD1", "BAD2"]
    ]


@pytest.mark.parametrize("method", ["get_profile", "get_summary"])
@pytest.mark.parametrize(
    "codes,expected",
    [
        (["PROVIDER_TIMEOUT"] * 2, "PROVIDER_TIMEOUT"),
        (["PROVIDER_UNAVAILABLE"] * 2, "PROVIDER_UNAVAILABLE"),
        (["PROVIDER_TIMEOUT", "PROVIDER_UNAVAILABLE"], "PROVIDER_UNAVAILABLE"),
    ],
)
async def test_operation_failure(
    adapter: AsyncMock, method: str, codes: list[str], expected: str
) -> None:
    adapter.get_profile.side_effect = [
        ProviderError(
            "Unavailable.",
            "FMP",
            code,
            503 if code == "PROVIDER_UNAVAILABLE" else None,
            True,
        )
        for code in codes
    ]
    with pytest.raises(MarketDataError) as caught:
        await getattr(CompanyService(adapter), method)(["IBM", "NVDA"])
    assert caught.value.error_code == expected
    assert caught.value.provider == "FMP"
    assert caught.value.provider_status_code == (
        503 if expected == "PROVIDER_UNAVAILABLE" else None
    )
    assert caught.value.retryable is True
    assert adapter.get_profile.await_count == 2


async def test_partial_unavailability(adapter: AsyncMock) -> None:
    adapter.get_profile.side_effect = [
        ProviderError("Unavailable.", "FMP", "PROVIDER_UNAVAILABLE", 503, True),
        [profile("IBM")],
    ]
    result = await CompanyService(adapter).get_profile(["NVDA", "IBM"])
    assert result["summary"] == {"requested": 2, "successful": 1, "failed": 1}
    assert result["errors"][0]["code"] == "PROVIDER_UNAVAILABLE"


async def test_mixed_all_failed(adapter: AsyncMock) -> None:
    adapter.get_profile.side_effect = [
        [],
        ProviderError("Unavailable.", "FMP", "PROVIDER_UNAVAILABLE", 503, True),
    ]
    result = await CompanyService(adapter).get_profile(["BAD", "IBM"])
    assert result["summary"] == {"requested": 2, "successful": 0, "failed": 2}


@pytest.mark.parametrize("payload", [None, {}, [1], [{"symbol": "OTHER"}], [profile("IBM")] * 2])
async def test_malformed_payload(adapter: AsyncMock, payload: Any) -> None:
    adapter.get_profile.side_effect = None
    adapter.get_profile.return_value = payload
    result = await CompanyService(adapter).get_profile("IBM")
    assert result["companies"] == []
    assert result["errors"][0]["code"] == "PROVIDER_ERROR"


async def test_unexpected_exception_is_not_item_error(adapter: AsyncMock) -> None:
    adapter.get_profile.side_effect = RuntimeError("Programming defect")
    with pytest.raises(RuntimeError, match="Programming defect"):
        await CompanyService(adapter).get_profile("IBM")


async def test_batch_can_serve_other_domains() -> None:
    fetch = AsyncMock(return_value={"eps": 1.5})
    result = await collect_batch("IBM", fetch, "earnings")
    assert result == {
        "earnings": [{"eps": 1.5}],
        "errors": [],
        "summary": {"requested": 1, "successful": 1, "failed": 0},
    }


def test_factory() -> None:
    settings = SDKSettings(
        provider="fmp",
        providers=MarketProviderSettings(
            fmp_api_key="test-key",
            request_timeout=7,
        ),
    )
    service = ServiceFactory(settings).create_company_service()
    assert isinstance(service, CompanyService)
    assert isinstance(service.adapter, FMPCompanyAdapter)
    assert service.adapter.timeout == 7
    assert service.adapter._api_key == "test-key"


@pytest.mark.parametrize("provider,key", [("unknown", "key"), ("fmp", "")])
def test_factory_configuration_error(provider: str, key: str) -> None:
    settings = SDKSettings(provider=provider, providers=MarketProviderSettings(fmp_api_key=key))
    with pytest.raises(MarketDataError) as caught:
        ServiceFactory(settings).create_company_service()
    assert caught.value.error_code == "CONFIGURATION_ERROR"
    assert caught.value.retryable is False
