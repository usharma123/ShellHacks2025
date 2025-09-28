# syntax=docker/dockerfile:1

FROM python:3.11-slim AS base

# Install system dependencies for scientific stack and build tools
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
       build-essential \
       git \
       curl \
       ca-certificates \
       libgomp1 \
       libatlas-base-dev \
       libopenblas-dev \
       liblapack-dev \
    && rm -rf /var/lib/apt/lists/*

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    UVICORN_WORKERS=2 \
    PORT=8080

WORKDIR /app

# Copy only Python backend first to leverage Docker layer caching
COPY VC_Analyst/requirements.txt /app/requirements.txt

RUN pip install --no-cache-dir -r /app/requirements.txt

# Copy backend code
COPY VC_Analyst /app/VC_Analyst

# Expose the port Cloud Run expects
EXPOSE 8080

# Default command: run FastAPI app (honor Cloud Run PORT env var)
CMD ["sh", "-c", "uvicorn VC_Analyst.api:app --host 0.0.0.0 --port ${PORT:-8080}"]


