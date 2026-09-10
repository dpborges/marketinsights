"""Service factory for dependency injection"""

from .config.settings import SDKSettings
from .domain.exceptions import ConfigurationError
from .interfaces.sector_performance_service import SectorPerformanceService
from .providers.fmp.fmp_adapter import FMPAdapter
from .providers.fmp.fmp_analyst import FMPAnalystAdapter
from .services.analyst_service import AnalystService
from .services.sector_leadership_service import SectorLeadershipService
from .services.sector_performance_service import SectorPerformanceServiceImpl
from .services.sector_summary_service import SectorSummaryService


class ServiceFactory:
    """Factory for creating services with proper dependencies"""

    def __init__(self, settings: SDKSettings) -> None:
        self.settings = settings

    def create_sector_performance_service(self) -> SectorPerformanceService:
        """Create sector performance service with configured adapter"""

        adapter = self._build_adapter()
        return SectorPerformanceServiceImpl(adapter)

    def create_sector_summary_service(self) -> SectorSummaryService:
        """Create sector summary service with configured adapter."""

        adapter = self._build_adapter()
        return SectorSummaryService(adapter=adapter)

    def create_sector_leadership_service(self) -> SectorLeadershipService:
        """Create leadership service using the configured sector summary service."""
        return SectorLeadershipService(self.create_sector_summary_service())

    def create_analyst_service(self) -> AnalystService:
        """Create the analyst service with the configured provider and timeout."""
        if self.settings.provider.lower() != "fmp":
            raise ConfigurationError("Unsupported analyst provider.")
        api_key = self.settings.providers.fmp_api_key
        if not api_key or not api_key.strip():
            raise ConfigurationError("Analyst provider credentials are not configured.")
        return AnalystService(
            FMPAnalystAdapter(api_key=api_key, timeout=self.settings.providers.request_timeout)
        )

    def _build_adapter(self) -> FMPAdapter:
        if self.settings.provider.lower() == "fmp":
            if not self.settings.providers.fmp_api_key:
                raise ValueError("FMP API key not configured")

            return FMPAdapter(
                api_key=self.settings.providers.fmp_api_key,
                timeout=self.settings.providers.request_timeout,
            )

        raise ValueError(f"Unsupported provider: {self.settings.provider}")
