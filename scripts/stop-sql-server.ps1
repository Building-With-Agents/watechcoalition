# Stop SQL Server container using Docker Compose
param(
    [string]$EnvFile = ".env.docker"
)

Write-Host "Stopping SQL Server container..." -ForegroundColor Cyan

# Check if docker-compose.yml exists
if (-not (Test-Path "docker-compose.yml")) {
    Write-Host "Error: docker-compose.yml file not found!" -ForegroundColor Red
    exit 1
}

# Stop the container
docker-compose --env-file $EnvFile down

if ($LASTEXITCODE -eq 0) {
    Write-Host "SQL Server container stopped successfully!" -ForegroundColor Green
} else {
    Write-Host "Failed to stop SQL Server container" -ForegroundColor Red
    exit 1
}
