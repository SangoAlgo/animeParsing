# ==========================================
# Multi-stage Dockerfile for AnimeParsing
# Stage 1: Build Frontend (Vite + React 19)
# Stage 2: Python Backend (SQLite FTS5 + JIT Player)
# ==========================================

# Stage 1: Build React Frontend
FROM node:20-alpine AS frontend-builder
WORKDIR /app/frontend

COPY frontend/package.json ./
RUN npm install

COPY frontend/ ./
RUN npm run build

# Stage 2: Python Runtime
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libxml2-dev \
    libxslt-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Python requirements
COPY backend/requirements.txt ./backend/
RUN pip install --no-cache-dir -r backend/requirements.txt

# Copy Backend, Data chunks, Scripts, and Frontend build
COPY backend/ ./backend/
COPY data/ ./data/
COPY scratch/ ./scratch/
COPY --from=frontend-builder /app/frontend/dist ./frontend/dist

# Unpack SQLite database from split chunks
RUN python backend/scripts/prepare_data.py restore || true

# Expose standard web port
ENV PORT=8000
ENV HOST=0.0.0.0
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
  CMD curl -f http://localhost:${PORT}/api/health || exit 1

# Start Server
CMD ["python", "backend/server.py"]
