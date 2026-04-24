"""Sector performance service implementation"""

from ..domain.models.sector_performance import SectorPerformanceRequest, SectorPerformanceResponse
from ..interfaces.adapters import SectorPerformanceAdapter


class SectorPerformanceServiceImpl:
    """Implementation of sector performance service"""

    def __init__(self, adapter: SectorPerformanceAdapter) -> None:
        self.adapter = adapter

    async def get_sector_performance(
        self, request: SectorPerformanceRequest
    ) -> SectorPerformanceResponse:
        """Get performance data for sector ETFs"""
        return await self.adapter.fetch_sector_performance(request)