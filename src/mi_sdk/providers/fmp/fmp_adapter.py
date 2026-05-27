"""FMP (Financial Modeling Prep) provider adapter"""

import asyncio
import logging
from typing import Any, Dict, List, Optional

import httpx
from pydantic import BaseModel

from ...domain.exceptions import (
    AuthorizationError,
    AuthenticationError,
    ProviderUnavailableError,
    RateLimitError,
    SdkError,
    SymbolNotFoundError,
)
from ...domain.models.sector_performance import (
    SectorPerformance,
    SectorPerformanceRequest,
    SectorPerformanceResponse,
)
from ...mappers.fmp_mappers import FMPQuoteMapper

logger = logging.getLogger(__name__)


class FMPQuoteResponse(BaseModel):
    """FMP quote response model"""

    symbol: str
    price: float
    change: float
    changesPercentage: float
    volume: Optional[int] = None
    marketCap: Optional[float] = None
    pe: Optional[float] = None
    dividendYield: Optional[float] = None


class FMPAdapter:
    """FMP adapter for sector performance data"""

    # Mapping of ETF symbols to sectors
    SECTOR_MAPPING = {
        "XLK": "Technology",
        "XLF": "Financial",
        "XLV": "Health Care",
        "XLY": "Consumer Discretionary",
        "XLI": "Industrial",
        "XLC": "Communication Services",
        "XLE": "Energy",
        "XLU": "Utilities",
        "XLP": "Consumer Staples",
        "XLB": "Materials",
        "XLRE": "Real Estate",
    }

    def __init__(self, api_key: str, timeout: int = 30) -> None:
        self.api_key = api_key
        self.timeout = timeout
        self.base_url = "https://financialmodelingprep.com/stable/".rstrip("/")
        self.mapper = FMPQuoteMapper()

    async def fetch_sector_performance(
        self, request: SectorPerformanceRequest
    ) -> SectorPerformanceResponse:
        """Fetch sector performance data from FMP"""

        # Validate symbols are known sector ETFs
        invalid_symbols = [s for s in request.symbols if s not in self.SECTOR_MAPPING]
        if invalid_symbols:
            raise SymbolNotFoundError(
                f"Invalid sector ETF symbols: {invalid_symbols}. "
                f"Supported symbols: {list(self.SECTOR_MAPPING.keys())}"
            )

        try:
            # Fetch quotes for all symbols concurrently
            quotes = await self._fetch_quotes_batch(request.symbols)

            # Map to domain models
            performances = []
            for quote_data in quotes:
                symbol = quote_data.get("symbol", "")
                sector = self.SECTOR_MAPPING.get(symbol, "Unknown")
                performance = self.mapper.to_sector_performance(quote_data, sector)
                performances.append(performance)

            return SectorPerformanceResponse(performances=performances)

        except httpx.HTTPError as e:
            logger.error(f"FMP API error: {e}")
            raise ProviderUnavailableError(f"Failed to fetch data from FMP: {str(e)}")
        except SdkError:
            raise
        except Exception as e:
            logger.error(f"Unexpected error in FMP adapter: {e}")
            raise ProviderUnavailableError(f"Unexpected error: {str(e)}")

    async def _fetch_quotes_batch(self, symbols: List[str]) -> List[Dict[str, Any]]:
        """Fetch quotes for multiple symbols"""

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            # Use the current stable FMP batch quote endpoint instead of legacy /quote
            symbols_str = ",".join(symbols)
            url = f"{self.base_url.rstrip('/')}/batch-quote"
            params = {"symbols": symbols_str, "apikey": self.api_key}

            try:
                response = await client.get(url, params=params)
                response.raise_for_status()
            except httpx.HTTPStatusError as exc:
                status = exc.response.status_code if exc.response is not None else None
                if status == 401:
                    raise AuthenticationError(
                        "FMP authentication failed. Check your API key."
                    ) from exc
                if status in (402, 403):
                    logger.warning(
                        "FMP batch-quote endpoint restricted; falling back to individual quote requests"
                    )
                    return await self._fetch_quotes_individually(client, symbols)
                if status == 429:
                    raise RateLimitError(
                        "FMP rate limit exceeded. Please retry after a short delay."
                    ) from exc
                raise ProviderUnavailableError(
                    f"Failed to fetch data from FMP: {str(exc)}"
                ) from exc

            data = response.json()

            # FMP returns a list of quotes
            if not isinstance(data, list):
                raise ProviderUnavailableError("Unexpected response format from FMP")

            return data

    async def _fetch_quotes_individually(
        self, client: httpx.AsyncClient, symbols: List[str]
    ) -> List[Dict[str, Any]]:
        """Fetch quotes one symbol at a time when batch quotes are restricted."""
        url = f"{self.base_url.rstrip('/')}/quote"
        tasks = [self._fetch_single_quote(client, url, symbol) for symbol in symbols]
        return await asyncio.gather(*tasks)

    async def _fetch_single_quote(
        self, client: httpx.AsyncClient, url: str, symbol: str
    ) -> Dict[str, Any]:
        params = {"symbol": symbol, "apikey": self.api_key}

        try:
            response = await client.get(url, params=params)
            response.raise_for_status()
        except httpx.HTTPStatusError as exc:
            status = exc.response.status_code if exc.response is not None else None
            if status == 401:
                raise AuthenticationError(
                    "FMP authentication failed. Check your API key."
                ) from exc
            if status in (402, 403):
                raise AuthorizationError(
                    "FMP authorization failed. Ensure your key has access to this endpoint."
                ) from exc
            if status == 429:
                raise RateLimitError(
                    "FMP rate limit exceeded. Please retry after a short delay."
                ) from exc
            raise ProviderUnavailableError(
                f"Failed to fetch data from FMP quote: {str(exc)}"
            ) from exc

        data = response.json()
        if not isinstance(data, list):
            raise ProviderUnavailableError("Unexpected response format from FMP quote")
        if len(data) == 0:
            raise ProviderUnavailableError(f"No quote data returned for symbol: {symbol}")
        return data[0]
