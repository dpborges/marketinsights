"""Provider adapter interfaces"""

from typing import Protocol

from ..domain.models.sector_performance import SectorPerformanceRequest, SectorPerformanceResponse


class SectorPerformanceAdapter(Protocol):
    """Protocol for sector performance data adapters"""

    async def fetch_sector_performance(
        self, request: SectorPerformanceRequest
    ) -> SectorPerformanceResponse:
        """Fetch sector performance data from the provider"""
        ...