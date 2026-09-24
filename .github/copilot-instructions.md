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

## Asynchronous provider call chains

- Use async end to end for external provider requests: FastAPI route -> SDK service(s) -> provider adapter -> HTTP client.
- Declare functions that perform or await asynchronous I/O with `async def`, and `await` each downstream call, including SDK-to-SDK calls.
- Provider adapters must use a nonblocking HTTP client such as `httpx.AsyncClient`; changing a function to `async def` does not make synchronous HTTP calls nonblocking.
- Keep pure calculations, ranking, classification, and validation synchronous. Constructors and factories can remain synchronous when they do not perform asynchronous I/O.
- Do not call blocking HTTP clients or use `asyncio.run()` inside the API request call chain to bridge async services.
- When migrating an existing workflow, update its callers, interface protocols, tests, and mocks together. Use async tests and awaitable mocks for asynchronous dependencies.

## FastAPI standards

- FastAPI routes must stay thin
- Business logic belongs in the SDK/service layer
- Keeps domain and business logic out of route handlers.
- Validate inbound/outbound API payloads with Pydantic V2
- Use typed request and response models
- Convert SDK exceptions into consistent HTTP responses
- Use an application factory or clearly isolated application-construction function.
- Use dependency injection for service construction
- Use APIRouter modules rather than placing routes in one file.
- Use centralized configuration through pydantic-settings.
- Should support local, test, and production environments.
- Use structured logging.
- Is set up to integrate with PostgreSQL.

## Error handling

- Use the exception management pattern described in .github/prompts/exception-management/exception-management.md
- Do not leak provider-specific exceptions past the adapter layer

## Testing

- Generate pytest tests for SDK services and API routes

## FMP Adapter manual testing and validation

- For manual testing for newly created adapter service, look for a directive in the prompt of the specific FMP Adapter service itself. The fmp_adapter_run.py should be updated to be able to test the service manually.
