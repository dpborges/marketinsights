# FastAPI dependency setup

This project targets Python 3.10 or newer and manages dependencies with `uv` through
`pyproject.toml` and `uv.lock`. The FastAPI application itself is intentionally not part of this setup.

## Prerequisites

- Python 3.10 or newer (the repository's `.python-version` selects Python 3.10)
- PostgreSQL when running database-backed features
- `uv`

Install `uv` using an official installer, or see <https://docs.astral.sh/uv/getting-started/installation/>:

```powershell
winget install --id=astral-sh.uv -e
```

## Install and use the environment

Create or update `.venv` from the locked dependency set, including development tools:

```powershell
uv sync
```

Run commands without activating the environment by prefixing them with `uv run`. To activate it in PowerShell instead:

```powershell
.\.venv\Scripts\Activate.ps1
```

Do not commit credentials. Put local secrets in the gitignored `.env` file or inject them through the deployment platform's secret manager.

## Dependency management

Add runtime and development dependencies through the existing uv workflow:

```powershell
uv add <package>
uv add --dev <package>
```

Inspect packages with newer releases:

```powershell
uv tree --outdated
```

Update all dependencies, regenerate `uv.lock`, and synchronize the environment:

```powershell
uv lock --upgrade
uv sync
```

Review and commit both `pyproject.toml` and `uv.lock` after an intentional dependency change.

## Quality checks

Run the repository checks from its root:

```powershell
uv run ruff check .
uv run ruff format --check .
uv run mypy .
uv run pytest
```

To apply Ruff's safe formatting changes locally, run `uv run ruff format .`. Ruff lint fixes should
be reviewed before committing; inspect them first with `uv run ruff check .`.
