"""Environment-driven settings for the HTTP API."""

from enum import Enum
from typing import Annotated, Any

from pydantic import Field, SecretStr, field_validator, model_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict


class Environment(str, Enum):
    """Supported application environments."""

    LOCAL = "local"
    TEST = "test"
    PRODUCTION = "production"


StringList = Annotated[list[str], NoDecode]


class APISettings(BaseSettings):
    """Validated runtime configuration loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    app_name: str = "market-insights-api"
    app_env: Environment = Environment.LOCAL
    app_version: str = "1.0.0"
    debug: bool = False
    log_level: str = "INFO"
    api_v1_prefix: str = "/api/v1"
    host: str = "127.0.0.1"
    port: int = Field(default=8000, ge=1, le=65535)
    workers: int = Field(default=1, ge=1)
    database_url: str | None = None
    redis_url: str | None = None
    redis_required: bool = False
    cors_allowed_origins: StringList = Field(default_factory=list)
    trusted_hosts: StringList = Field(
        default_factory=lambda: ["localhost", "127.0.0.1", "testserver"]
    )
    enable_docs: bool = True
    secret_key: SecretStr | None = None
    access_token_expire_minutes: int = Field(default=30, ge=1)

    @field_validator("api_v1_prefix")
    @classmethod
    def validate_prefix(cls, value: str) -> str:
        normalized = value.rstrip("/")
        if not normalized.startswith("/") or normalized == "":
            raise ValueError("API_V1_PREFIX must start with '/'")
        return normalized

    @field_validator("debug", mode="before")
    @classmethod
    def parse_debug(cls, value: Any) -> Any:
        if isinstance(value, str):
            normalized = value.lower()
            if normalized in {"release", "production"}:
                return False
            if normalized in {"development", "develop"}:
                return True
        return value

    @field_validator("log_level")
    @classmethod
    def validate_log_level(cls, value: str) -> str:
        normalized = value.upper()
        if normalized not in {"CRITICAL", "ERROR", "WARNING", "INFO", "DEBUG"}:
            raise ValueError("LOG_LEVEL is not valid")
        return normalized

    @field_validator("cors_allowed_origins", "trusted_hosts", mode="before")
    @classmethod
    def parse_string_list(cls, value: Any) -> Any:
        if isinstance(value, str):
            return [item.strip() for item in value.split(",") if item.strip()]
        return value

    @model_validator(mode="after")
    def validate_environment_security(self) -> "APISettings":
        if self.redis_required and not self.redis_url:
            raise ValueError("REDIS_URL is required when REDIS_REQUIRED is true")

        if self.app_env is Environment.PRODUCTION:
            if not self.database_url:
                raise ValueError("DATABASE_URL is required in production")
            if self.debug:
                raise ValueError("DEBUG must be false in production")
            if self.enable_docs:
                raise ValueError("ENABLE_DOCS must be false in production")
            if not self.secret_key or len(self.secret_key.get_secret_value()) < 32:
                raise ValueError("SECRET_KEY must contain at least 32 characters in production")
            if not self.trusted_hosts or "*" in self.trusted_hosts:
                raise ValueError("TRUSTED_HOSTS must be explicit in production")
            if "*" in self.cors_allowed_origins:
                raise ValueError("CORS_ALLOWED_ORIGINS cannot contain '*' in production")

        return self
