### Market Insights CLI

CLI for retrieving and displaying sector performance data using Typer and Rich.

### To view md files in HTML, click within the file and hit Ctrl + Shift + V

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

## Usage

### Display all default SPDR sector ETF tickers

```bash
python -m mi_sdk.cli.sector_service_cli
```

### Display specific sector ETF tickers

```bash
python -m mi_sdk.cli.sector_service_cli --symbols XLK,XLF,XLV
```

Supported SPDR ETFs:
- **XLK** – Technology
- **XLF** – Financial Services
- **XLV** – Healthcare
- **XLY** – Consumer Discretionary
- **XLI** – Industrials
- **XLC** – Communication Services
- **XLE** – Energy
- **XLU** – Utilities
- **XLP** – Consumer Staples
- **XLB** – Materials
- **XLRE** – Real Estate

### Show help

```bash
python -m mi_sdk.cli.sector_service_cli --help
```

## Testing

Run the CLI tests:

```bash
pytest tests/test_cli_sector_service.py -q
```
