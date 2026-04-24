"""Example usage of the Market Insights SDK"""

import asyncio

from src.mi_sdk import SDKSettings, ServiceFactory
from src.mi_sdk.domain.models.sector_performance import SectorPerformanceRequest


async def main():
    """Example of using the sector performance service"""

    # Load settings from environment
    settings = SDKSettings()

    # Create service factory
    factory = ServiceFactory(settings)

    # Create sector performance service
    service = factory.create_sector_performance_service()

    # Create request for all SPDR sector ETFs
    request = SectorPerformanceRequest(
        symbols=[
            "XLK", "XLF", "XLV", "XLY", "XLI",
            "XLC", "XLE", "XLU", "XLP", "XLB", "XLRE"
        ]
    )

    try:
        # Fetch sector performance data
        response = await service.get_sector_performance(request)

        print("Sector Performance Data:")
        print("=" * 50)

        for performance in response.performances:
            print(f"{performance.symbol} ({performance.sector}):")
            print(".2f")
            print(".2f")
            print(".2f")
            if performance.volume:
                print(",")
            print("-" * 30)

        print(f"\nData fetched at: {response.request_timestamp}")

    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    asyncio.run(main())
