"""Asynchronous company profiles and summaries through an injected adapter."""

from typing import Any

from ..interfaces.adapters import CompanyAdapter
from .batch_result_handler import collect_batch
from .exceptions import MarketDataError


class CompanyService:
    """Retrieve up to ten unique symbols, retaining successful records in input order."""

    def __init__(self, adapter: CompanyAdapter) -> None:
        self.adapter = adapter

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
