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
