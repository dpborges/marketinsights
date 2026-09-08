# API testing

Run commands from the repository root in Git Bash. Use forward slashes in executable paths.

The commands below disable Git Bash path conversion for that invocation and explicitly
set `API_V1_PREFIX=/api/v1`. Otherwise, Git Bash can convert an exported prefix into
`C:/Program Files/Git/api/v1`, causing settings validation to fail during test collection.
These settings apply only to the command; they do not modify `.env`.

## Sector summary API test harness

Run only the sector summary endpoint tests:

```bash
MSYS_NO_PATHCONV=1 API_V1_PREFIX=/api/v1 \
uv run pytest tests/api/test_sector_summary.py -q
```

The harness replaces the real SDK service through FastAPI dependency injection, so it does
not call a market-data provider or require an API key. It verifies default SDK delegation,
single and comma-separated filters, case normalization, duplicate removal, invalid and empty
values, all sort combinations, the public `422` error contract, and OpenAPI query-parameter
documentation. Sorting tests also run the real SDK with a mocked price adapter to verify
single- and multi-period ordering while preserving the response payload.

## All API tests

```bash
MSYS_NO_PATHCONV=1 API_V1_PREFIX=/api/v1 \
uv run pytest tests/api -q
```

## Complete test suite

```bash
MSYS_NO_PATHCONV=1 API_V1_PREFIX=/api/v1 \
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

```bash
MSYS_NO_PATHCONV=1 API_V1_PREFIX=/api/v1 \
uv run pytest tests/api/test_sector_summary.py tests/sdk/test_sector_summary_service.py -q
```


## Sector leadership API test harness

Run from the repository root:

```bash
MSYS_NO_PATHCONV=1 API_V1_PREFIX=/api/v1 \
./.venv/Scripts/python.exe -m pytest tests/api/test_sector_leadership.py -q
```

Or with uv:

```bash
MSYS_NO_PATHCONV=1 API_V1_PREFIX=/api/v1 \
uv run pytest tests/api/test_sector_leadership.py -q
```

Run the leadership API and SDK tests together:

```bash
MSYS_NO_PATHCONV=1 API_V1_PREFIX=/api/v1 \
./.venv/Scripts/python.exe -m pytest tests/api/test_sector_leadership.py tests/sdk/test_sector_leadership_service.py -q
```

The API harness injects the real leadership and summary SDK services with a mocked price
adapter. No API key or network connection is needed. Tests cover explicit and default
periods, top 3 and top 5 selection, default top 5, normalized CSV periods, query validation,
response aliases, partial data errors, fatal SDK errors, sanitized unexpected failures,
and OpenAPI documentation.

### Requests and defaults

```text
/api/v1/sector/leadership?periods=2W,1M,3M&top_n=3
/api/v1/sector/leadership?periods=2W,1M,3M&top_n=5
/api/v1/sector/leadership?top_n=3
/api/v1/sector/leadership?top_n=5
```

Omitting `periods` uses `2W,1M,3M`. Leadership requires all three periods, because the
SDK uses 1M as anchor, 2W as momentum, and 3M as confirmation. Other periods supported
by sector summary cannot be used for leadership. CSV input is case-insensitive,
whitespace is trimmed, and duplicates are removed.

`top_n` accepts only `3` or `5` and defaults to `5`. Invalid values return HTTP 422
with the specified message `Invald top_n value. Only 3 and 5 are supported`.
`top_n=3` returns up to three sectors even when periods are omitted.

Successful responses preserve the SDK payload, including `errors` and coverage counts
before top-N selection. Partial results return HTTP 200 with their errors intact.
Fatal SDK errors return the leadership response shape with no sectors, zero successes,
11 failures, and a safe error entry containing a code, message, and request ID.
For fatal failures, `asOfDate` is the server request date rather than a market-data date.
HTTP status codes follow the central SDK exception mapping (for example, 422 for SDK
validation and 503 for provider unavailability). Invalid query parameters and unexpected
errors retain the standard API `error` envelope; unexpected errors return a sanitized 500.


## Async sector summary validation

The summary API awaits the summary SDK, which awaits the provider's async HTTP calls.
Leadership also awaits summary. Python SDK callers must now use
`await service.build_sector_summary(...)` and `await service.build_sector_leadership(...)`.
HTTP URLs and response formats are unchanged. CLI commands manage their event loop at
entry; no event loop bridge is used inside API requests.

Run the sector summary SDK, API, and provider tests from Git Bash:

```bash
MSYS_NO_PATHCONV=1 API_V1_PREFIX=/api/v1 ./.venv/Scripts/python.exe -m pytest tests/sdk/test_sector_summary_service.py tests/api/test_sector_summary.py tests/test_fmp_adapter.py -q
```

These tests use async mocks and a mocked HTTP transport; no live provider access is needed.
