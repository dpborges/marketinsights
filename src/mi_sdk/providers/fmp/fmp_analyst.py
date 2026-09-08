"""Async analyst adapter. Run from the repository root in Git Bash:

    PYTHONPATH=src ./.venv/Scripts/python.exe -m mi_sdk.providers.fmp.fmp_analyst_run
    PYTHONPATH=src ./.venv/Scripts/python.exe -m mi_sdk.providers.fmp.fmp_analyst_run get_analyst_consensus NVDA
    PYTHONPATH=src ./.venv/Scripts/python.exe -m mi_sdk.providers.fmp.fmp_analyst_run get_analyst_targets NVDA

Loads MARKET_FMP_API_KEY from the environment or .env. Returns JSON-compatible
objects for one symbol per request. No SDK service contains FMP logic.
"""

from math import isfinite
from typing import Any

import httpx
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

from ...domain.exceptions import (
    AuthenticationError,
    AuthorizationError,
    ConfigurationError,
    DataValidationError,
    ProviderUnavailableError,
    RateLimitError,
)


class _AnalystSettings(BaseSettings):
    """Internal configuration; do not print the settings or request URLs."""

    api_key: str = Field(default="", validation_alias="MARKET_FMP_API_KEY", repr=False)
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


class FMPAnalystAdapter:
    """Retrieve analyst data and translate it into provider-neutral dictionaries."""

    def __init__(self, api_key: str | None = None, timeout: float = 30.0) -> None:
        self._api_key = api_key if api_key is not None else _AnalystSettings().api_key
        if not self._api_key.strip():
            raise ConfigurationError("Set MARKET_FMP_API_KEY in the environment or .env file.")
        self.timeout = timeout
        self.base_url = "https://financialmodelingprep.com/stable"

    async def get_analyst_consensus(self, symbol: str) -> dict[str, Any]:
        """Get the number of analysts in each recommendation category.

        Input: one stock symbol, e.g. "NVDA".
        Returns: JSON-compatible object {symbol, analystConsensus}, containing
        strongBuy, buy, hold, sell, and strongSell counts. The symbol is trimmed
        and uppercased. Lists and multiple-symbol strings are rejected.
        """
        fields = {name: name for name in ("strongBuy", "buy", "hold", "sell", "strongSell")}
        return await self._get_record(symbol, "grades-consensus", "analystConsensus", fields)

    async def get_analyst_targets(self, symbol: str) -> dict[str, Any]:
        """Get the high, low, median, and consensus analyst price targets.

        Input: one stock symbol, e.g. "NVDA".
        Returns: JSON-compatible object {symbol, priceTarget}, with high, low,
        median, and consensus values. Missing or invalid data raises an SDK error
        rather than substituting zero for unavailable targets.
        """
        fields = {
            "high": "targetHigh",
            "low": "targetLow",
            "median": "targetMedian",
            "consensus": "targetConsensus",
        }
        return await self._get_record(symbol, "price-target-consensus", "priceTarget", fields)

    async def _get_record(
        self, symbol: str, endpoint: str, key: str, fields: dict[str, str]
    ) -> dict[str, Any]:
        if not isinstance(symbol, str) or not symbol.strip():
            raise DataValidationError("Provide one non-empty stock symbol as a string.")
        symbol = symbol.strip().upper()
        if "," in symbol or any(character.isspace() for character in symbol):
            raise DataValidationError("Provide only one stock symbol, not multiple symbols.")
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            payload = await self._request(client, endpoint, symbol)
        if not isinstance(payload, list) or any(not isinstance(row, dict) for row in payload):
            raise DataValidationError(f"Unexpected analyst response for {symbol}.")
        matches = [row for row in payload if row.get("symbol") == symbol]
        if not matches:
            raise DataValidationError(f"No analyst data available for {symbol}.")
        if len(matches) != 1:
            raise DataValidationError(f"Ambiguous analyst response for {symbol}.")
        values = {}
        for output, source in fields.items():
            value = matches[0].get(source)
            if (
                isinstance(value, bool)
                or not isinstance(value, (int, float))
                or not isfinite(value)
                or value < 0
                or (key == "analystConsensus" and int(value) != value)
            ):
                raise DataValidationError(f"Invalid or missing {output} for {symbol}.")
            values[output] = int(value) if key == "analystConsensus" else float(value)
        return {"symbol": symbol, key: values}

    async def _request(self, client: httpx.AsyncClient, endpoint: str, symbol: str) -> Any:
        try:
            response = await client.get(
                f"{self.base_url}/{endpoint}", params={"symbol": symbol, "apikey": self._api_key}
            )
            response.raise_for_status()
        except httpx.HTTPStatusError as exc:
            status = exc.response.status_code
            if status == 401:
                raise AuthenticationError("Analyst provider authentication failed.") from None
            if status in (402, 403):
                raise AuthorizationError("Analyst data access is not authorized.") from None
            if status == 429:
                raise RateLimitError("Analyst provider rate limit exceeded.") from None
            raise ProviderUnavailableError(f"Analyst request failed (HTTP {status}).") from None
        except httpx.HTTPError:
            raise ProviderUnavailableError("Unable to connect to the analyst provider.") from None
        try:
            return response.json()
        except ValueError:
            raise DataValidationError("Analyst provider returned invalid JSON.") from None
