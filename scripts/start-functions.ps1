# Start local Azure Functions + Azurite using Docker Compose under the same project as SQL Server.
param(
    [string]$EnvFile = ".env"
)

$ErrorActionPreference = "Stop"

Write-Host "Starting local Functions + Azurite..." -ForegroundColor Cyan

if (-not (Test-Path $EnvFile)) {
    Write-Host "Error: $EnvFile not found." -ForegroundColor Red
    Write-Host "Create it by copying .env.example -> .env and adjusting values as needed." -ForegroundColor Yellow
    exit 1
}

if (-not (Test-Path "docker-compose.yml")) {
    Write-Host "Error: docker-compose.yml not found in the current directory." -ForegroundColor Red
    exit 1
}

if (-not (Test-Path "docker-compose.functions.yml")) {
    Write-Host "Error: docker-compose.functions.yml not found in the current directory." -ForegroundColor Red
    exit 1
}

# Use the same project name (`-p watechcoalition`) so Docker Desktop groups containers together
# with mssql-server, but do NOT include docker-compose.yml to avoid recreating SQL Server.
docker compose -p watechcoalition -f docker-compose.functions.yml --env-file $EnvFile up -d --build

if ($LASTEXITCODE -ne 0) {
    Write-Host "Failed to start Functions stack." -ForegroundColor Red
    exit 1
}

Write-Host "Functions stack started." -ForegroundColor Green
Write-Host "Try: http://localhost:7071/api/copilot" -ForegroundColor Yellow

