"""Market Insights SDK"""

from .config.settings import SDKSettings
from .config.stop_loss_settings import StopLossSettings
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
from .domain.models.stop_loss import InvestmentHorizon
from .factory import ServiceFactory
from .interfaces import SectorPerformanceService
from .services.calculation_service import CalculationService
from .services.company_service import CompanyService
from .services.exceptions import MarketDataError
from .services.sector_leadership_service import SectorLeadershipService

__all__ = [
    # Settings
    "SDKSettings",
    "StopLossSettings",
    # Domain models
    "InvestmentHorizon",
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
    "CalculationService",
    "CompanyService",
    "SectorPerformanceService",
    "SectorLeadershipService",
    # Factory
    "ServiceFactory",
]
