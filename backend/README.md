# FastAPI Backend Foundation

Structured FastAPI backend with API versioning, structured logging, centralized error handling, and environment configuration.

## Development

```bash
# Install dependencies with uv
uv sync --all-extras

# Run development server
uv run uvicorn app.main:app --reload --port 8000

# Run tests
uv run pytest
```
