"""Service factory for dependency injection"""

from .config.settings import SDKSettings
from .interfaces.sector_performance_service import SectorPerformanceService
from .providers.fmp.fmp_adapter import FMPAdapter
from .services.sector_performance_service import SectorPerformanceServiceImpl


class ServiceFactory:
    """Factory for creating services with proper dependencies"""

    def __init__(self, settings: SDKSettings) -> None:
        self.settings = settings

    def create_sector_performance_service(self) -> SectorPerformanceService:
        """Create sector performance service with configured adapter"""

        if self.settings.provider.lower() == "fmp":
            if not self.settings.providers.fmp_api_key:
                raise ValueError("FMP API key not configured")

            adapter = FMPAdapter(
                api_key=self.settings.providers.fmp_api_key,
                timeout=self.settings.providers.request_timeout,
            )
        else:
            raise ValueError(f"Unsupported provider: {self.settings.provider}")

        return SectorPerformanceServiceImpl(adapter)