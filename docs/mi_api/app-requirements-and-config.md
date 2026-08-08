# FastAPI application requirements and configuration

## Application requirements

The HTTP application:

- Uses FastAPI, Pydantic v2, APIRouter modules, dependency injection, and explicit response models.
- Is constructed through `create_app()` and also exports a module-level `app` for ASGI servers.
- Places versioned endpoints under the configurable `/api/v1` prefix.
- Keeps existing SDK services, provider adapters, domain models, SQLAlchemy models, Alembic files,
  and CLI code in their current packages.
- Uses lifespan management for database, Redis, and application lifecycle cleanup.
- Emits structured application and access logs with request correlation IDs.
- Applies trusted-host, configurable CORS, and GZip middleware.
- Returns centralized JSON errors without stack traces or internal exception messages.
- Provides inexpensive process liveness and dependency-aware readiness endpoints.
- Uses one synchronous SQLAlchemy engine because the existing PostgreSQL driver is psycopg.
- Does not return SQLAlchemy models or execute domain queries in route handlers.

## Environment variables

| Variable | Default | Purpose |
|---|---:|---|
| `APP_NAME` | `market-insights-api` | Public service name. |
| `APP_ENV` | `local` | One of `local`, `test`, or `production`. |
| `APP_VERSION` | `1.0.0` | Public API service version. |
| `DEBUG` | `false` | Framework debug behavior; forbidden in production. |
| `LOG_LEVEL` | `INFO` | Structured logging threshold. |
| `API_V1_PREFIX` | `/api/v1` | Prefix for versioned routers. |
| `HOST` | `127.0.0.1` | Documented server bind host. |
| `PORT` | `8000` | Documented server port. |
| `WORKERS` | `1` | Intended ASGI worker count. |
| `DATABASE_URL` | unset | SQLAlchemy PostgreSQL URL; required in production. |
| `REDIS_URL` | unset | Redis connection URL. |
| `REDIS_REQUIRED` | `false` | Makes Redis part of readiness when true. |
| `CORS_ALLOWED_ORIGINS` | empty | Comma-separated browser origins. |
| `TRUSTED_HOSTS` | local hosts | Comma-separated accepted HTTP Host values. |
| `ENABLE_DOCS` | `true` | Enables `/docs` and `/openapi.json`; must be false in production. |
| `SECRET_KEY` | unset | Authentication secret; at least 32 characters in production. |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | `30` | Intended access-token lifetime. |

The SDK continues to use its existing `MARKET_*` variables. See `.env.example` for non-secret local
placeholders.

## Validation and security

Settings load from environment variables and optionally from `.env` for local development. The
populated `.env` file must never be committed. Deployment secrets should come from the platform's
secret manager.

Production configuration fails during application construction when:

- `DATABASE_URL` is missing.
- Debug mode or API documentation is enabled.
- `SECRET_KEY` is missing or shorter than 32 characters.
- Trusted hosts are empty or contain `*`.
- CORS origins contain `*`.
- Redis is marked required without a Redis URL.

Credentialed CORS is enabled only for explicit origin lists; wildcard origins are never combined
with credentialed requests.
