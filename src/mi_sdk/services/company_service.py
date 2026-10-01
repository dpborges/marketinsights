"""Asynchronous company profiles, summaries, and historical daily prices."""

import calendar
import re
from datetime import date, timedelta
from typing import Any

from ..interfaces.adapters import CompanyAdapter
from ..providers.common.exceptions import ProviderError
from .batch_result_handler import collect_batch, normalize_symbols, translate_provider_error
from .exceptions import MarketDataError


class CompanyService:
    """Retrieve company batches and single-symbol historical daily prices."""

    def __init__(self, adapter: CompanyAdapter) -> None:
        self.adapter = adapter

    async def get_historical_pricing(
        self,
        symbol: str,
        from_date: str | None = None,
        to_date: str | None = None,
        lookback_period: str | None = None,
    ) -> dict[str, Any]:
        """Return priceData, its row count, and errors for one symbol.

        Supply either both inclusive calendar dates or a lookback period ending
        today. Day periods include today (1D is today alone); weeks, months, and
        years subtract calendar periods. Provider failures raise MarketDataError.
        """
        if not isinstance(symbol, str):
            raise MarketDataError("Provide one stock symbol as a string.", "BAD_REQUEST")
        symbol = normalize_symbols(symbol, maximum=1)[0]
        if lookback_period is not None:
            if from_date is not None or to_date is not None:
                raise MarketDataError(
                    "Provide either from_date and to_date or lookback_period.", "BAD_REQUEST"
                )
            today = date.today()
            to_date = today.isoformat()
            from_date = self.convert_period_code_to_from_date(lookback_period, as_of_date=today)
        else:
            for value in (from_date, to_date):
                if not isinstance(value, str) or not re.fullmatch(
                    r"[0-9]{4}-[0-9]{2}-[0-9]{2}", value
                ):
                    raise MarketDataError(
                        "Provide both from_date and to_date in YYYY-MM-DD format.", "BAD_REQUEST"
                    )
                try:
                    date.fromisoformat(value)
                except ValueError:
                    raise MarketDataError(
                        "from_date and to_date must be real calendar dates.", "BAD_REQUEST"
                    ) from None
            assert from_date is not None and to_date is not None
            if from_date > to_date:
                raise MarketDataError("from_date must be on or before to_date.", "BAD_REQUEST")

        try:
            payload = await self.adapter.get_historical_pricing(symbol, from_date, to_date)
        except ProviderError as exc:
            raise translate_provider_error(exc) from exc
        price_data = payload.get("data") if isinstance(payload, dict) else payload
        if not isinstance(price_data, list) or any(not isinstance(row, dict) for row in price_data):
            raise MarketDataError("Invalid historical pricing response.", "PROVIDER_ERROR")
        return {"requestedTradingDays": len(price_data), "priceData": price_data, "errors": []}

    @staticmethod
    def convert_period_code_to_from_date(
        period_code: str, *, as_of_date: date | None = None
    ) -> str:
        """Convert a supported calendar period, clamping month/year end dates."""
        supported = {
            "1D",
            "2D",
            "3D",
            "4D",
            "5D",
            "1W",
            "2W",
            "1M",
            "3M",
            "6M",
            "9M",
            "12M",
            "18M",
            "1Y",
            "2Y",
            "3Y",
            "4Y",
            "5Y",
        }
        if not isinstance(period_code, str) or period_code not in supported:
            raise MarketDataError("Unsupported lookback_period.", "BAD_REQUEST")
        today = as_of_date if as_of_date is not None else date.today()
        count = int(period_code[:-1])
        unit = period_code[-1]
        if unit == "D":
            return (today - timedelta(days=count - 1)).isoformat()
        if unit == "W":
            return (today - timedelta(weeks=count)).isoformat()
        months = count * 12 if unit == "Y" else count
        year, month_index = divmod(today.year * 12 + today.month - 1 - months, 12)
        month = month_index + 1
        day = min(today.day, calendar.monthrange(year, month)[1])
        return date(year, month, day).isoformat()

    async def get_profile(self, symbols: str | list[str] | None = None) -> dict[str, Any]:
        """Return full profiles, per-symbol errors, and counts for the entire batch."""
        return await collect_batch(symbols, self._profile, "companies")

    async def get_summary(self, symbols: str | list[str] | None = None) -> dict[str, Any]:
        """Return symbol, name, price, sector, and industry with batch diagnostics."""
        return await collect_batch(symbols, self._summary, "companies")

    async def _profile(self, symbol: str) -> dict[str, Any]:
        payload = await self.adapter.get_profile(symbol)
        if isinstance(payload, list) and not payload:
            raise MarketDataError(
                f"Symbol {symbol} was not found.",
                "SYMBOL_NOT_FOUND",
                retryable=False,
            )
        if (
            not isinstance(payload, list)
            or len(payload) != 1
            or not isinstance(payload[0], dict)
            or payload[0].get("symbol") != symbol
        ):
            raise MarketDataError(
                f"Invalid company profile response for {symbol}.",
                "PROVIDER_ERROR",
                retryable=False,
            )
        return dict(payload[0])

    async def _summary(self, symbol: str) -> dict[str, Any]:
        profile = await self._profile(symbol)
        return {
            "symbol": profile["symbol"],
            "name": profile.get("companyName"),
            "price": profile.get("price"),
            "sector": profile.get("sector"),
            "industry": profile.get("industry"),
        }
