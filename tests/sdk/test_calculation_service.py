"""Deterministic stop-loss tests (no credentials or live market data needed).

Git Bash: 
PowerShell: .\\.venv\\Scripts\\python.exe -m pytest tests/sdk/test_calculation_service.py
"""

import os
from datetime import date, timedelta
from math import sin
from typing import Any
from unittest.mock import AsyncMock

import pytest
from pydantic import ValidationError

from mi_sdk import (
    CalculationService,
    InvestmentHorizon,
    MarketDataError,
    ServiceFactory,
    StopLossSettings,
)
from mi_sdk.config.settings import MarketProviderSettings, SDKSettings
from mi_sdk.interfaces.adapters import CompanyAdapter
from mi_sdk.providers.common.exceptions import ProviderError
from mi_sdk.services.company_service import CompanyService
from mi_sdk.services.stop_loss_calculations import (
    PriceBar,
    SwingLow,
    calculate_atr,
    find_swing_lows,
    parse_bars,
    select_support,
    weekly_bars,
)

AS_OF = date(2026, 10, 2)


@pytest.fixture(autouse=True)
def isolated_settings(monkeypatch: pytest.MonkeyPatch) -> None:
    for settings_class in (StopLossSettings, SDKSettings, MarketProviderSettings):
        monkeypatch.setitem(settings_class.model_config, "env_file", None)
    for name in os.environ:
        if name.startswith("STOP_LOSS_"):
            monkeypatch.delenv(name)


def historical_rows() -> list[dict[str, Any]]:
    rows = []
    for index in range(1200):
        day = AS_OF - timedelta(days=1199 - index)
        if day.weekday() >= 5:
            continue
        price = 100 + 6 * sin(index / 12) + 2 * sin(index / 2)
        rows.append(
            {
                "date": day.isoformat(),
                "open": price,
                "high": price + 3,
                "low": price - 3,
                "close": price + 1,
                "volume": 1000,
            }
        )
    return rows


@pytest.fixture
def company() -> AsyncMock:
    mock = AsyncMock(spec=CompanyService)

    async def summary(symbols: list[str]) -> dict[str, Any]:
        return {
            "companies": [{"symbol": symbols[0], "price": 130.0}],
            "errors": [],
            "summary": {"requested": 1, "successful": 1, "failed": 0},
        }

    mock.get_summary.side_effect = summary
    mock.get_historical_pricing.return_value = {"priceData": list(reversed(historical_rows()))}
    return mock


def service(company: AsyncMock, **kwargs: Any) -> CalculationService:
    return CalculationService(company, StopLossSettings(), today=lambda: AS_OF, **kwargs)


@pytest.mark.parametrize(
    "symbol,horizons,start",
    [
        ("AAPL", ["SHORT"], "2026-04-02"),
        ("AAPL", ["SHORT", "MEDIUM"], "2025-10-02"),
        ("IBM", ["SHORT", "MEDIUM", "LONG"], "2023-10-02"),
    ],
)
async def test_requested_examples(
    company: AsyncMock,
    symbol: str,
    horizons: list[str],
    start: str,
) -> None:
    result = await service(company).get_stop_loss([symbol], horizons)
    assert result["errors"] == []
    assert result["summary"] == {"requested": 1, "successful": 1, "failed": 0}
    record = result["companies"][0]
    assert record["currentPrice"] == 130.0  # summary quote, never the historical close
    assert list(record["horizons"]) == horizons
    company.get_summary.assert_awaited_once_with([symbol])
    company.get_historical_pricing.assert_awaited_once_with(
        symbol, from_date=start, to_date=AS_OF.isoformat()
    )
    for horizon, outcome in record["horizons"].items():
        stop, support, volatility = (outcome[key] for key in ("stopLoss", "support", "volatility"))
        assert stop["price"] == pytest.approx(
            support["price"] - volatility["atr"] * volatility["bufferMultiplier"]
        )
        assert stop["downsidePct"] == pytest.approx((130 - stop["price"]) / 130 * 100)
        assert volatility["atrTimeframe"] == ("WEEKLY" if horizon == "LONG" else "DAILY")
        assert volatility["atrPeriod"] == (20 if horizon == "MEDIUM" else 14)
        assert 0 <= support["strength"] <= 1


async def test_horizon_independence_and_determinism(company: AsyncMock) -> None:
    sdk = service(company)
    first = await sdk.get_stop_loss(["AAPL"], ["SHORT"])
    combined = await sdk.get_stop_loss(["AAPL"], ["SHORT", "LONG"])
    again = await sdk.get_stop_loss(["AAPL"], ["SHORT"])
    assert first == again
    assert (
        first["companies"][0]["horizons"]["SHORT"] == combined["companies"][0]["horizons"]["SHORT"]
    )


async def test_normalization_and_duplicates(company: AsyncMock) -> None:
    result = await service(company).get_stop_loss(
        [" aapl ", "AAPL"], ["short", " SHORT ", InvestmentHorizon.MEDIUM]
    )
    assert list(result["companies"][0]["horizons"]) == ["SHORT", "MEDIUM"]
    assert result["summary"]["requested"] == 1
    assert company.get_historical_pricing.await_count == 1


