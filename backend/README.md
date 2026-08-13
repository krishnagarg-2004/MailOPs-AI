# MailOps AI Backend Service

The backend is built as a **Modular Monolith** using Python 3.14 and FastAPI.

## Directory Layout

```
backend/
├── pyproject.toml        # Authoritative package configuration and dependencies
├── README.md             # Developer overview
├── app/
│   ├── __init__.py
│   ├── main.py           # Application entry point and health check
│   └── core/             # Centralized settings and security
│       ├── __init__.py
│       └── config.py     # Pydantic BaseSettings management
└── tests/                # Test suite
    ├── __init__.py
    └── test_health.py    # Health endpoint verification test
```

## Local Development Execution

```bash
# Install package in editable mode
pip install -e .

# Run Pytest suite
pytest

# Launch local server
uvicorn app.main:app --reload
```
