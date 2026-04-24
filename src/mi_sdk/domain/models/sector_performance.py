"""Domain models for sector performance"""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class SectorPerformance(BaseModel):
    """Represents performance data for a sector ETF"""

    symbol: str = Field(..., description="ETF symbol (e.g., XLK)")
    sector: str = Field(..., description="Sector name (e.g., Technology)")
    price: float = Field(..., description="Current price")
    change: float = Field(..., description="Price change from previous close")
    change_percent: float = Field(..., description="Percentage change")
    volume: Optional[int] = Field(None, description="Trading volume")
    market_cap: Optional[float] = Field(None, description="Market capitalization")
    pe_ratio: Optional[float] = Field(None, description="Price to earnings ratio")
    dividend_yield: Optional[float] = Field(None, description="Dividend yield percentage")
    last_updated: datetime = Field(default_factory=datetime.now, description="Last update timestamp")


class SectorPerformanceRequest(BaseModel):
    """Request model for sector performance data"""

    symbols: list[str] = Field(..., description="List of ETF symbols to fetch performance for")


class SectorPerformanceResponse(BaseModel):
    """Response model containing sector performance data"""

    performances: list[SectorPerformance] = Field(..., description="List of sector performances")
    request_timestamp: datetime = Field(default_factory=datetime.now, description="When the request was made")