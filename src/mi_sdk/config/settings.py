"""Configuration settings for the SDK"""

from typing import Optional

from pydantic_settings import BaseSettings, SettingsConfigDict


class MarketProviderSettings(BaseSettings):
    """Settings for market data providers"""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_prefix="MARKET_",
        case_sensitive=False,
        extra="ignore",
    )

    fmp_api_key: Optional[str] = None
    alphavantage_api_key: Optional[str] = None
    request_timeout: int = 30


class SDKSettings(BaseSettings):
    """Main SDK settings"""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_prefix="MARKET_",
        case_sensitive=False,
        extra="ignore",
    )

    provider: str = "fmp"  # Default provider
    providers: MarketProviderSettings = MarketProviderSettings()