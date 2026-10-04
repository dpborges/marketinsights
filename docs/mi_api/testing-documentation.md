# Calculation API testing

Run the mocked Calculation API harness from the repository root in PowerShell:

```powershell
.venv/Scripts/python.exe -m pytest tests/api/test_calculation.py --no-cov -v
```

The tests need no provider credentials, network, PostgreSQL, or Redis. They cover
the sample requests, default and case-insensitive horizons, symbol normalization,
deduplication, the ten-unique-symbol boundary, validation before service
construction, exact SDK response preservation, partial/all item failures,
SDK exception mapping, response validation, dependency wiring, and OpenAPI.

For manual testing, configure `MARKET_FMP_API_KEY` in the environment or `.env`
and start the application:

```powershell
.venv/Scripts/python.exe -m uvicorn mi_api.main:app --app-dir src --reload
```

Open http://localhost:8000/docs and expand **calculation**, or run:

```powershell
curl.exe "http://localhost:8000/api/v1/calculation/stop-loss?symbols=META&horizons=SHORT,MEDIUM"
curl.exe "http://localhost:8000/api/v1/calculation/stop-loss?symbols=IBM&horizons=short,medium"
curl.exe "http://localhost:8000/api/v1/calculation/stop-loss?symbols=AAPL&horizons=short"
curl.exe "http://localhost:8000/api/v1/calculation/stop-loss?symbols=,META,APPL&horizons=SHORT,medium,LONG"
curl.exe "http://localhost:8000/api/v1/calculation/stop-loss?symbols=AAPL"
```

Symbols are trimmed, uppercased, and deduplicated in request order; empty symbol
entries are ignored. Missing symbols or an empty resulting list return HTTP 400
with `No symbols provided`. More than ten unique symbols return HTTP 400 with
`10 symbol request limit exceeded`. Embedded whitespace in a symbol is rejected.
`APPL` in the sample is passed through as written; use `AAPL` for Apple.

Omitted horizons default to `SHORT`. Provided horizons are trimmed, uppercased,
and deduplicated in request order. An empty horizons list returns HTTP 400 with
`No horizons provided`. Values other than `SHORT`, `MEDIUM`, and `LONG`, including
empty entries mixed with valid horizons, return HTTP 400 with
`Invalid horizon value provided`.

Successful requests return the SDK's `companies`, `errors`, and `summary`, with
each company's `currentPrice` and calculations under its `horizons` dictionary.
Each horizon includes `stopLoss`, `support`, and `volatility`. The SDK rounds
response floats to two decimal places, except `support.strength`, which uses
three. Calculations retain full precision internally. Partial and all item
failures remain HTTP 200. Operation-wide
failures use the centralized SDK exception handler, including HTTP 503 for
unavailability and HTTP 504 for timeouts. Responses are validated against the
SDK domain models.

# Analyst API testing

Run from the repository root in PowerShell:

```powershell
.venv/Scripts/python.exe -m pytest tests/api/test_analyst.py --no-cov -v
```

Run all API and SDK regression tests:

```powershell
.venv/Scripts/python.exe -m pytest tests/api tests/sdk --no-cov -q
```

The analyst tests use mocked asynchronous SDK services and require no provider key,
network access, PostgreSQL, or Redis. They cover single and multiple symbols,
the ten-symbol boundary, HTTP 400 validation, partial failures, response validation,
normalization, sanitized fatal errors, and OpenAPI registration.

For manual testing, configure `MARKET_FMP_API_KEY` in the environment or `.env`,
then start the application from the repository root:

```powershell
.venv/Scripts/python.exe -m uvicorn mi_api.main:app --app-dir src --reload
```

Open http://localhost:8000/docs and expand the **analyst** endpoints, or run:

```powershell
curl.exe "http://localhost:8000/api/v1/analyst/consensus?symbols=NVDA"
curl.exe "http://localhost:8000/api/v1/analyst/consensus?symbols=NVDA,META,AAPL,IBM"
curl.exe "http://localhost:8000/api/v1/analyst/targets?symbols=NVDA"
curl.exe "http://localhost:8000/api/v1/analyst/targets?symbols=NVDA,META,AAPL,IBM"
```

Both endpoints accept one to ten comma-separated symbols. Consensus returns
`consensus` and `errors`; targets returns `priceTargets` and `errors`, with flat
`symbol`, `high`, `low`, `median`, and `consensus` fields in each target record.
Per-symbol SDK failures remain in `errors` with HTTP 200, including when all symbols
fail. Missing or blank symbols return HTTP 400 with `No symbols provided`;
more than ten symbols return HTTP 400 with `10 symbol request limit exceeded`.
Fatal SDK failures use the application's centralized error handling.

For the broader API testing guide, see [api-testing-documentation.md](api-testing-documentation.md).


# Company API testing

Run the mocked company API harness from the repository root:

```powershell
.venv/Scripts/python.exe -m pytest tests/api/test_company.py --no-cov -v
```

Git Bash with the project environment activated:

```bash
python -m pytest tests/api/test_company.py --no-cov -v
```

No provider key, network, database, or Redis is needed. Tests cover both routes,
full profile field preservation, summary fields, single/multiple symbols,
normalization and deduplication, the ten-unique-symbol limit, validation before
service construction, partial/all item failures, SDK error status mapping,
response validation, dependency wiring, and OpenAPI registration.

Start the application using the uvicorn command above. With docs enabled, open
http://localhost:8000/docs and expand **company**, or run:

```powershell
curl.exe "http://localhost:8000/api/v1/company/profile?symbols=META"
curl.exe "http://localhost:8000/api/v1/company/profile?symbols=META,MSFT"
curl.exe "http://localhost:8000/api/v1/company/summary?symbols=META"
curl.exe "http://localhost:8000/api/v1/company/summary?symbols=AAPL,META"
```

Manual calls require `MARKET_FMP_API_KEY`. Both endpoints return the SDK's
`companies`, `errors`, and `summary` unchanged. Profile retains all company
fields; summary contains `symbol`, `name`, `price`, `sector`, and `industry`.
Symbols are trimmed, uppercased, and deduplicated before enforcing the limit.
Missing or blank symbols return HTTP 400 with `No symbols provided`. More than
ten unique symbols return HTTP 400 with `10 symbol request limit exceeded`.
Empty entries or embedded whitespace are also rejected with HTTP 400.
Item failures, including all symbols not found, return HTTP 200 with item errors.
Operation-wide unavailability and timeouts use the central SDK exception handler
and return HTTP 503 and 504 respectively with a singular `error` object.

Company API validation errors explicitly include `retryable: false`. Under the
default REST policy, operation-wide provider outages (503) and timeouts (504)
also return `retryable: false`, overriding upstream retry hints. Per-symbol
errors retain their SDK retryability.
