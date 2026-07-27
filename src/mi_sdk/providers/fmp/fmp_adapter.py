"""FMP v2 adapter for historical price data."""

from __future__ import annotations

# import asyncio
import logging
import os
from datetime import date, datetime, timedelta
from typing import Any, Dict, List, Optional, Sequence

import httpx
from dotenv import load_dotenv

from ...domain.exceptions import (
    AuthenticationError,
    AuthorizationError,
    ConfigurationError,
    DataValidationError,
    ProviderUnavailableError,
    RateLimitError,
    # SdkError,
    # SymbolNotFoundError,
)
# from ...domain.models.sector_performance import (
#    SectorPerformanceRequest,
#    SectorPerformanceResponse,
#)
# from ...mappers.fmp_mappers import FMPQuoteMapper

# logger = logging.getLogger(__name__)

DEFAULT_BASE_URL = "https://financialmodelingprep.com/stable"
DEFAULT_TIMEOUT = 30


class FMPAdapter:
    """FMP adapter for both historical pricing and sector performance."""

#    SECTOR_MAPPING = {
#        "XLK": "Technology",
#        "XLF": "Financial",
#        "XLV": "Health Care",
#        "XLY": "Consumer Discretionary",
#        "XLI": "Industrial",
#        "XLC": "Communication Services",
#        "XLE": "Energy",
#        "XLU": "Utilities",
#        "XLP": "Consumer Staples",
#        "XLB": "Materials",
#        "XLRE": "Real Estate",
#    }

    def __init__(self, api_key: Optional[str] = None, timeout: int = DEFAULT_TIMEOUT) -> None:
        load_dotenv()  # Load .env when CLI or local script runs.
        self.api_key = api_key or os.getenv("MARKET_FMP_API_KEY")
        self.timeout = timeout
        self.base_url = DEFAULT_BASE_URL.rstrip("/")
        # self.mapper = FMPQuoteMapper()

        if not self.api_key:
            raise ConfigurationError(
                "Missing FMP API key. Set MARKET_FMP_API_KEY in the environment or .env file."
            )

    def get_historical_prices(
        self,
        symbols: Sequence[str],
        as_of_date: str,
        lookback_periods: int,
    ) -> Dict[str, Any]:
        """Get historical pricing for sector ETFs, SPY, and any public stocks.

        Description: Returns historical pricing for all SPDR Sector ETFS, the SPY, and public stocks.
        The SPY will be used by the SDK layer (that calls this) to calculate relative strength for each of the sectors.
        The as_of_date is the date for which the current price is requested, and the lookback_periods is the number of trading days to look back for the historical price.
        For example, if as_of_date is 2026-07-16 and lookback_periods is 1, the historical price will be for 2026-07-15 (the previous day).
        For example, if as_of_date is 2026-07-16 and lookback_periods is 10, the historical price will be for 2026-07-01 (2 weeks prior).
        Inputs: list of stock symbols, as_of_date, lookback_periods.
        returns: json structure with historical pricing for SYMBOLS provided for the given date range.
        """

        symbol_list = self._normalize_symbols(symbols)
        validated_symbols = self._validate_symbols(symbol_list)
        as_of = self._parse_as_of_date(as_of_date)
        lookback = self._validate_lookback_periods(lookback_periods)

        prices: List[Dict[str, Any]] = []
        errors: List[Dict[str, Any]] = []

        for symbol in validated_symbols:
            try:
                historical_data = self._fetch_historical_series(symbol, as_of, lookback)
                current_price, lookback_price = self._extract_prices(
                    historical_data, as_of, lookback
                )
                prices.append(
                    {
                        "symbol": symbol,
                        "current": current_price,
                        "lookback": lookback_price,
                    }
                )
            except ProviderUnavailableError as error:
                if self._is_symbol_level_error(error):
                    error_code, error_message = self._classify_symbol_error(symbol, error)
                    errors.append(
                        {
                            "symbol": symbol,
                            "code": error_code,
                            "message": error_message,
                        }
                    )
                    continue
                raise

        response: Dict[str, Any] = {
            "provider": "FMP",
            "status": (
                "SUCCESS"
                if prices and not errors
                else "PARTIAL_SUCCESS"
                if prices and errors
                else "FAILED"
            ),
            "requestedSymbolCount": len(validated_symbols),
            "successfulSymbolCount": len(prices),
            "failedSymbolCount": len(errors),
            "prices": prices,
        }

        if errors:
            response["errors"] = errors

        return response

    def _is_symbol_level_error(self, error: ProviderUnavailableError) -> bool:
        message = str(error)
        return any(
            token in message
            for token in (
                "No historical pricing returned for symbol",
                "No trade data available on or before",
                "Insufficient historical data to compute",
                "FMP historical pricing response is missing adjusted close prices.",
            )
        )

    def _classify_symbol_error(
        self, symbol: str, error: ProviderUnavailableError
    ) -> tuple[str, str]:
        message = str(error)
        if "No historical pricing returned for symbol" in message:
            try:
                if self._symbol_exists(symbol):
                    return "NO_PRICE_DATA", message
                return "SYMBOL_NOT_FOUND", f"Symbol not found: {symbol}."
            except ProviderUnavailableError:
                return "HISTORICAL_PRICING_ERROR", message

        if "No trade data available on or before" in message:
            return "NO_PRICE_DATA", message

        if "Insufficient historical data to compute" in message:
            return "NO_PRICE_DATA", message

        if "missing adjusted close prices" in message:
            return "NO_PRICE_DATA", message

        return "HISTORICAL_PRICING_ERROR", message

    def _symbol_exists(self, symbol: str) -> bool:
        url = f"{self.base_url}/quote/{symbol}"
        params = {"apikey": self.api_key}

        try:
            with httpx.Client(timeout=self.timeout) as client:
                response = client.get(url, params=params)
                response.raise_for_status()
                payload = response.json()
        except httpx.HTTPStatusError as exc:
            status = exc.response.status_code if exc.response is not None else None
            if status == 401:
                raise AuthenticationError(
                    "FMP authentication failed. Check your API key."
                ) from exc
            if status in (402, 403):
                raise AuthorizationError(
                    "FMP authorization failed. Ensure the API key has access."
                ) from exc
            if status == 429:
                raise RateLimitError(
                    "FMP rate limit exceeded. Please retry after a short delay."
                ) from exc
            raise ProviderUnavailableError(
                f"Failed to fetch quote from FMP: {exc}"
            ) from exc
        except httpx.HTTPError as exc:
            raise ProviderUnavailableError(
                f"Failed to connect to FMP: {exc}"
            ) from exc

        if not isinstance(payload, list):
            raise ProviderUnavailableError(
                "Unexpected response format from FMP quote endpoint."
            )

        return bool(payload and payload[0].get("symbol") == symbol)

