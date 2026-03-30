#!/usr/bin/env bash
# =============================================================================
# reset-db.sh
# Stops the PostgreSQL container, removes the named volume (destroying all data),
# and restarts so Docker re-runs all init scripts from scratch.
#
# Usage (from the database/ directory):
#   chmod +x scripts/reset-db.sh
#   ./scripts/reset-db.sh
# =============================================================================

set -euo pipefail

COMPOSE_FILE="$(dirname "$0")/../docker-compose.yml"
VOLUME_NAME="oil_warehouse_data"

echo "==================================================="
echo "  Oil Warehouse DB — Full Reset"
echo "==================================================="
echo ""
echo "WARNING: This will DELETE ALL DATA in the database."
read -r -p "Are you sure? Type 'yes' to continue: " confirmation

if [[ "$confirmation" != "yes" ]]; then
    echo "Aborted."
    exit 0
fi

echo ""
echo "▶ Step 1: Stopping containers..."
docker compose -f "$COMPOSE_FILE" down --remove-orphans

echo ""
echo "▶ Step 2: Removing data volume '$VOLUME_NAME'..."
if docker volume inspect "$VOLUME_NAME" > /dev/null 2>&1; then
    docker volume rm "$VOLUME_NAME"
    echo "   Volume removed."
else
    echo "   Volume not found — nothing to remove."
fi

echo ""
echo "▶ Step 3: Starting fresh (init scripts will run automatically)..."
docker compose -f "$COMPOSE_FILE" up -d

echo ""
echo "▶ Step 4: Waiting for PostgreSQL to be healthy..."
MAX_WAIT=60
SECONDS_WAITED=0
until docker compose -f "$COMPOSE_FILE" exec -T postgres \
      pg_isready -U arash -d oil_warehouse > /dev/null 2>&1; do
    if [[ $SECONDS_WAITED -ge $MAX_WAIT ]]; then
        echo "ERROR: PostgreSQL did not become ready within ${MAX_WAIT}s."
        exit 1
    fi
    printf "."
    sleep 2
    SECONDS_WAITED=$((SECONDS_WAITED + 2))
done

echo ""
echo ""
echo "==================================================="
echo "  Database is ready!"
echo ""
echo "  Connect with:"
echo "  psql postgresql://arash:warehouse_dev_2026@localhost:5432/oil_warehouse"
echo "==================================================="
