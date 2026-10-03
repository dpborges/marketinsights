"""Provider-neutral stop-loss result models."""

from enum import Enum
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class InvestmentHorizon(str, Enum):
    SHORT = "SHORT"
    MEDIUM = "MEDIUM"
    LONG = "LONG"


class CalculationModel(BaseModel):
    model_config = ConfigDict(allow_inf_nan=False)


class StopLoss(CalculationModel):
    price: float = Field(gt=0)
    downsidePct: float = Field(gt=0, lt=100)
    method: Literal["SUPPORT_ATR"] = "SUPPORT_ATR"


class Support(CalculationModel):
    price: float = Field(gt=0)
    strength: float = Field(ge=0, le=1)
    touches: int = Field(gt=0)


class Volatility(CalculationModel):
    atr: float = Field(ge=0)
    atrPeriod: int = Field(gt=0)
    atrTimeframe: Literal["DAILY", "WEEKLY"]
    bufferMultiplier: float = Field(ge=0)


class HorizonStopLoss(CalculationModel):
    stopLoss: StopLoss
    support: Support
    volatility: Volatility


class CompanyStopLoss(CalculationModel):
    symbol: str
    currentPrice: float = Field(gt=0)
    horizons: dict[InvestmentHorizon, HorizonStopLoss]
