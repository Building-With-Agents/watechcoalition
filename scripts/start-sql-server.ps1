# Start SQL Server container using Docker Compose
param(
    [string]$EnvFile = ".env.docker"
)

$ErrorActionPreference = "Stop"

Write-Host "Starting SQL Server container..." -ForegroundColor Cyan

# Check if .env.docker exists
if (-not (Test-Path $EnvFile)) {
    Write-Host "Error: $EnvFile file not found!" -ForegroundColor Red
    Write-Host "Please run the setup script first to create the .env.docker file." -ForegroundColor Yellow
    exit 1
}

# Check if docker-compose.yml exists
if (-not (Test-Path "docker-compose.yml")) {
    Write-Host "Error: docker-compose.yml file not found!" -ForegroundColor Red
    exit 1
}

# Start the container
Write-Host "Starting container with docker-compose..." -ForegroundColor Cyan
docker-compose --env-file $EnvFile up -d

if ($LASTEXITCODE -eq 0) {
    Write-Host "SQL Server container started successfully!" -ForegroundColor Green
    Write-Host "Waiting for container to be healthy..." -ForegroundColor Cyan
    
    # Wait for container to be healthy
    & "$PSScriptRoot\wait-for-sql.ps1"
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "SQL Server is ready to accept connections!" -ForegroundColor Green
    }
} else {
    Write-Host "Failed to start SQL Server container" -ForegroundColor Red
    exit 1
}
