# syntax=docker/dockerfile:1
FROM python:3.14-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# System deps: cryptography build tools, pdf2image (poppler), tesseract-ocr, get-pip for curl fallback
RUN apt-get update && apt-get install -y --no-install-recommends \
        build-essential \
        libpq-dev \
        python3-dev \
        tesseract-ocr \
        poppler-utils \
        libjpeg62 \
        libxml2-dev \
        libxslt1-dev \
        zlib1g-dev \
        curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python dependencies first (better layer caching)
COPY backend/pyproject.toml ./
RUN pip install --upgrade pip \
    && pip install -e .[dev]

# Copy application code
COPY backend/ ./backend/
COPY alembic.ini ./
COPY database ./database

# Backend listens on port 8000
EXPOSE 8000

# Auto-run Alembic migrations happen inside app/main.py lifespan.
# Start uvicorn with reload for local development.
CMD ["uvicorn", "backend.app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
