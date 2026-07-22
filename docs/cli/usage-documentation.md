## CLI Usage

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

### Display sector summary for all SPDR ETFs for a 2W period

```bash
python -m mi_sdk.cli.sector_service_cli sector summary
```

### Display sector summary for 1D and 2W periods

```bash
python -m mi_sdk.cli.sector_service_cli sector summary --periods 1D,2W
```

### Display sector summary for specific symbols and a 2W period

```bash
python -m mi_sdk.cli.sector_service_cli sector summary --periods 2W --symbols XLK,XLE,XLU
```

### Show help

```bash
python -m mi_sdk.cli.sector_service_cli --help
python -m mi_sdk.cli.sector_service_cli sector summary --help
```


