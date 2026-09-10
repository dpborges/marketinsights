"""Validated analyst API response contracts."""

from typing import Annotated, Literal

from pydantic import BaseModel, Field

Count = Annotated[int, Field(ge=0, strict=True)]
Price = Annotated[float, Field(ge=0, allow_inf_nan=False)]


class AnalystError(BaseModel):
    symbol: str
    code: str
    message: str


class AnalystConsensus(BaseModel):
    symbol: str
    strongBuy: Count
    buy: Count
    hold: Count
    sell: Count
    strongSell: Count
    recommendation: Literal["strongBuy", "buy", "hold", "sell", "strongSell"]


class AnalystPriceTarget(BaseModel):
    symbol: str
    high: Price
    low: Price
    median: Price
    consensus: Price


class AnalystConsensusResponse(BaseModel):
    consensus: list[AnalystConsensus]
    errors: list[AnalystError]


class AnalystTargetsResponse(BaseModel):
    priceTargets: list[AnalystPriceTarget]
    errors: list[AnalystError]
