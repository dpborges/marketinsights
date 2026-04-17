## Architecture
- The SDK is provider-agnostic.
- Public interfaces must not expose provider-specific names such as FMP or AlphaVantage.
- Use domain-oriented service names such as SectoryService, PricingService, EarningsService, AnalystService, and TechnicalIndicatorService.
- Provider-specific adapters belong under internal provider packages.

## Python standards
- Use Python 3.12+
- Prefer type hints everywhere
- Prefer small service classes and dependency injection
- Use Pydantic v2 for API request/response models and configuration
- Use Async services for all calls to REST / API providers
- Keep core SDK domain logic decoupled from FastAPI

## Configuration management
- use dotenv to manage enviroment variables 
  - Example
    - MARKET_PROVIDER=fmp
    - FMP_API_KEY=your_key_here
    - ALPHAVANTAGE_API_KEY=your_key_here
    - REQUEST_TIMEOUT=30

- use pydantic-settings for configuration management

## Error handling
- Use SDK exception hierarchy rather than ad hoc ValueError/RuntimeError, for example
  - SdkError
  - ConfigurationError
  - AuthenticationError
  - AuthorizationError
  - RateLimitError
  - ProviderUnavailableError
  - DataValidationError
  - SymbolNotFoundError
  - UnsupportedOperationError
- Do not leak provider-specific exceptions past the adapter layer

## Testing
- Generate pytest tests for services, adapters, and API routes
- Mock provider adapters in API tests


## SDK Project Hierarchy
- src
  - mi_sdk
    - config (settigns.py)
    - domain ( contains domain models)
    - interfaces (pricing_service.py)
    - mappers (provider payload mapping to canonical domain model)
    - provider (provider specific code for  FMP, yahoo finance, or alphavantage)
    - services 
    - streaming (optional RxPy adapters later)
    - transport (http client wrappers)

## Public API design
Keep the SDK public surface generic and provider-neutral.
That allows for switching providers without changing the application-facing API.

### Example public services:
- PricingService
- EarningsService
- AnalystService
###  Example provider-specific classes should stay internal:
- FmpPricingProvider
- AlphaVantageEarningsProvider
