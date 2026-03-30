# =============================================================================
# reset-db.ps1
# Stops the PostgreSQL container, removes the named volume (destroying all data),
# and restarts so Docker re-runs all init scripts from scratch.
#
# Usage (from the database\ directory):
#   .\scripts\reset-db.ps1
# =============================================================================

# Do NOT use "Stop" here - external docker commands return non-zero exit codes
# for normal conditions (e.g. volume not found) and we need to inspect $LASTEXITCODE
# rather than catching thrown exceptions.
$ErrorActionPreference = "Continue"

$ComposeFile = Join-Path $PSScriptRoot "..\docker-compose.yml"

Write-Host "===================================================" -ForegroundColor Cyan
Write-Host "  Oil Warehouse DB - Full Reset"                     -ForegroundColor Cyan
Write-Host "===================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "WARNING: This will DELETE ALL DATA in the database." -ForegroundColor Yellow
$confirmation = Read-Host "Are you sure? Type 'yes' to continue"

if ($confirmation -ne "yes") {
    Write-Host "Aborted." -ForegroundColor Red
    exit 0
}

# ---------------------------------------------------------------------------
# Step 1: Stop containers AND remove named volumes in one command.
# The -v flag removes volumes declared in the compose file, which is
# equivalent to the previous two-step stop + manual volume-rm approach,
# but avoids the $LASTEXITCODE ambiguity of 'docker volume inspect'.
# ---------------------------------------------------------------------------
Write-Host ""
Write-Host "[Step 1] Stopping containers and removing volume..." -ForegroundColor Green
docker compose -f $ComposeFile down -v --remove-orphans
if ($LASTEXITCODE -ne 0) {
    Write-Host "ERROR: 'docker compose down' failed (exit $LASTEXITCODE)." -ForegroundColor Red
    exit 1
}
Write-Host "        Container and volume removed." -ForegroundColor Green

# ---------------------------------------------------------------------------
# Step 2: Start fresh.
# --wait blocks until the container's healthcheck reports healthy,
# so we don't need a manual polling loop.
# --timeout sets the upper bound in seconds before --wait gives up.
# ---------------------------------------------------------------------------
Write-Host ""
Write-Host "[Step 2] Starting fresh and waiting for healthy status..." -ForegroundColor Green
Write-Host "         (init scripts run automatically - this takes ~30s)" -ForegroundColor DarkGray
docker compose -f $ComposeFile up -d --wait --timeout 120
if ($LASTEXITCODE -ne 0) {
    Write-Host ""
    Write-Host "ERROR: Container did not become healthy within 120s." -ForegroundColor Red
    Write-Host "       Check logs with: docker logs oil_warehouse_db"  -ForegroundColor Yellow
    exit 1
}

Write-Host ""
Write-Host "===================================================" -ForegroundColor Cyan
Write-Host "  Database is ready!"                                -ForegroundColor Green
Write-Host ""
Write-Host "  Connect with:"                                     -ForegroundColor White
Write-Host "  psql postgresql://arash:warehouse_dev_2026@localhost:5432/oil_warehouse" -ForegroundColor Yellow
Write-Host "===================================================" -ForegroundColor Cyan
