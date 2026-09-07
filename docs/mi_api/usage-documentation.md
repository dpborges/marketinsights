# FastAPI usage

Run commands from the repository root in Git Bash. The application entry point is `src/mi_api/main.py`, and
the module-level ASGI application is `mi_api.main:app`.

Git Bash can convert an exported `/api/v1` prefix into a Windows filesystem path.
The startup commands below disable that conversion and set the correct prefix for
that invocation without modifying `.env`.

## Start for development

```bash
MSYS_NO_PATHCONV=1 API_V1_PREFIX=/api/v1 uv run fastapi dev src/mi_api/main.py
```

This starts the local development server with automatic reload. It is intended only for developer
workstations. Stop it with `Ctrl+C` in the terminal where it is running.

## Start with production-like settings

```bash
MSYS_NO_PATHCONV=1 API_V1_PREFIX=/api/v1 uv run fastapi run src/mi_api/main.py --host 0.0.0.0 --port 8000
```

This starts the server without automatic reload and listens on all container or host interfaces.
Set `APP_ENV=production`, `ENABLE_DOCS=false`, and all required production environment variables
before using production mode. Stop a foreground process with `Ctrl+C`; service managers and
container platforms should stop it with their normal graceful-stop operation.

An equivalent direct Uvicorn command is:

```bash
MSYS_NO_PATHCONV=1 API_V1_PREFIX=/api/v1 uv run uvicorn mi_api.main:app --app-dir src --host 0.0.0.0 --port 8000
```

## Verify the running API

With the server listening on port 8000:

```bash
curl http://localhost:8000/health/live
curl http://localhost:8000/health/ready
curl http://localhost:8000/api/v1/system/info
curl http://localhost:8000/docs
curl http://localhost:8000/openapi.json
```

- `/health/live` confirms the process can answer requests without checking external systems.
- `/health/ready` checks configured PostgreSQL connectivity and required Redis connectivity.
- `/api/v1/system/info` returns non-sensitive name, version, and environment metadata.
- `/docs` serves Swagger UI when `ENABLE_DOCS=true`.
- `/openapi.json` serves the OpenAPI specification when `ENABLE_DOCS=true`.

Documentation endpoints return 404 when disabled, as required for production.

## Repository quality commands

```bash
uv run ruff check .
```

Checks Python source for configured lint violations, unsafe patterns, import ordering, and supported
Python modernization rules. It reports problems without changing files.

```bash
uv run ruff format --check .
```

Checks whether Python files match Ruff formatting without rewriting them. Run
`uv run ruff format .` to format files intentionally.

```bash
uv run mypy .
```

Runs strict static type analysis over the repository. Type errors should not be hidden with broad
ignores.

```bash
MSYS_NO_PATHCONV=1 API_V1_PREFIX=/api/v1 uv run pytest
```

Runs the unit and API test suites with async test support and branch coverage reporting for `src`.
