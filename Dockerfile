# syntax=docker/dockerfile:1
# Agentic AI Engine — main application
# Two-stage build: builder installs deps into /opt/venv; runtime copies it in.

# ── Stage 1: dependency builder ───────────────────────────────────────────────
FROM python:3.14-slim AS builder

WORKDIR /build

RUN apt-get update && apt-get install -y --no-install-recommends gcc && \
    rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir uv

# Copy manifests first — changes to app code won't bust this layer
COPY pyproject.toml uv.lock ./

# Create isolated venv and install all production dependencies
RUN uv venv /opt/venv
ENV VIRTUAL_ENV=/opt/venv PATH="/opt/venv/bin:$PATH"
RUN uv pip install --no-cache .

# ── Stage 2: lean runtime image ───────────────────────────────────────────────
FROM python:3.14-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends curl && \
    rm -rf /var/lib/apt/lists/* && \
    useradd --create-home --uid 1000 appuser && \
    chown appuser:appuser /app

# Virtual environment from builder — owned by appuser so pip/uv can't be run at runtime
COPY --chown=appuser:appuser --from=builder /opt/venv /opt/venv

# Application source
COPY --chown=appuser:appuser app/ ./app/
COPY --chown=appuser:appuser agentic_ai_main.py ./

ENV VIRTUAL_ENV=/opt/venv \
    PATH="/opt/venv/bin:$PATH" \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

# Switch to non-root before the process starts — never run uvicorn as root
USER appuser

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=10s --start-period=15s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Single worker: session handler is a module-level singleton;
# Cloud Run scales horizontally via instances, not workers.
CMD ["uvicorn", "agentic_ai_main:app", \
     "--host", "0.0.0.0", \
     "--port", "8000", \
     "--workers", "1"]
