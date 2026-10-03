"""Validated starting parameters for stop-loss calculations, pending backtesting."""

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class StopLossSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="STOP_LOSS_", env_file=".env", extra="ignore", allow_inf_nan=False
    )

    short_atr_period: int = Field(default=14, gt=0)
    short_atr_buffer: float = Field(default=0.50, ge=0)
    short_swing_window: int = Field(default=2, gt=0)
    medium_atr_period: int = Field(default=20, gt=0)
    medium_atr_buffer: float = Field(default=0.75, ge=0)
    medium_swing_window: int = Field(default=2, gt=0)
    long_atr_period: int = Field(default=14, gt=0)
    long_atr_buffer: float = Field(default=1.00, ge=0)
    long_swing_window: int = Field(default=2, gt=0)
