"""Public response contracts for sector endpoints."""

from pydantic import BaseModel, ConfigDict, Field


class Performance(BaseModel):
    """Absolute and percentage performance for a period."""

    absolute_change: float | None = Field(default=None, alias="absoluteChange")
    return_pct: float = Field(alias="returnPct")

    model_config = ConfigDict(populate_by_name=True)


class RelativeStrength(BaseModel):
    """Performance relative to the SPY benchmark."""

    excess_return_pct: float = Field(alias="excessReturnPct")
    outperformed_benchmark: bool = Field(alias="outperformedBenchmark")

    model_config = ConfigDict(populate_by_name=True)


class Ranking(BaseModel):
    """Sector rankings within a requested period."""

    return_rank: int = Field(alias="returnRank")
    relative_strength_rank: int = Field(alias="relativeStrengthRank")

    model_config = ConfigDict(populate_by_name=True)


class PricePoint(BaseModel):
    """Adjusted closing price on a trading date."""

    date: str
    adjusted_close: float = Field(alias="adjustedClose")

    model_config = ConfigDict(populate_by_name=True)


class SectorPeriodSummary(BaseModel):
    """A sector's metrics for one period in a multi-period response."""

    period_code: str = Field(alias="periodCode")
    performance: Performance
    relative_strength: RelativeStrength = Field(alias="relativeStrength")
    ranking: Ranking

    model_config = ConfigDict(populate_by_name=True)


class SectorSummary(BaseModel):
    """A sector summary in either single-period or multi-period form."""

    symbol: str
    sector_code: str = Field(alias="sectorCode")
    sector_name: str = Field(alias="sectorName")
    current: PricePoint | None = None
    lookback: PricePoint | None = None
    performance: Performance | None = None
    relative_strength: RelativeStrength | None = Field(default=None, alias="relativeStrength")
    ranking: Ranking | None = None
    periods: list[SectorPeriodSummary] | None = None

    model_config = ConfigDict(populate_by_name=True)


class RequestedPeriod(BaseModel):
    """Resolved date window for a single-period response."""

    period_code: str = Field(alias="periodCode")
    requested_trading_days: int = Field(alias="requestedTradingDays")
    current_date: str = Field(alias="currentDate")
    lookback_date: str = Field(alias="lookbackDate")

    model_config = ConfigDict(populate_by_name=True)


class BenchmarkPeriod(BaseModel):
    """SPY benchmark metrics for one requested period."""

    period_code: str = Field(alias="periodCode")
    requested_trading_days: int = Field(alias="requestedTradingDays")
    current_date: str = Field(alias="currentDate")
    lookback_date: str = Field(alias="lookbackDate")
    performance: Performance

    model_config = ConfigDict(populate_by_name=True)


class Benchmark(BaseModel):
    """SPY benchmark in single-period or multi-period form."""

    symbol: str
    current_adjusted_close: float | None = Field(default=None, alias="currentAdjustedClose")
    lookback_adjusted_close: float | None = Field(default=None, alias="lookbackAdjustedClose")
    absolute_change: float | None = Field(default=None, alias="absoluteChange")
    return_pct: float | None = Field(default=None, alias="returnPct")
    periods: list[BenchmarkPeriod] | None = None

    model_config = ConfigDict(populate_by_name=True)


class SectorSummaryResponse(BaseModel):
    """Sector summary returned by the SDK workflow."""

    provider: str
    status: str
    as_of_date: str = Field(alias="asOfDate")
    period: RequestedPeriod | None = None
    benchmark: Benchmark
    requested_sector_count: int = Field(alias="requestedSectorCount")
    successful_sector_count: int = Field(alias="successfulSectorCount")
    failed_sector_count: int = Field(alias="failedSectorCount")
    sectors: list[SectorSummary]
    errors: list[dict[str, object]]

    model_config = ConfigDict(populate_by_name=True)
