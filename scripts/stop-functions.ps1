# Stop local Azure Functions + Azurite stack (does not remove SQL Server volume).
param(
    [string]$EnvFile = ".env.local"
)

$ErrorActionPreference = "Stop"

Write-Host "Stopping local Functions + Azurite..." -ForegroundColor Cyan

if (-not (Test-Path "docker-compose.yml")) {
    Write-Host "Error: docker-compose.yml not found in the current directory." -ForegroundColor Red
    exit 1
}

if (-not (Test-Path "docker-compose.functions.yml")) {
    Write-Host "Error: docker-compose.functions.yml not found in the current directory." -ForegroundColor Red
    exit 1
}

# Use the same project name so Docker Desktop groups are consistent,
# but do NOT include docker-compose.yml to avoid touching SQL Server.
docker compose -p frontend-cfa -f docker-compose.functions.yml --env-file $EnvFile down

if ($LASTEXITCODE -ne 0) {
    Write-Host "Failed to stop Functions stack." -ForegroundColor Red
    exit 1
}

Write-Host "Functions stack stopped." -ForegroundColor Green

