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
from .services.company_service import CompanyService
from .services.exceptions import MarketDataError
from .services.sector_leadership_service import SectorLeadershipService

__all__ = [
    # Settings
    "SDKSettings",
    # Domain models
    "SectorPerformance",
    "SectorPerformanceRequest",
    "SectorPerformanceResponse",
    # Exceptions
    "SdkError",
    "MarketDataError",
    "ConfigurationError",
    "AuthenticationError",
    "AuthorizationError",
    "RateLimitError",
    "ProviderUnavailableError",
    "DataValidationError",
    "SymbolNotFoundError",
    "UnsupportedOperationError",
    # Services
    "CompanyService",
    "SectorPerformanceService",
    "SectorLeadershipService",
    # Factory
    "ServiceFactory",
]
