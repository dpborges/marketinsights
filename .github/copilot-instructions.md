# Market Insights SDK + FastAPI project instructions

## Architecture
- The SDK is provider-agnostic.
- Public interfaces must not expose provider-specific names such as FMP or AlphaVantage.
- Use domain-oriented service names such as PricingService, EarningsService, AnalystService, and TechnicalIndicatorService.
- Provider-specific adapters belong under internal provider packages.

## Python standards
- Use Python 3.12+
- Prefer type hints everywhere
- Prefer small service classes and dependency injection
- Use Pydantic v2 for API request/response models and configuration
- Keep core SDK domain logic decoupled from FastAPI

## FastAPI standards
- FastAPI routes must stay thin
- Business logic belongs in the SDK/service layer
- Validate inbound/outbound API payloads with Pydantic
- Convert SDK exceptions into consistent HTTP responses
- Use dependency injection for service construction

## Error handling
- Use SDK exception hierarchy rather than ad hoc ValueError/RuntimeError
- Do not leak provider-specific exceptions past the adapter layer

## Testing
- Generate pytest tests for services, adapters, and API routes
- Mock provider adapters in API tests