@pytest.mark.parametrize(
    "symbols,horizons",
    [
        ([], ["SHORT"]),
        ([str(i) for i in range(11)], ["SHORT"]),
        (["AAPL"], []),
        (["AAPL"], ["INVALID"]),
        (["AAPL"], [None]),
        (["AAPL"], "SHORT"),
        ([""], ["SHORT"]),
    ],
)
async def test_bad_request_before_io(company: AsyncMock, symbols: Any, horizons: Any) -> None:
    with pytest.raises(MarketDataError) as exc:
        await service(company).get_stop_loss(symbols, horizons)
    assert exc.value.error_code == "BAD_REQUEST"
    company.get_summary.assert_not_awaited()
    company.get_historical_pricing.assert_not_awaited()


@pytest.mark.parametrize("price", [None, 0, -1, float("nan"), float("inf"), True, "130"])
async def test_invalid_quote(company: AsyncMock, price: Any) -> None:
    company.get_summary.side_effect = None
    company.get_summary.return_value = {"companies": [{"symbol": "AAPL", "price": price}]}
    result = await service(company).get_stop_loss(["AAPL"], ["SHORT"])
    assert result["errors"][0]["code"] == "INVALID_PRICE_DATA"
    company.get_historical_pricing.assert_not_awaited()


async def test_partial_batch_summary_error(company: AsyncMock) -> None:
    original = company.get_summary.side_effect

    async def summary(symbols: list[str]) -> dict[str, Any]:
        if symbols == ["BAD"]:
            return {
                "companies": [],
                "errors": [
                    {
                        "symbol": "BAD",
                        "code": "SYMBOL_NOT_FOUND",
                        "message": "Unknown symbol",
                        "retryable": False,
                    }
                ],
            }
        return await original(symbols)  # type: ignore[no-any-return]

    company.get_summary.side_effect = summary
    result = await service(company).get_stop_loss(["AAPL", "BAD"], ["SHORT"])
    assert result["summary"] == {"requested": 2, "successful": 1, "failed": 1}
    assert result["errors"][0]["symbol"] == "BAD"
    assert result["companies"][0]["symbol"] == "AAPL"


@pytest.mark.parametrize("code", ["PROVIDER_TIMEOUT", "PROVIDER_UNAVAILABLE"])
async def test_operation_wide_failure(company: AsyncMock, code: str) -> None:
    company.get_historical_pricing.side_effect = MarketDataError("Unavailable", code)
    with pytest.raises(MarketDataError) as exc:
        await service(company).get_stop_loss(["AAPL", "IBM"], ["SHORT"])
    assert exc.value.error_code == code
    assert exc.value.retryable


async def test_partial_horizon_fails_whole_symbol(company: AsyncMock) -> None:
    company.get_historical_pricing.return_value = {"priceData": historical_rows()[-60:]}
    result = await service(company).get_stop_loss(["AAPL"], ["SHORT", "LONG"])
    assert result["companies"] == []
    assert result["errors"][0]["code"] == "INSUFFICIENT_HISTORY"
    assert result["summary"]["failed"] == 1


def bars_with_lows(lows: list[float]) -> list[PriceBar]:
    return [
        PriceBar(
            date=date(2026, 1, 1) + timedelta(days=i),
            open=low + 1,
            high=low + 2,
            low=low,
            close=low + 1,
            volume=10,
        )
        for i, low in enumerate(lows)
    ]


def test_wilder_atr_uses_previous_close_and_smoothing() -> None:
    bars = bars_with_lows([10, 11, 15, 14, 16])
    # TR = 2, 5, 2, 3; seed(3) = 3; final Wilder ATR = 3.
    assert calculate_atr(bars, 3) == 3
    assert calculate_atr(bars, 2) == pytest.approx(2.875)
    with pytest.raises(MarketDataError):
        calculate_atr(bars[:3], 3)


@pytest.mark.parametrize(
    "lows,expected",
    [
        ([103, 101, 97, 99, 102], [SwingLow(2, 97)]),
        ([103, 101, 97, 97, 97, 99, 102], [SwingLow(4, 97)]),
        ([97] * 10, []),
        ([1, 2, 3, 4, 5], []),
        ([5, 4, 3, 2, 1], []),
    ],
)
def test_confirmed_swings(lows: list[float], expected: list[SwingLow]) -> None:
    assert find_swing_lows(bars_with_lows(lows)) == expected


def test_weekly_ohlcv_and_exclusion() -> None:
    bars = [
        bar.model_copy(update={"date": date(2026, 9, 21) + timedelta(days=i)})
        for i, bar in enumerate(bars_with_lows([10, 11, 9, 12, 10, 13, 11, 1, 2, 3, 4, 5]))
    ]
    weeks = weekly_bars(bars, AS_OF)
    assert len(weeks) == 1
    assert weeks[0].model_dump() == {
        "date": date(2026, 9, 27),
        "open": 11,
        "high": 15,
        "low": 9,
        "close": 12,
        "volume": 70,
    }
    assert weekly_bars([], AS_OF) == []


