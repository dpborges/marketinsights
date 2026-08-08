# FastAPI architecture

## Goals

The API is a modular HTTP delivery layer around the existing Market Insights SDK and database
packages. It does not duplicate business logic, provider code, persistence models, migrations, or CLI behavior.

The design uses:

- FastAPI with Pydantic v2 models.
- An application factory for isolated construction and test configuration.
- Small APIRouter modules organized by HTTP responsibility, which effective maps to business domains.
- Dependency providers for settings and request-scoped database sessions.
- Centralized, environment-driven Pydantic settings.
- Structured JSON logging in production and readable structured logs elsewhere.
- Lifespan-managed database and Redis resources.
- A single error contract and centralized exception-to-HTTP translation.
- Middleware for request IDs, access logs, trusted hosts, CORS, and response compression.

## Package responsibilities

```text
src/mi_api/
|-- main.py              Application factory, middleware, routers, lifespan
|-- config/              Environment settings and production validation
|-- routers/             Health and versioned HTTP routes
|-- schemas/             Public request and response contracts
|-- dependencies/        Settings, database engine, and session providers
|-- security/            Future authentication and authorization primitives
|-- middleware/          Request correlation and access logging
|-- observability/       Structlog configuration
`-- errors.py            Public errors and centralized handlers
```

Existing modules retain their responsibilities:

- `mi_sdk/domain` owns domain models and domain exceptions.
- `mi_sdk/services` owns business workflows.
- `mi_sdk/providers` owns external market-data integration.
- `mi_sdk/interfaces` defines service and adapter boundaries.
- `src/db/models` owns SQLAlchemy persistence models and metadata.
- `alembic` owns schema migrations.
- `mi_sdk/cli` remains the command-line delivery layer.

## Request flow

An HTTP request passes through trusted-host, request-correlation, CORS, and compression middleware before reaching a router. 
The router validates input into a public schema and obtains services or
sessions through dependencies. 
Business behavior remains in SDK services. 
Known failures are translated into stable public error codes; unexpected failures are logged with request context and returned as sanitized HTTP 500 responses.

The liveness endpoint performs no external I/O. Readiness checks PostgreSQL only when configured and Redis only when marked required. This keeps local and unit-test construction independent of live infrastructure while allowing production orchestration to detect dependency failures.
