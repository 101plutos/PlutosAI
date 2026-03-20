FROM python:3.11-slim

WORKDIR /app

# Install system deps
RUN apt-get update && apt-get install -y --no-install-recommends curl && rm -rf /var/lib/apt/lists/*

# Copy shared module first (needed by pyproject.toml)
COPY ../../shared /app/shared

# Copy service code
COPY pyproject.toml .
COPY src/ src/

# Install service + dependencies
RUN pip install --no-cache-dir -e .

EXPOSE 8007

HEALTHCHECK --interval=30s --timeout=10s --retries=3 \
  CMD curl -f http://localhost:8007/health || exit 1

CMD ["uvicorn", "src.api:app", "--host", "0.0.0.0", "--port", "8007", "--workers", "2"]
