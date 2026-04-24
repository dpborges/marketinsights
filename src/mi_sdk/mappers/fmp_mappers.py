"""Mappers for FMP provider data"""

from typing import Any, Dict

from ..domain.models.sector_performance import SectorPerformance


class FMPQuoteMapper:
    """Mapper for FMP quote data to domain models"""

    def to_sector_performance(self, quote_data: Dict[str, Any], sector: str) -> SectorPerformance:
        """Map FMP quote data to SectorPerformance domain model"""

        return SectorPerformance(
            symbol=quote_data.get("symbol", ""),
            sector=sector,
            price=quote_data.get("price", 0.0),
            change=quote_data.get("change", 0.0),
            change_percent=quote_data.get("changesPercentage", 0.0),
            volume=quote_data.get("volume"),
            market_cap=quote_data.get("marketCap"),
            pe_ratio=quote_data.get("pe"),
            dividend_yield=quote_data.get("dividendYield"),
        )