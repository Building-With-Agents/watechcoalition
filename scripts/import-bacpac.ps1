# Import BACPAC file into SQL Server Docker container
param(
    [string]$BacpacPath = "prod-backup-20251117.bacpac",
    [string]$EnvFile = ".env.docker",
    [switch]$SkipDrop = $false
)

$ErrorActionPreference = "Stop"

Write-Host "BACPAC Import Script" -ForegroundColor Cyan
Write-Host "====================" -ForegroundColor Cyan

# Check if .env.docker exists
if (-not (Test-Path $EnvFile)) {
    Write-Host "Error: $EnvFile file not found!" -ForegroundColor Red
    Write-Host "Please run the setup script first to create the .env.docker file." -ForegroundColor Yellow
    exit 1
}

# Load environment variables from .env.docker
$envVars = @{}
Get-Content $EnvFile | ForEach-Object {
    if ($_ -match '^\s*([^#][^=]+)=(.*)$') {
        $key = $matches[1].Trim()
        $value = $matches[2].Trim()
        $envVars[$key] = $value
    }
}

$saPassword = $envVars['MSSQL_SA_PASSWORD']
$database = $envVars['MSSQL_DATABASE']
$port = $envVars['MSSQL_PORT']

if (-not $saPassword) {
    Write-Host "Error: MSSQL_SA_PASSWORD not found in $EnvFile" -ForegroundColor Red
    exit 1
}

if (-not $database) {
    $database = "talent_finder"
    Write-Host "Warning: MSSQL_DATABASE not found, using default: $database" -ForegroundColor Yellow
}

if (-not $port) {
    $port = "1433"
    Write-Host "Warning: MSSQL_PORT not found, using default: $port" -ForegroundColor Yellow
}

# Check if bacpac file exists
if (-not (Test-Path $BacpacPath)) {
    Write-Host "Error: BACPAC file not found at: $BacpacPath" -ForegroundColor Red
    exit 1
}

Write-Host "BACPAC file: $BacpacPath" -ForegroundColor Green
Write-Host "Database: $database" -ForegroundColor Green
Write-Host "Port: $port" -ForegroundColor Green

# Wait for SQL Server to be ready
Write-Host "`nChecking if SQL Server container is ready..." -ForegroundColor Cyan
& "$PSScriptRoot\wait-for-sql.ps1"

if ($LASTEXITCODE -ne 0) {
    Write-Host "Error: SQL Server container is not ready. Please start it first." -ForegroundColor Red
    Write-Host "Run: .\scripts\start-sql-server.ps1" -ForegroundColor Yellow
    exit 1
}

# Find SqlPackage.exe
Write-Host "`nLooking for SqlPackage.exe..." -ForegroundColor Cyan

# Refresh PATH to include newly installed programs
$env:Path = [System.Environment]::GetEnvironmentVariable("Path", "Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path", "User")

$sqlPackagePaths = @(
    "${env:ProgramFiles}\Microsoft SQL Server\170\DAC\bin\SqlPackage.exe",
    "${env:ProgramFiles(x86)}\Microsoft SQL Server\170\DAC\bin\SqlPackage.exe",
    "${env:ProgramFiles}\Microsoft SQL Server\160\DAC\bin\SqlPackage.exe",
    "${env:ProgramFiles(x86)}\Microsoft SQL Server\160\DAC\bin\SqlPackage.exe",
    "${env:ProgramFiles}\Microsoft SQL Server\150\DAC\bin\SqlPackage.exe",
    "${env:ProgramFiles(x86)}\Microsoft SQL Server\150\DAC\bin\SqlPackage.exe",
    "${env:ProgramFiles}\Microsoft SQL Server\140\DAC\bin\SqlPackage.exe",
    "${env:ProgramFiles(x86)}\Microsoft SQL Server\140\DAC\bin\SqlPackage.exe",
    "${env:LOCALAPPDATA}\Microsoft\WindowsApps\sqlpackage.exe"
)

$sqlPackage = $null
foreach ($path in $sqlPackagePaths) {
    if (Test-Path $path) {
        $sqlPackage = $path
        Write-Host "Found SqlPackage.exe at: $path" -ForegroundColor Green
        break
    }
}

