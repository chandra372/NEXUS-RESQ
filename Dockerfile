# ==============================================================================
# NEXUS RESQ - Production Multi-Stage Container Image
# Unified Frontend (React 19 / Vite / Tailwind) + Backend (FastAPI / AI Pipeline)
# ==============================================================================

# ------------------------------------------------------------------------------
# Stage 1: Build Frontend SPA
# ------------------------------------------------------------------------------
FROM node:20-alpine AS frontend-builder
WORKDIR /app/frontend

# Install dependencies using clean install
COPY nexus-resq/frontend/package*.json ./
RUN npm ci

# Copy source and build distribution
COPY nexus-resq/frontend ./
RUN npm run build

# ------------------------------------------------------------------------------
# Stage 2: Production Python Runtime & Static Assets
# ------------------------------------------------------------------------------
FROM python:3.10-slim

# Prevent pyc generation and ensure realtime terminal logging
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    DEBIAN_FRONTEND=noninteractive \
    PORT=8000 \
    DATASET_PATH=/app/nexus-resq/large_emergency_dataset

WORKDIR /app

# Install system dependencies for audio decoding, C-extensions, and health checks
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    ffmpeg \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Python requirements
COPY nexus-resq/backend/requirements.txt ./nexus-resq/backend/requirements.txt
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r ./nexus-resq/backend/requirements.txt

# Copy backend source code
COPY nexus-resq/backend ./nexus-resq/backend

# Copy emergency dataset (audio, ground truth, social/sms feeds)
COPY nexus-resq/large_emergency_dataset ./nexus-resq/large_emergency_dataset

# Copy compiled frontend from Stage 1 to the location expected by FastAPI
COPY --from=frontend-builder /app/frontend/dist ./nexus-resq/frontend/dist

# Expose HTTP port
EXPOSE 8000

# Container healthcheck
HEALTHCHECK --interval=30s --timeout=5s --start-period=15s --retries=3 \
    CMD curl -f http://localhost:${PORT:-8000}/api/health || exit 1

# Workdir set to backend for python module resolution
WORKDIR /app/nexus-resq/backend

# Default entrypoint / startup command compatible with Cloud Run, App Runner, Render, Railway, etc.
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
