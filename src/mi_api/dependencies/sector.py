"""Dependency providers for sector services."""

from mi_sdk.config.settings import SDKSettings
from mi_sdk.factory import ServiceFactory
from mi_sdk.services.sector_summary_service import SectorSummaryService


def get_sector_summary_service() -> SectorSummaryService:
    """Construct the configured sector summary SDK service."""

    return ServiceFactory(SDKSettings()).create_sector_summary_service()
