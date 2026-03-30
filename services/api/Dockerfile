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

EXPOSE 8000

# Run uvicorn directly (avoids reload=True from run.py, which is dev-only).
# Binds to 0.0.0.0 so the port is reachable from outside the container.
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
