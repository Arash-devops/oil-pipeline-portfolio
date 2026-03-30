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

# DATA_DIR is the root for all Parquet output.
# The volume is mounted at /app/data so Parquet files persist beyond the container.
ENV DATA_DIR=/app/data

# Run the full Bronze→Silver→Gold pipeline.
# Override at runtime with: docker compose run lakehouse python -m src.main export
CMD ["python", "-m", "src.main", "full-pipeline"]
