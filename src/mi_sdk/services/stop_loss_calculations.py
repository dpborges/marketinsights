"""Pure deterministic OHLCV, Wilder ATR, swing and support calculations."""

from dataclasses import dataclass
from datetime import date, timedelta
from math import fsum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, ValidationError, model_validator

from .exceptions import MarketDataError


class PriceBar(BaseModel):
    model_config = ConfigDict(allow_inf_nan=False, frozen=True)

    date: date
    open: float = Field(gt=0)
    high: float = Field(gt=0)
    low: float = Field(gt=0)
    close: float = Field(gt=0)
    volume: float = Field(ge=0)

    @model_validator(mode="after")
    def valid_range(self) -> "PriceBar":
        if not self.low <= min(self.open, self.close) <= max(self.open, self.close) <= self.high:
            raise ValueError("Inconsistent OHLC range")
        return self


def calculation_error(message: str, code: str) -> MarketDataError:
    return MarketDataError(message, code, retryable=False)


def parse_bars(payload: Any, as_of: date) -> list[PriceBar]:
    if not isinstance(payload, list):
        raise calculation_error("Invalid historical price data.", "INVALID_PRICE_DATA")
    try:
        bars = sorted((PriceBar.model_validate(row) for row in payload), key=lambda bar: bar.date)
    except (ValidationError, TypeError, ValueError) as exc:
        raise calculation_error("Invalid historical OHLCV data.", "INVALID_PRICE_DATA") from exc
    if len({bar.date for bar in bars}) != len(bars) or any(bar.date > as_of for bar in bars):
        raise calculation_error("Duplicate or future historical dates.", "INVALID_PRICE_DATA")
    return bars


def weekly_bars(bars: list[PriceBar], as_of: date) -> list[PriceBar]:
    """Monday-based weeks; omit the current week and a partial starting week."""
    current_week = as_of - timedelta(days=as_of.weekday())
    groups: dict[date, list[PriceBar]] = {}
    for bar in bars:
        monday = bar.date - timedelta(days=bar.date.weekday())
        if monday < current_week:
            groups.setdefault(monday, []).append(bar)
    result = []
    for monday, group in groups.items():
        if monday < bars[0].date:
            continue
        result.append(
            PriceBar(
                date=group[-1].date,
                open=group[0].open,
                high=max(bar.high for bar in group),
                low=min(bar.low for bar in group),
                close=group[-1].close,
                volume=fsum(bar.volume for bar in group),
            )
        )
    return result


def calculate_atr(bars: list[PriceBar], period: int) -> float:
    """Seed with N ranges having previous closes, then apply Wilder smoothing."""
    if len(bars) < period + 1:
        raise calculation_error("Insufficient bars for ATR.", "INSUFFICIENT_HISTORY")
    ranges = [
        max(bar.high - bar.low, abs(bar.high - previous.close), abs(bar.low - previous.close))
        for previous, bar in zip(bars[:-1], bars[1:], strict=True)
    ]
    atr = fsum(ranges[:period]) / period
    for value in ranges[period:]:
        atr = atr * ((period - 1) / period) + value / period
    return atr


@dataclass(frozen=True)
class SwingLow:
    index: int
    price: float


def find_swing_lows(bars: list[PriceBar], window: int = 2) -> list[SwingLow]:
    """Confirm a plateau against W bars on either side; count its last bar once."""
    swings = []
    start = 0
    while start < len(bars):
        end = start
        low = bars[start].low
        while end + 1 < len(bars) and bars[end + 1].low == low:
            end += 1
        if start >= window and end + window < len(bars):
            left = [bar.low for bar in bars[start - window : start]]
            right = [bar.low for bar in bars[end + 1 : end + window + 1]]
            if (
                all(low <= value for value in left + right)
                and any(low < value for value in left)
                and any(low < value for value in right)
            ):
                swings.append(SwingLow(end, low))
        start = end + 1
    return swings


@dataclass(frozen=True)
class SupportZone:
    price: float
    strength: float
    touches: int
    latest_index: int


def select_support(
    bars: list[PriceBar],
    swings: list[SwingLow],
    atr: float,
    current: float,
    buffer: float,
    window: int,
) -> SupportZone:
    """Price-sorted clusters span <=0.5 ATR, avoiding chained distant levels.

    Touch score saturates at five touches. Recency is the latest touch index
    divided by the final bar index. Rebound is the average next-W-bar high
    excursion, normalized by 2 ATR and capped at one. Ties prefer recency,
    then the higher support price. Only valid stops compete.
    """
    clusters: list[list[SwingLow]] = []
    for swing in sorted((s for s in swings if s.price < current), key=lambda s: s.price):
        if not clusters or swing.price - clusters[-1][0].price > 0.5 * atr:
            clusters.append([])
        clusters[-1].append(swing)
    zones = []
    for cluster in clusters:
        price = fsum(s.price / len(cluster) for s in cluster)
        if not 0 < price - atr * buffer < current:
            continue
        latest = max(s.index for s in cluster)
        rebounds = [
            min(
                1.0,
                max(
                    0.0, max(bar.high for bar in bars[s.index + 1 : s.index + window + 1]) - s.price
                )
                / (2 * atr),
            )
            if atr > 0
            else 0.0
            for s in cluster
        ]
        strength = (
            0.4 * min(len(cluster) / 5, 1.0)
            + 0.3 * latest / (len(bars) - 1)
            + 0.3 * fsum(rebounds) / len(cluster)
        )
        zones.append(SupportZone(price, strength, len(cluster), latest))
    if not zones:
        raise calculation_error("No support produces a valid stop.", "NO_VALID_SUPPORT")
    return max(zones, key=lambda zone: (zone.strength, zone.latest_index, zone.price))