def test_support_clustering_and_exact_score() -> None:
    bars = bars_with_lows([95, 94, 91, 94, 95, 94, 91.1, 94, 95])
    zone = select_support(bars, find_swing_lows(bars), 2, 100, 0.5, 2)
    assert zone.price == pytest.approx(91.05)
    assert zone.touches == 2
    assert zone.strength == pytest.approx(0.4 * 2 / 5 + 0.3 * 6 / 8 + 0.3)
    for current, buffer in [(90, 0.5), (100, 100)]:
        with pytest.raises(MarketDataError, match="No support"):
            select_support(bars, find_swing_lows(bars), 2, current, buffer, 2)


@pytest.mark.parametrize("kind", ["nan", "range", "duplicate", "future", "missing"])
def test_invalid_history(kind: str) -> None:
    rows = historical_rows()[-3:]
    if kind == "nan":
        rows[0]["low"] = float("nan")
    elif kind == "range":
        rows[0]["high"] = 1
    elif kind == "duplicate":
        rows.append(rows[0])
    elif kind == "future":
        rows[0]["date"] = "2099-01-01"
    else:
        del rows[0]["volume"]
    with pytest.raises(MarketDataError) as exc:
        parse_bars(rows, AS_OF)
    assert exc.value.error_code == "INVALID_PRICE_DATA"


def test_settings_environment_and_validation(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("STOP_LOSS_SHORT_SWING_WINDOW", "3")
    assert StopLossSettings().short_swing_window == 3
    invalid_settings: list[dict[str, Any]] = [
        {"short_atr_period": 0},
        {"long_swing_window": 0},
        {"medium_atr_buffer": -1},
        {"short_atr_buffer": float("inf")},
    ]
    for kwargs in invalid_settings:
        with pytest.raises(ValidationError):
            StopLossSettings(**kwargs)


async def test_company_sdk_integration_preserves_partial_provider_failure() -> None:
    adapter = AsyncMock(spec=CompanyAdapter)

    async def profile(symbol: str) -> list[dict[str, Any]]:
        if symbol == "BAD":
            raise ProviderError("Unavailable", "test", "PROVIDER_TIMEOUT", retryable=True)
        return [{"symbol": symbol, "price": 150.0}]

    adapter.get_profile.side_effect = profile
    adapter.get_historical_pricing.return_value = historical_rows()
    sdk = CalculationService(CompanyService(adapter), StopLossSettings(), today=lambda: AS_OF)
    result = await sdk.get_stop_loss(["AAPL", "BAD"], ["SHORT"])
    assert result["summary"] == {"requested": 2, "successful": 1, "failed": 1}
    assert result["companies"][0]["currentPrice"] == 150.0
    assert result["errors"][0]["code"] == "PROVIDER_TIMEOUT"
    assert result["errors"][0]["retryable"] is True


def test_factory_wires_company_service_and_settings() -> None:
    factory = ServiceFactory(
        SDKSettings(
            provider="fmp",
            providers=MarketProviderSettings(fmp_api_key="test"),
        )
    )
    settings = StopLossSettings(short_atr_period=7)
    sdk = factory.create_calculation_service(settings)
    assert isinstance(sdk.company_service, CompanyService)
    assert sdk.settings is settings


async def test_all_item_failures_return_batch(company: AsyncMock) -> None:
    company.get_historical_pricing.return_value = {"priceData": []}
    result = await service(company).get_stop_loss(["AAPL", "IBM"], ["SHORT"])
    assert result["companies"] == []
    assert result["summary"] == {"requested": 2, "successful": 0, "failed": 2}
    assert [error["symbol"] for error in result["errors"]] == ["AAPL", "IBM"]
    assert all(error["code"] == "INSUFFICIENT_HISTORY" for error in result["errors"])


def test_swing_window_is_configurable() -> None:
    bars = bars_with_lows([8, 10, 9, 10, 8])
    assert find_swing_lows(bars, 1) == [SwingLow(2, 9)]
    assert find_swing_lows(bars, 2) == []


def test_clustering_does_not_chain_distant_levels() -> None:
    bars = bars_with_lows([95, 94, 90, 94, 95, 94, 90.75, 94, 95, 94, 91.5, 94, 95] + [95] * 4)
    zone = select_support(bars, find_swing_lows(bars), 2, 100, 0.5, 2)
    assert zone.touches == 2
    assert zone.price == 90.375


def test_support_tie_break_prefers_higher_price() -> None:
    bars = bars_with_lows([100] * 7)
    zone = select_support(bars, [SwingLow(2, 90), SwingLow(2, 95)], 2, 110, 0.5, 2)
    assert zone.price == 95


def test_weekly_partial_start_is_excluded() -> None:
    bars = bars_with_lows([10] * 20)
    weeks = weekly_bars(bars, date(2026, 1, 20))
    assert [bar.date for bar in weeks] == [date(2026, 1, 11), date(2026, 1, 18)]
