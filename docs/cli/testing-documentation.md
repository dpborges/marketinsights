### CLI Testing Documentation

## Run the sector summary CLI tests

From the project root, run:

```bash
pytest tests/cli/test_sector_summary_cli.py -q
```

## Run the full CLI-related test suite

```bash
pytest tests/test_cli_sector_service.py tests/cli/test_sector_summary_cli.py -q
```