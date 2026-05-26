Context:
- Architecture:           docs/sdk-architecture.md
- SDK Design:             docs/sdk-architecture.md
- Exception Handling:     docs/exception-handling.md
- CLI tools of choice:    Typer and Rich
- testing documentation:  /tests/testing documentation.md 

Tasks: 
You are a CLI developer.  Create a CLI sector performance service that returns sector performance for SPDR ETF tickers: XLK, XLF, XLV, XLY, XLI, XLC, XLE, XLU, XLP, XLB, XLRE

Generate Pytest for the sector performance service CLI

Update testing documentation.md with how to test the sector performance cli located in  /tests/testing documentation.md file

Update /docs/cli-usage-documentation.md with usage instructions on how to use the CLI

Constraints: Create CLI using the SDK service found in this path: src/mi_sdk/services/sector_performance_service.py

Leverage the same SDK exception hierarchy for the CLI.

Use API KEY found in the .env file. The property name is MARKET_FMP_API_KEY


