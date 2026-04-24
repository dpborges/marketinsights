"""Service interfaces for the SDK"""

from typing import Protocol

from ..domain.models.sector_performance import SectorPerformanceRequest, SectorPerformanceResponse


class SectorPerformanceService(Protocol):
    """Protocol for sector performance services"""

    async def get_sector_performance(
        self, request: SectorPerformanceRequest
    ) -> SectorPerformanceResponse:
        """Get performance data for sector ETFs"""
        ...