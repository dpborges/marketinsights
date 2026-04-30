### Command to activate python virtual environment
source .venv/Scripts/activate

### Two commands to esnure test files use pytest with async support

#### using uv prefix
uv pip install -e ".[test]"

#### uv specific
uv sync --extra test

### Testing
#### How to run test for sector performance
##### From repo root
pytest tests/test_sector_performance_service.py
##### Alternatively
python -m pytest tests/test_sector_performance_service.py
#### How to run test for fmp_adapter
pytest tests/test_fmp_adapter.py -q