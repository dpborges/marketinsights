### Command to activate python virtual environment
source .venv/Scripts/activate

### Two commands to esnure test files use pytest with async support

#### using uv prefix
uv pip install -e ".[test]"

#### uv specific
uv sync --extra test