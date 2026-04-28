"""Tests for FMP adapter"""

import pytest
from unittest.mock import AsyncMock, Mock, patch

import httpx

from mi_sdk.domain.exceptions import ProviderUnavailableError, SymbolNotFoundError
from mi_sdk.providers.fmp.fmp_adapter import FMPAdapter


class TestFMPAdapter:
    """Test cases for FMP adapter"""

    @pytest.fixture
    def adapter(self) -> FMPAdapter:
        """Adapter fixture"""
        return FMPAdapter(api_key="test_key", timeout=30)

    @pytest.fixture
    def valid_request(self) -> dict:
        """Valid request fixture"""
        from mi_sdk.domain.models.sector_performance import SectorPerformanceRequest
        return SectorPerformanceRequest(symbols=["XLK", "XLF"])

    @pytest.fixture
    def fmp_quote_response(self) -> list[dict]:
        """Sample FMP quote response"""
        return [
            {
                "symbol": "XLK",
                "price": 150.0,
                "change": 2.5,
                "changesPercentage": 1.69,
                "volume": 1000000,
                "marketCap": 50000000000,
                "pe": 25.0,
                "dividendYield": 1.2,
            },
            {
                "symbol": "XLF",
                "price": 40.0,
                "change": -0.5,
                "changesPercentage": -1.23,
                "volume": 500000,
                "marketCap": 25000000000,
                "pe": 15.0,
                "dividendYield": 2.5,
            },
        ]

    def test_sector_mapping(self, adapter: FMPAdapter) -> None:
        """Test sector mapping is correct"""
        assert adapter.SECTOR_MAPPING["XLK"] == "Technology"
        assert adapter.SECTOR_MAPPING["XLF"] == "Financial"
        assert len(adapter.SECTOR_MAPPING) == 11  # All SPDR sectors

    def test_invalid_symbols(self, adapter: FMPAdapter) -> None:
        """Test validation of invalid symbols"""
        from mi_sdk.domain.models.sector_performance import SectorPerformanceRequest

        request = SectorPerformanceRequest(symbols=["INVALID", "XLK"])

        with pytest.raises(SymbolNotFoundError, match="Invalid sector ETF symbols"):
            # This will fail at validation, before making HTTP call
            import asyncio
            asyncio.run(adapter.fetch_sector_performance(request))

    @pytest.mark.asyncio
    async def test_fetch_sector_performance_success(
        self, adapter: FMPAdapter, valid_request, fmp_quote_response
    ) -> None:
        """Test successful data fetching"""
        with patch("mi_sdk.providers.fmp.fmp_adapter.httpx.AsyncClient") as mock_client_class:
            # Setup mock response - use Mock for synchronous json() method
            mock_response = Mock()
            mock_response.json.return_value = fmp_quote_response
            mock_response.raise_for_status = Mock()

            mock_client = AsyncMock()
            mock_client.get = AsyncMock(return_value=mock_response)
            mock_client.__aenter__.return_value = mock_client
            mock_client.__aexit__.return_value = None
            mock_client_class.return_value = mock_client

            # Act
            result = await adapter.fetch_sector_performance(valid_request)

            # Assert
            assert len(result.performances) == 2
            assert result.performances[0].symbol == "XLK"
            assert result.performances[0].sector == "Technology"
            assert result.performances[0].price == 150.0
            assert result.performances[1].symbol == "XLF"
            assert result.performances[1].sector == "Financial"

    @pytest.mark.asyncio
    async def test_fetch_sector_performance_http_error(
        self, adapter: FMPAdapter, valid_request
    ) -> None:
        """Test handling of HTTP errors"""
        with patch("mi_sdk.providers.fmp.fmp_adapter.httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.get.side_effect = httpx.HTTPError("HTTP Error")
            mock_client_class.return_value.__aenter__.return_value = mock_client

            with pytest.raises(ProviderUnavailableError, match="Failed to fetch data from FMP"):
                await adapter.fetch_sector_performance(valid_request)

    @pytest.mark.asyncio
    async def test_fetch_sector_performance_invalid_response(
        self, adapter: FMPAdapter, valid_request
    ) -> None:
        """Test handling of invalid response format"""
        with patch("mi_sdk.providers.fmp.fmp_adapter.httpx.AsyncClient") as mock_client_class:
            mock_response = Mock()
            mock_response.json.return_value = {"error": "Invalid format"}  # Not a list
            mock_response.raise_for_status = Mock()

            mock_client = AsyncMock()
            mock_client.get = AsyncMock(return_value=mock_response)
            mock_client.__aenter__.return_value = mock_client
            mock_client.__aexit__.return_value = None
            mock_client_class.return_value = mock_client

            with pytest.raises(ProviderUnavailableError, match="Unexpected response format"):
                await adapter.fetch_sector_performance(valid_request)