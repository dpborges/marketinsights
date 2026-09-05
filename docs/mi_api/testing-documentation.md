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
values, all sort combinations, the public `422` error contract, and OpenAPI query-parameter
documentation. Sorting tests also run the real SDK with a mocked price adapter to verify
single- and multi-period ordering while preserving the response payload.

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


## Sector summary sorting

The endpoint accepts four optional parameters: `symbols`, `periods`, `sort_by`, and
`sort_direction`. Symbols and periods remain comma-separated lists.

- `sort_by`: `performance` (`performance.returnPct`) or `relative_strength`
  (`relativeStrength.excessReturnPct`); defaults to `relative_strength`.
- `sort_direction`: `asc` or `desc`; defaults to `desc`.

Sort values are case-insensitive and surrounding whitespace is trimmed. Invalid or empty
sort values return `422` with `INVALID_QUERY_PARAMETER`, `parameter`, and `allowedValues`.
For multiple periods, the first requested period determines sector order. The JSON
structure and ranking values are unchanged; only the order of `sectors` changes.
Omitting symbols selects all SPDR sector ETFs; omitting periods selects `2W`.

Use `&` between query parameters and commas only within lists:

```text
/api/v1/sector/summary?periods=2W&sort_by=relative_strength&sort_direction=desc
/api/v1/sector/summary?symbols=XLF,XLK,XLV&periods=2W,1M&sort_by=performance&sort_direction=asc
```

Run the API harness together with the SDK sector summary tests:

```powershell
uv run pytest tests/api/test_sector_summary.py tests/test_sector_summary_service.py -q
```
