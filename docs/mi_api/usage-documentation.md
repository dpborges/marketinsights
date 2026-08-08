# FastAPI usage

Run commands from the repository root. The application entry point is `src/mi_api/main.py`, and
the module-level ASGI application is `mi_api.main:app`.

## Start for development

```powershell
uv run fastapi dev src/mi_api/main.py
```

This starts the local development server with automatic reload. It is intended only for developer
workstations. Stop it with `Ctrl+C` in the terminal where it is running.

## Start with production-like settings

```powershell
uv run fastapi run src/mi_api/main.py --host 0.0.0.0 --port 8000
```

This starts the server without automatic reload and listens on all container or host interfaces.
Set `APP_ENV=production`, `ENABLE_DOCS=false`, and all required production environment variables
before using production mode. Stop a foreground process with `Ctrl+C`; service managers and
container platforms should stop it with their normal graceful-stop operation.

An equivalent direct Uvicorn command is:

```powershell
uv run uvicorn mi_api.main:app --app-dir src --host 0.0.0.0 --port 8000
```

## Verify the running API

With the server listening on port 8000:

```powershell
Invoke-RestMethod http://localhost:8000/health/live
Invoke-RestMethod http://localhost:8000/health/ready
Invoke-RestMethod http://localhost:8000/api/v1/system/info
Invoke-WebRequest http://localhost:8000/docs
Invoke-WebRequest http://localhost:8000/openapi.json
```

- `/health/live` confirms the process can answer requests without checking external systems.
- `/health/ready` checks configured PostgreSQL connectivity and required Redis connectivity.
- `/api/v1/system/info` returns non-sensitive name, version, and environment metadata.
- `/docs` serves Swagger UI when `ENABLE_DOCS=true`.
- `/openapi.json` serves the OpenAPI specification when `ENABLE_DOCS=true`.

Documentation endpoints return 404 when disabled, as required for production.

## Repository quality commands

```powershell
uv run ruff check .
```

Checks Python source for configured lint violations, unsafe patterns, import ordering, and supported
Python modernization rules. It reports problems without changing files.

```powershell
uv run ruff format --check .
```

Checks whether Python files match Ruff formatting without rewriting them. Run
`uv run ruff format .` to format files intentionally.

```powershell
uv run mypy .
```

Runs strict static type analysis over the repository. Type errors should not be hidden with broad
ignores.

```powershell
uv run pytest
```

Runs the unit and API test suites with async test support and branch coverage reporting for `src`.