#    async def fetch_sector_performance(
#        self, request: SectorPerformanceRequest
#    ) -> SectorPerformanceResponse:
#        """Fetch sector performance data from FMP."""
#
#        invalid_symbols = [s for s in request.symbols if s not in self.SECTOR_MAPPING]
#        if invalid_symbols:
#            raise SymbolNotFoundError(
#                f"Invalid sector ETF symbols: {invalid_symbols}. "
#                f"Supported symbols: {list(self.SECTOR_MAPPING.keys())}"
#            )
#
#        try:
#            quotes = await self._fetch_quotes_batch(request.symbols)
#            performances = []
#            for quote_data in quotes:
#                symbol = quote_data.get("symbol", "")
#                sector = self.SECTOR_MAPPING.get(symbol, "Unknown")
#                performance = self.mapper.to_sector_performance(quote_data, sector)
#                performances.append(performance)
#
#            return SectorPerformanceResponse(performances=performances)
#        except httpx.HTTPError as error:
#            raise ProviderUnavailableError(
#                f"Failed to fetch data from FMP: {str(error)}"
#            ) from error
#        except SdkError:
#            raise
#        except Exception as error:
#            raise ProviderUnavailableError(
#                f"Unexpected error: {str(error)}"
#            ) from error
#
#    async def _fetch_quotes_batch(self, symbols: List[str]) -> List[Dict[str, Any]]:
#        async with httpx.AsyncClient(timeout=self.timeout) as client:
#            symbols_str = ",".join(symbols)
#            url = f"{self.base_url.rstrip('/')}/batch-quote"
#            params = {"symbols": symbols_str, "apikey": self.api_key}
#
#            try:
#                response = await client.get(url, params=params)
#                response.raise_for_status()
#            except httpx.HTTPStatusError as exc:
#                status = exc.response.status_code if exc.response is not None else None
#                if status == 401:
#                    raise AuthenticationError(
#                        "FMP authentication failed. Check your API key."
#                    ) from exc
#                if status in (402, 403):
#                    return await self._fetch_quotes_individually(client, symbols)
#                if status == 429:
#                    raise RateLimitError(
#                        "FMP rate limit exceeded. Please retry after a short delay."
#                    ) from exc
#                raise ProviderUnavailableError(
#                    f"Failed to fetch data from FMP: {str(exc)}"
#                ) from exc
#
#            data = response.json()
#            if not isinstance(data, list):
#                raise ProviderUnavailableError("Unexpected response format from FMP")
#            return data
#
#    async def _fetch_quotes_individually(
#        self, client: httpx.AsyncClient, symbols: List[str]
#    ) -> List[Dict[str, Any]]:
#        url = f"{self.base_url.rstrip('/')}/quote"
#        tasks = [self._fetch_single_quote(client, url, symbol) for symbol in symbols]
#        return await asyncio.gather(*tasks)
#
#    async def _fetch_single_quote(
#        self, client: httpx.AsyncClient, url: str, symbol: str
#    ) -> Dict[str, Any]:
#        params = {"symbol": symbol, "apikey": self.api_key}
#
#        try:
#            response = await client.get(url, params=params)
#            response.raise_for_status()
#        except httpx.HTTPStatusError as exc:
#            status = exc.response.status_code if exc.response is not None else None
#            if status == 401:
#                raise AuthenticationError(
#                    "FMP authentication failed. Check your API key."
#                ) from exc
#            if status in (402, 403):
#                raise AuthorizationError(
#                    "FMP authorization failed. Ensure the API key has access to this endpoint."
#                ) from exc
#            if status == 429:
#                raise RateLimitError(
#                    "FMP rate limit exceeded. Please retry after a short delay."
#                ) from exc
#            raise ProviderUnavailableError(
#                f"Failed to fetch data from FMP quote: {str(exc)}"
#            ) from exc
#
#        data = response.json()
#        if not isinstance(data, list):
#            raise ProviderUnavailableError("Unexpected response format from FMP quote")
#        if len(data) == 0:
#            raise ProviderUnavailableError(f"No quote data returned for symbol: {symbol}")
#        return data[0]

    def _normalize_symbols(self, symbols: Sequence[str]) -> List[str]:
        if not symbols:
            raise DataValidationError("At least one symbol is required.")

        normalized = []
        for symbol in symbols:
            if not isinstance(symbol, str) or not symbol.strip():
                raise DataValidationError("Symbols must be non-empty strings.")
            normalized.append(symbol.strip().upper())

        return normalized

    def _validate_symbols(self, symbols: List[str]) -> List[str]:
        # this is place holder if I want to add logic to validate symbols list here
        # for now, just return the symbols as is
        return symbols

    def _parse_as_of_date(self, as_of_date: str) -> date:
        try:
            parsed = datetime.fromisoformat(as_of_date).date()
        except ValueError as exc:
            raise DataValidationError(
                f"Invalid as_of_date '{as_of_date}'. Use YYYY-MM-DD format."
            ) from exc
        return parsed

    def _validate_lookback_periods(self, lookback_periods: int) -> int:
        if not isinstance(lookback_periods, int) or lookback_periods < 1:
            raise DataValidationError(
                "lookback_periods must be a whole number greater than zero."
            )
        return lookback_periods

    def _fetch_historical_series(
        self, symbol: str, as_of: date, lookback_periods: int
    ) -> List[Dict[str, Any]]:
        date_span = timedelta(days=lookback_periods * 5 + 14)
        from_date = as_of - date_span
        url = f"{self.base_url}/historical-price-eod/dividend-adjusted"
        params = {
            "symbol": symbol,
            "from": from_date.isoformat(),
            "to": as_of.isoformat(),
            "apikey": self.api_key,
        }

        try:
            with httpx.Client(timeout=self.timeout) as client:
                response = client.get(url, params=params)
                response.raise_for_status()
                payload = response.json()
        except httpx.HTTPStatusError as exc:
            status = exc.response.status_code if exc.response is not None else None
            if status == 401:
                raise AuthenticationError(
                    "FMP authentication failed. Check your API key."
                ) from exc
            if status in (402, 403):
                raise AuthorizationError(
                    "FMP authorization failed. Ensure the API key has access."
                ) from exc
            if status == 429:
                raise RateLimitError(
                    "FMP rate limit exceeded. Please retry after a short delay."
                ) from exc
            raise ProviderUnavailableError(
                f"Failed to fetch historical pricing from FMP: {exc}"
            ) from exc
        except httpx.HTTPError as exc:
            raise ProviderUnavailableError(
                f"Failed to connect to FMP: {exc}"
            ) from exc

        if not isinstance(payload, list):
            raise ProviderUnavailableError(
                "Unexpected response format from FMP historical pricing endpoint."
            )

        historical = payload
        if len(historical) == 0:
            raise ProviderUnavailableError(
                f"No historical pricing returned for symbol: {symbol}."
            )

        return historical

    def _extract_prices(
        self, historical: List[Dict[str, Any]], as_of: date, lookback_periods: int
    ) -> tuple[Dict[str, Any], Dict[str, Any]]:
        normalized = [
            {
                "date": datetime.fromisoformat(item["date"]).date(),
                "adjustedClose": float(item.get("adjClose", item.get("close", 0.0))) if item.get("adjClose", item.get("close")) is not None else None,
            }
            for item in historical
            if item.get("date")
        ]

        normalized.sort(key=lambda item: item["date"])
        filtered = [item for item in normalized if item["date"] <= as_of]
        if not filtered:
            raise ProviderUnavailableError(
                f"No trade data available on or before {as_of.isoformat()}."
            )

        current_record = filtered[-1]
        lookback_index = len(filtered) - 1 - lookback_periods
        if lookback_index < 0:
            raise ProviderUnavailableError(
                f"Insufficient historical data to compute {lookback_periods} lookback periods."
            )

        lookback_record = filtered[lookback_index]

        if current_record["adjustedClose"] is None or lookback_record["adjustedClose"] is None:
            raise ProviderUnavailableError(
                "FMP historical pricing response is missing adjusted close prices."
            )

        return (
            {
                "date": current_record["date"].isoformat(),
                "adjustedClose": current_record["adjustedClose"],
            },
            {
                "date": lookback_record["date"].isoformat(),
                "adjustedClose": lookback_record["adjustedClose"],
            },
        )
