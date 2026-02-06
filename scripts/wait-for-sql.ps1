# Wait for SQL Server container to be ready and healthy
param(
    [int]$TimeoutSeconds = 300,
    [string]$ContainerName = "mssql-server"
)

Write-Host "Waiting for SQL Server container '$ContainerName' to be ready..." -ForegroundColor Cyan

$startTime = Get-Date
$elapsed = 0

while ($elapsed -lt $TimeoutSeconds) {
    $containerStatus = docker ps --filter "name=$ContainerName" --format "{{.Status}}" 2>$null
    
    if ($containerStatus -match "healthy|Up") {
        Write-Host "SQL Server container is ready!" -ForegroundColor Green
        return $true
    }
    
    Start-Sleep -Seconds 5
    $elapsed = ((Get-Date) - $startTime).TotalSeconds
    Write-Host "Still waiting... ($([math]::Round($elapsed))s elapsed)" -ForegroundColor Yellow
}

Write-Host "Timeout waiting for SQL Server container to be ready after $TimeoutSeconds seconds" -ForegroundColor Red
return $false
