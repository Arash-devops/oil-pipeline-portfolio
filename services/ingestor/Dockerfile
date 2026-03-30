FROM python:3.13-slim

# libpq5 is the runtime library required by psycopg[binary]
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install dependencies first for layer caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source
COPY . .

# Default command: full historical backfill.
# Override at runtime: docker compose run ingestor python -m src.main incremental
ENTRYPOINT ["python", "-m", "src.main"]
CMD ["backfill"]
