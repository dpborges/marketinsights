"""Concurrent analyst retrieval using an injected analyst adapter."""

import asyncio
from collections.abc import Awaitable, Callable
from math import isfinite
from typing import Any

from ..domain.exceptions import DataValidationError, SdkError
from ..interfaces.adapters import AnalystAdapter


class AnalystService:
    """Aggregate up to ten symbols, retaining successful results in input order."""

    def __init__(self, adapter: AnalystAdapter) -> None:
        self.adapter = adapter

    async def get_consensus(self, symbols: str | list[str]) -> dict[str, Any]:
        """Return flat consensus records with recommendations and per-symbol errors."""
        return await self._collect(symbols, self.adapter.get_analyst_consensus, "consensus")

    async def get_targets(self, symbols: str | list[str]) -> dict[str, Any]:
        """Return flat priceTargets records and per-symbol errors."""
        return await self._collect(symbols, self.adapter.get_analyst_targets, "priceTargets")

    def get_overall_recommendation(self, consensus: dict[str, Any]) -> str:
        """Classify a flat ratings record or an adapter's analystConsensus envelope.

        Weights run from strongBuy=5 to strongSell=1. Scores below 1.5 are
        strongSell; subsequent boundaries are 2.5, 3.5, and 4.5. Zero total
        ratings cannot produce a recommendation and raise DataValidationError.
        """
        if not isinstance(consensus, dict):
            raise DataValidationError("Analyst consensus must be an object.")
        ratings = consensus.get("analystConsensus", consensus)
        if not isinstance(ratings, dict):
            raise DataValidationError("Analyst ratings must be an object.")
        total = weighted = 0
        for rating, weight in (
            ("strongBuy", 5),
            ("buy", 4),
            ("hold", 3),
            ("sell", 2),
            ("strongSell", 1),
        ):
            count = ratings.get(rating)
            if (
                isinstance(count, bool)
                or not isinstance(count, (int, float))
                or not isfinite(count)
                or count < 0
                or int(count) != count
            ):
                raise DataValidationError(f"Invalid or missing analyst count: {rating}.")
            total += int(count)
            weighted += int(count) * weight
        if total == 0:
            raise DataValidationError("Cannot recommend without analyst ratings.")
        score = weighted / total
        for threshold, label in ((4.5, "strongBuy"), (3.5, "buy"), (2.5, "hold"), (1.5, "sell")):
            if score >= threshold:
                return label
        return "strongSell"

    async def _collect(
        self,
        symbols: str | list[str],
        fetch: Callable[[str], Awaitable[dict[str, Any]]],
        result_key: str,
    ) -> dict[str, Any]:
        requested = [symbols] if isinstance(symbols, str) else symbols
        if not isinstance(requested, list) or not requested:
            raise DataValidationError("Provide a stock symbol or a non-empty list of symbols.")
        if len(requested) > 10:
            raise DataValidationError("exceeded maximum of 10 symbols per request")
        if any(
            not isinstance(symbol, str)
            or not symbol.strip()
            or "," in symbol
            or any(char.isspace() for char in symbol.strip())
            for symbol in requested
        ):
            raise DataValidationError("Each symbol must be a non-empty single stock symbol.")
        normalized = [symbol.strip().upper() for symbol in requested]

        async def retrieve(symbol: str) -> tuple[dict[str, Any] | None, dict[str, Any] | None]:
            try:
                record = await fetch(symbol)
                key = "analystConsensus" if result_key == "consensus" else "priceTarget"
                row = {"symbol": symbol, **record[key]}
                if result_key == "consensus":
                    row["recommendation"] = self.get_overall_recommendation(record)
                return row, None
            except Exception as exc:
                return None, {
                    "symbol": symbol,
                    "code": type(exc).__name__ if isinstance(exc, SdkError) else "INTERNAL_ERROR",
                    "message": str(exc)
                    if isinstance(exc, SdkError)
                    else "Unable to retrieve analyst data.",
                }

        results = await asyncio.gather(*(retrieve(symbol) for symbol in normalized))
        return {
            result_key: [row for row, _ in results if row is not None],
            "errors": [error for _, error in results if error is not None],
        }
