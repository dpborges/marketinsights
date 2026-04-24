"""Tests for sector performance service"""

import pytest
from unittest.mock import AsyncMock, MagicMock

from mi_sdk.domain.models.sector_performance import (
    SectorPerformance,
    SectorPerformanceRequest,
    SectorPerformanceResponse,
)
from mi_sdk.interfaces.adapters import SectorPerformanceAdapter
from mi_sdk.services.sector_performance_service import SectorPerformanceServiceImpl


class TestSectorPerformanceService:
    """Test cases for sector performance service"""

    @pytest.fixture
    def mock_adapter(self) -> SectorPerformanceAdapter:
        """Mock adapter fixture"""
        return AsyncMock(spec=SectorPerformanceAdapter)

    @pytest.fixture
    def service(self, mock_adapter: SectorPerformanceAdapter) -> SectorPerformanceServiceImpl:
        """Service fixture"""
        return SectorPerformanceServiceImpl(mock_adapter)

    @pytest.fixture
    def sample_request(self) -> SectorPerformanceRequest:
        """Sample request fixture"""
        return SectorPerformanceRequest(symbols=["XLK", "XLF"])

    @pytest.fixture
    def sample_response(self) -> SectorPerformanceResponse:
        """Sample response fixture"""
        performances = [
            SectorPerformance(
                symbol="XLK",
                sector="Technology",
                price=150.0,
                change=2.5,
                change_percent=1.69,
            ),
            SectorPerformance(
                symbol="XLF",
                sector="Financial",
                price=40.0,
                change=-0.5,
                change_percent=-1.23,
            ),
        ]
        return SectorPerformanceResponse(performances=performances)

    @pytest.mark.asyncio
    async def test_get_sector_performance_success(
        self,
        service: SectorPerformanceServiceImpl,
        mock_adapter: AsyncMock,
        sample_request: SectorPerformanceRequest,
        sample_response: SectorPerformanceResponse,
    ) -> None:
        """Test successful sector performance retrieval"""
        # Arrange
        mock_adapter.fetch_sector_performance.return_value = sample_response

        # Act
        result = await service.get_sector_performance(sample_request)

        # Assert
        assert result == sample_response
        mock_adapter.fetch_sector_performance.assert_called_once_with(sample_request)

    @pytest.mark.asyncio
    async def test_get_sector_performance_adapter_error(
        self,
        service: SectorPerformanceServiceImpl,
        mock_adapter: AsyncMock,
        sample_request: SectorPerformanceRequest,
    ) -> None:
        """Test handling of adapter errors"""
        # Arrange
        mock_adapter.fetch_sector_performance.side_effect = Exception("Adapter error")

        # Act & Assert
        with pytest.raises(Exception, match="Adapter error"):
            await service.get_sector_performance(sample_request)