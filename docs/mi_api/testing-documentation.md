# API testing

Run commands from the repository root.

## Sector summary API test harness

Run only the sector summary endpoint tests:

```powershell
uv run pytest tests/api/test_sector_summary.py -q
```

The harness replaces the real SDK service through FastAPI dependency injection, so it does
not call a market-data provider or require an API key. It verifies default SDK delegation,
single and comma-separated filters, case normalization, duplicate removal, invalid and empty
values, the public `422` error contract, and OpenAPI query-parameter documentation.

## All API tests

```powershell
uv run pytest tests/api -q
```

## Complete test suite

```powershell
uv run pytest
```

The repository's pytest configuration automatically adds `src` to the Python import path and
collects branch coverage for the `src` tree.
