"""Internal asynchronous adapter for FMP company profiles."""

from typing import Any

import httpx
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

from ..common.exceptions import ProviderError


class _CompanySettings(BaseSettings):
    api_key: str = Field(default="", validation_alias="MARKET_FMP_API_KEY", repr=False)
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


class FMPCompanyAdapter:
    """Retrieve raw company profile JSON without mapping provider fields."""

    def __init__(self, api_key: str | None = None, timeout: float = 30.0) -> None:
        self._api_key = api_key if api_key is not None else _CompanySettings().api_key
        if not self._api_key.strip():
            raise ProviderError(
                "Set MARKET_FMP_API_KEY in the environment or .env file.",
                provider="FMP",
                error_code="CONFIGURATION_ERROR",
            )
        self.timeout = timeout
        self.base_url = "https://financialmodelingprep.com/stable"

    async def get_profile(self, symbol: str) -> Any:
        """Return the provider JSON unchanged for one stock symbol, e.g. AAPL."""
        # This service return a full company profile
        if not isinstance(symbol, str) or not symbol.strip():
            raise ProviderError(
                "Provide one non-empty stock symbol as a string.",
                provider="FMP",
                error_code="BAD_REQUEST",
                retryable=False,
            )
        symbol = symbol.strip().upper()
        if "," in symbol or any(character.isspace() for character in symbol):
            raise ProviderError(
                "Provide only one stock symbol, not multiple symbols.",
                provider="FMP",
                error_code="BAD_REQUEST",
                retryable=False,
            )
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(
                    f"{self.base_url}/profile", params={"symbol": symbol, "apikey": self._api_key}
                )
                response.raise_for_status()
        except httpx.HTTPStatusError as exc:
            status = exc.response.status_code
            code, message = {
                400: ("BAD_REQUEST", "Company request was rejected."),
                401: ("INVALID_API_KEY", "Company provider authentication failed."),
                402: ("FORBIDDEN_PLAN_LIMIT", "Company data access is not authorized."),
                403: ("FORBIDDEN_PLAN_LIMIT", "Company data access is not authorized."),
                404: ("SYMBOL_NOT_FOUND", "Company profile was not found."),
                429: ("RATE_LIMIT_EXCEEDED", "Company provider rate limit exceeded."),
            }.get(
                status,
                (
                    "PROVIDER_UNAVAILABLE" if status >= 500 else "PROVIDER_ERROR",
                    f"Company request failed (HTTP {status}).",
                ),
            )
            raise ProviderError(
                message=message,
                provider="FMP",
                error_code=code,
                status_code=status,
                retryable=status == 429 or status >= 500,
            ) from None
        except httpx.TimeoutException:
            raise ProviderError(
                message="Company provider request timed out.",
                provider="FMP",
                error_code="PROVIDER_TIMEOUT",
                retryable=True,
            ) from None
        except httpx.HTTPError:
            raise ProviderError(
                message="Unable to connect to the company provider.",
                provider="FMP",
                error_code="PROVIDER_UNAVAILABLE",
                retryable=True,
            ) from None
        try:
            payload = response.json()
        except ValueError:
            raise ProviderError(
                message="Company provider returned invalid JSON.",
                provider="FMP",
                error_code="PROVIDER_ERROR",
                status_code=response.status_code,
            ) from None
        if isinstance(payload, dict) and any(
            key in payload for key in ("Error Message", "error", "Error")
        ):
            raise ProviderError(
                message="Company provider returned an error response.",
                provider="FMP",
                error_code="PROVIDER_ERROR",
                status_code=response.status_code,
            )
        return payload