# Also check PATH (including refreshed PATH)
if (-not $sqlPackage) {
    $sqlPackageCmd = Get-Command sqlpackage -ErrorAction SilentlyContinue
    if ($sqlPackageCmd) {
        $sqlPackage = $sqlPackageCmd.Source
        Write-Host "Found sqlpackage in PATH: $sqlPackage" -ForegroundColor Green
    } else {
        $sqlPackageCmd = Get-Command SqlPackage.exe -ErrorAction SilentlyContinue
        if ($sqlPackageCmd) {
            $sqlPackage = $sqlPackageCmd.Source
            Write-Host "Found SqlPackage.exe in PATH: $sqlPackage" -ForegroundColor Green
        }
    }
}

if (-not $sqlPackage) {
    Write-Host "Error: SqlPackage.exe not found!" -ForegroundColor Red
    Write-Host "`nPlease install SqlPackage.exe from one of the following:" -ForegroundColor Yellow
    Write-Host "1. Download from: https://aka.ms/sqlpackage" -ForegroundColor Yellow
    Write-Host "2. Install SQL Server Data Tools (SSDT)" -ForegroundColor Yellow
    Write-Host "3. Install via winget: winget install Microsoft.SqlPackage" -ForegroundColor Yellow
    Write-Host "`nAfter installation, run this script again." -ForegroundColor Yellow
    exit 1
}

# Drop database if it exists (docker-compose creates empty DB, but we need to drop if it has objects from previous failed import)
$containerName = "mssql-server"

if (-not $SkipDrop) {
    Write-Host "`nEnsuring database '$database' is clean for import..." -ForegroundColor Cyan
    
    # Simple drop query - docker-compose will recreate empty DB if needed
    $dropQuery = @"
IF EXISTS (SELECT name FROM sys.databases WHERE name = '$database')
BEGIN
    ALTER DATABASE [$database] SET SINGLE_USER WITH ROLLBACK IMMEDIATE;
    DROP DATABASE [$database];
END
"@
    
    try {
        $dropOutput = docker exec $containerName /opt/mssql-tools18/bin/sqlcmd -S localhost -U sa -P "$saPassword" -d master -C -Q "$dropQuery" -h -1 2>&1 | Out-Null
        Start-Sleep -Seconds 1  # Brief pause for cleanup
        
        # Wait a moment to ensure drop is complete
        Start-Sleep -Seconds 2
        
        # Don't recreate the database - let SqlPackage create it fresh
        # This ensures SqlPackage sees it as a truly new, empty database
        Write-Host "Database dropped. SqlPackage will create it during import." -ForegroundColor Green
    } catch {
        Write-Host "Note: Could not drop database (may not exist). Proceeding with import..." -ForegroundColor Yellow
    }
} else {
    Write-Host "-SkipDrop specified. Skipping database drop." -ForegroundColor Yellow
}

# Build connection string for import
# Connect to the target database directly - we've ensured it's empty
$connectionString = "Server=localhost,$port;Database=$database;User Id=sa;Password=$saPassword;TrustServerCertificate=True;Encrypt=True;"

Write-Host "`nImporting BACPAC file..." -ForegroundColor Cyan
Write-Host "This may take several minutes depending on the database size..." -ForegroundColor Yellow

# Import the bacpac
# SqlPackage will create the database if it doesn't exist
# We specify the database name in the connection string using Initial Catalog
$targetConnectionString = "Server=localhost,$port;Database=$database;User Id=sa;Password=$saPassword;TrustServerCertificate=True;Encrypt=True;"
$importArgs = @(
    "/Action:Import",
    "/SourceFile:`"$((Get-Item $BacpacPath).FullName)`"",
    "/TargetConnectionString:`"$targetConnectionString`"",
    "/p:CommandTimeout=0"
)

try {
    & $sqlPackage $importArgs
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "`nBACPAC import completed successfully!" -ForegroundColor Green
        Write-Host "Database '$database' is now available at localhost:$port" -ForegroundColor Green
    } else {
        Write-Host "`nBACPAC import failed with exit code: $LASTEXITCODE" -ForegroundColor Red
        exit 1
    }
} catch {
    Write-Host "`nError during BACPAC import: $_" -ForegroundColor Red
    exit 1
}
