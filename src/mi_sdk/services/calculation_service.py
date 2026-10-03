"""Asynchronous market data retrieval with synchronous stop-loss calculations."""

from collections.abc import Callable
from datetime import date
from math import isfinite
from typing import Any, Protocol

from ..config.stop_loss_settings import StopLossSettings
from ..domain.models.stop_loss import (
    CompanyStopLoss,
    HorizonStopLoss,
    InvestmentHorizon,
    StopLoss,
    Support,
    Volatility,
)
from .batch_result_handler import collect_batch, normalize_symbols
from .company_service import CompanyService
from .exceptions import MarketDataError
from .stop_loss_calculations import (
    calculate_atr,
    calculation_error,
    find_swing_lows,
    parse_bars,
    select_support,
    weekly_bars,
)


class CompanyPricing(Protocol):
    async def get_summary(self, symbols: str | list[str] | None = None) -> dict[str, Any]: ...

    async def get_historical_pricing(
        self,
        symbol: str,
        from_date: str | None = None,
        to_date: str | None = None,
        lookback_period: str | None = None,
    ) -> dict[str, Any]: ...


class CalculationService:
    """Calculate support-minus-ATR stops; each symbol succeeds atomically."""

    def __init__(
        self,
        company_service: CompanyPricing,
        settings: StopLossSettings | None = None,
        *,
        today: Callable[[], date] = date.today,
    ) -> None:
        self.company_service = company_service
        self.settings = settings if settings is not None else StopLossSettings()
        self._today = today

    async def _get_current_price(self, symbol: str) -> float:
        """Isolated temporary source, to be replaced by get_current_price later."""
        result = await self.company_service.get_summary([symbol])
        if result.get("errors"):
            error = result["errors"][0]
            raise MarketDataError(error["message"], error["code"], retryable=error["retryable"])
        companies = result.get("companies")
        if not isinstance(companies, list) or len(companies) != 1:
            raise calculation_error("Missing current price.", "INVALID_PRICE_DATA")
        company = companies[0]
        price = company.get("price") if isinstance(company, dict) else None
        if (
            not isinstance(company, dict)
            or company.get("symbol") != symbol
            or isinstance(price, bool)
            or not isinstance(price, (int, float))
            or not isfinite(price)
            or price <= 0
        ):
            raise calculation_error("Invalid current price.", "INVALID_PRICE_DATA")
        return float(price)

    async def get_stop_loss(
        self,
        symbols: list[str],
        horizons: list[str],
    ) -> dict[str, Any]:
        """Return companies, per-symbol errors and summary for up to 10 symbols.

        Horizons are case-insensitive and deduplicated in request order. One
        history fetch per symbol covers the longest requested calendar lookback.
        Output numbers retain precision for downstream risk/reward calculations.
        """
        requested = normalize_symbols(symbols)
        if not isinstance(horizons, list) or not horizons:
            raise calculation_error("Provide a non-empty horizons list.", "BAD_REQUEST")
        selected: list[InvestmentHorizon] = []
        for value in horizons:
            try:
                horizon = InvestmentHorizon(value.strip().upper())
            except (AttributeError, ValueError):
                raise calculation_error(
                    "Horizons must be SHORT, MEDIUM or LONG.", "BAD_REQUEST"
                ) from None
            if horizon not in selected:
                selected.append(horizon)
        as_of = self._today()
        periods = {
            InvestmentHorizon.SHORT: "6M",
            InvestmentHorizon.MEDIUM: "12M",
            InvestmentHorizon.LONG: "3Y",
        }
        starts = {
            h: date.fromisoformat(
                CompanyService.convert_period_code_to_from_date(periods[h], as_of_date=as_of)
            )
            for h in selected
        }
        start = min(starts.values())

        async def calculate(symbol: str) -> dict[str, Any]:
            current = await self._get_current_price(symbol)
            history = await self.company_service.get_historical_pricing(
                symbol,
                from_date=start.isoformat(),
                to_date=as_of.isoformat(),
            )
            bars = parse_bars(history.get("priceData"), as_of)
            results: dict[InvestmentHorizon, HorizonStopLoss] = {}
            for horizon in selected:
                horizon_bars = [bar for bar in bars if bar.date >= starts[horizon]]
                weekly = horizon == InvestmentHorizon.LONG
                if weekly:
                    horizon_bars = weekly_bars(horizon_bars, as_of)
                prefix = horizon.value.lower()
                period: int = getattr(self.settings, f"{prefix}_atr_period")
                buffer: float = getattr(self.settings, f"{prefix}_atr_buffer")
                window: int = getattr(self.settings, f"{prefix}_swing_window")
                if len(horizon_bars) < max(period + 1, 2 * window + 1):
                    raise calculation_error(
                        f"Insufficient history for {horizon.value}.", "INSUFFICIENT_HISTORY"
                    )
                atr = calculate_atr(horizon_bars, period)
                zone = select_support(
                    horizon_bars,
                    find_swing_lows(horizon_bars, window),
                    atr,
                    current,
                    buffer,
                    window,
                )
                stop = zone.price - atr * buffer
                results[horizon] = HorizonStopLoss(
                    stopLoss=StopLoss(price=stop, downsidePct=(current - stop) / current * 100),
                    support=Support(price=zone.price, strength=zone.strength, touches=zone.touches),
                    volatility=Volatility(
                        atr=atr,
                        atrPeriod=period,
                        atrTimeframe="WEEKLY" if weekly else "DAILY",
                        bufferMultiplier=buffer,
                    ),
                )
            return CompanyStopLoss(
                symbol=symbol, currentPrice=current, horizons=results
            ).model_dump(mode="json")

        return await collect_batch(requested, calculate, "companies")
