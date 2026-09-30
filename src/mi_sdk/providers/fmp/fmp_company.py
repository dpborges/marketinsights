"""Internal asynchronous adapter for FMP company data."""

import re
from datetime import date
from typing import Any

import httpx
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

from ..common.exceptions import ProviderError


class _CompanySettings(BaseSettings):
    api_key: str = Field(default="", validation_alias="MARKET_FMP_API_KEY", repr=False)
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


class FMPCompanyAdapter:
    """Retrieve raw company JSON without mapping provider fields."""

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
        return await self._request("profile", {"symbol": self._validate_symbol(symbol)})

    async def get_historical_pricing(
        self, symbol: str, from_date: str | None = None, to_date: str | None = None
    ) -> Any:
        """Return raw daily pricing; both dates are required in YYYY-MM-DD format.

        Omitted dates raise ProviderError, just like other invalid request inputs.
        """
        symbol = self._validate_symbol(symbol)
        for value in (from_date, to_date):
            if not isinstance(value, str) or not re.fullmatch(r"[0-9]{4}-[0-9]{2}-[0-9]{2}", value):
                raise ProviderError(
                    "Provide both from_date and to_date in YYYY-MM-DD format.",
                    provider="FMP",
                    error_code="BAD_REQUEST",
                )
            try:
                date.fromisoformat(value)
            except ValueError:
                raise ProviderError(
                    "from_date and to_date must be real calendar dates.",
                    provider="FMP",
                    error_code="BAD_REQUEST",
                ) from None
        assert from_date is not None and to_date is not None
        if from_date > to_date:
            raise ProviderError(
                "from_date must be on or before to_date.",
                provider="FMP",
                error_code="BAD_REQUEST",
            )
        return await self._request(
            "historical-price-eod/full",
            {"symbol": symbol, "from": from_date, "to": to_date},
        )

    @staticmethod
    def _validate_symbol(symbol: str) -> str:
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
        return symbol

    async def _request(self, endpoint: str, params: dict[str, str]) -> Any:
        """Apply shared transport and error handling to company endpoints."""
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(
                    f"{self.base_url}/{endpoint}", params={**params, "apikey": self._api_key}
                )
                response.raise_for_status()
        except httpx.HTTPStatusError as exc:
            status = exc.response.status_code
            code, message = {
                400: ("BAD_REQUEST", "Company request was rejected."),
                401: ("INVALID_API_KEY", "Company provider authentication failed."),
                402: ("FORBIDDEN_PLAN_LIMIT", "Company data access is not authorized."),
                403: ("FORBIDDEN_PLAN_LIMIT", "Company data access is not authorized."),
                404: ("SYMBOL_NOT_FOUND", "Company data was not found."),
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
