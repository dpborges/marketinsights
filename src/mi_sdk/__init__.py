"""Market Insights SDK"""

from .config.settings import SDKSettings
from .domain import (
    AuthenticationError,
    AuthorizationError,
    ConfigurationError,
    DataValidationError,
    ProviderUnavailableError,
    RateLimitError,
    SdkError,
    SectorPerformance,
    SectorPerformanceRequest,
    SectorPerformanceResponse,
    SymbolNotFoundError,
    UnsupportedOperationError,
)
from .factory import ServiceFactory
from .interfaces import SectorPerformanceService

__all__ = [
    # Settings
    "SDKSettings",
    # Domain models
    "SectorPerformance",
    "SectorPerformanceRequest",
    "SectorPerformanceResponse",
    # Exceptions
    "SdkError",
    "ConfigurationError",
    "AuthenticationError",
    "AuthorizationError",
    "RateLimitError",
    "ProviderUnavailableError",
    "DataValidationError",
    "SymbolNotFoundError",
    "UnsupportedOperationError",
    # Services
    "SectorPerformanceService",
    # Factory
    "ServiceFactory",
]