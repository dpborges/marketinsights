"""Internal asynchronous adapter for FMP company profiles."""

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


class _CompanySettings(BaseSettings):
    api_key: str = Field(default="", validation_alias="MARKET_FMP_API_KEY", repr=False)
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


class FMPCompanyAdapter:
    """Retrieve raw company profile JSON without mapping provider fields."""

    def __init__(self, api_key: str | None = None, timeout: float = 30.0) -> None:
        self._api_key = api_key if api_key is not None else _CompanySettings().api_key
        if not self._api_key.strip():
            raise ConfigurationError("Set MARKET_FMP_API_KEY in the environment or .env file.")
        self.timeout = timeout
        self.base_url = "https://financialmodelingprep.com/stable"

    async def get_profile(self, symbol: str) -> Any:
        """Return the provider JSON unchanged for one stock symbol, e.g. AAPL."""
        # This service return a full company profile
        if not isinstance(symbol, str) or not symbol.strip():
            raise DataValidationError("Provide one non-empty stock symbol as a string.")
        symbol = symbol.strip().upper()
        if "," in symbol or any(character.isspace() for character in symbol):
            raise DataValidationError("Provide only one stock symbol, not multiple symbols.")
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(
                    f"{self.base_url}/profile", params={"symbol": symbol, "apikey": self._api_key}
                )
                response.raise_for_status()
        except httpx.HTTPStatusError as exc:
            status = exc.response.status_code
            if status == 401:
                raise AuthenticationError("Company provider authentication failed.") from None
            if status in (402, 403):
                raise AuthorizationError("Company data access is not authorized.") from None
            if status == 429:
                raise RateLimitError("Company provider rate limit exceeded.") from None
            raise ProviderUnavailableError(f"Company request failed (HTTP {status}).") from None
        except httpx.HTTPError:
            raise ProviderUnavailableError("Unable to connect to the company provider.") from None
        try:
            return response.json()
        except ValueError:
            raise DataValidationError("Company provider returned invalid JSON.") from None
