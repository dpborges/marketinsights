"""Provider adapter interfaces"""

from collections.abc import Sequence
from typing import Any, Protocol

from ..domain.models.sector_performance import SectorPerformanceRequest, SectorPerformanceResponse


class SectorPerformanceAdapter(Protocol):
    """Protocol for sector performance data adapters"""

    async def fetch_sector_performance(
        self, request: SectorPerformanceRequest
    ) -> SectorPerformanceResponse:
        """Fetch sector performance data from the provider"""
        ...

class HistoricalPricingAdapter(Protocol):
    """Async historical pricing boundary used by sector summaries."""

    async def get_historical_prices(
        self, symbols: Sequence[str], as_of_date: str, lookback_periods: int
    ) -> dict[str, Any]:
        """Return adjusted current and lookback prices plus per-symbol errors."""
        ...
