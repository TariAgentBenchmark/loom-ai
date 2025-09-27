# LoomAI Backend

FastAPI backend powered by [uv](https://github.com/astral-sh/uv) for dependency management.

## Getting started

```bash
# create a virtual environment managed by uv
uv venv

# activate the environment (macOS / Linux)
source .venv/bin/activate

# install project dependencies declared in pyproject.toml
uv sync

# run the dev server with auto-reload via uvicorn
uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Alternatively use the packaged console script:

```bash
uv run loomai-api
```

## Running tests

```bash
uv run pytest
```
