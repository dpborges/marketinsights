### Market Insights CLI

CLI for retrieving and displaying market data using Typer and Rich.

## Installation & Setup

Activate the project virtual environment:

```bash
source .venv/Scripts/activate
```

Ensure `typer` and `rich` are installed:

```bash
uv pip install typer rich
```

## Environment Configuration

The CLI reads API credentials from the `.env` file in the project root. Ensure your `.env` contains:

```
MARKET_FMP_API_KEY=<your-fmp-api-key>
```

If you see `403 Forbidden` or `402 Restricted Endpoint`, your FMP key is not authorized for the quote/batch-quote endpoint. Verify the API key and subscription plan with Financial Modeling Prep.

