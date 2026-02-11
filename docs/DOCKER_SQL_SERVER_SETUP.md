# SQL Server Docker Setup Guide

This guide explains how to set up SQL Server Developer edition in a Docker container. **New developers** should follow [ONBOARDING.md](../ONBOARDING.md) and use `npm run db:seed:anonymized` with existing fixtures—no BACPAC import needed. **BACPAC import** is optional and used by maintainers when refreshing anonymized fixtures (see [REFRESH_ANONYMIZED_FIXTURES.md](REFRESH_ANONYMIZED_FIXTURES.md)).

## Prerequisites

- Docker Desktop installed and running
- PowerShell (for Windows)
- SqlPackage.exe installed (see installation instructions below)

## Quick Start

1. **Configure Environment Variables**
   - Copy `.env.docker.example` to `.env.docker`
   - Edit `.env.docker` and set your values:
     - `MSSQL_SA_PASSWORD` - Strong password (min 8 chars, must include uppercase, lowercase, number, special char)
     - `MSSQL_DATABASE` - Database name (default: talent_finder)
     - `MSSQL_PORT` - Port mapping (default: 1433)

2. **Start SQL Server Container**

   **Windows:**
   ```powershell
   .\scripts\start-sql-server.ps1
   ```

   **Linux / macOS:**
   ```bash
   docker compose --env-file .env.docker up -d
   ```

3. **Import BACPAC File** (optional, for maintainers refreshing fixtures)

   **Windows only** (requires SqlPackage.exe):
   ```powershell
   .\scripts\import-bacpac.ps1
   ```

## Detailed Steps

### Step 1: Environment Configuration

Create a `.env.docker` file in the repository root with the following variables:

```env
# SQL Server SA (System Administrator) password
# Must be at least 8 characters and contain uppercase, lowercase, numbers, and special characters
MSSQL_SA_PASSWORD=YourComplex!P4ssw0rd

# Database name (default: talent_finder)
MSSQL_DATABASE=talent_finder

# Port mapping for SQL Server (default: 1433)
MSSQL_PORT=1433
```

**Important:** The SA password must meet SQL Server's complexity requirements:
- At least 8 characters long
- Contains uppercase letters
- Contains lowercase letters
- Contains numbers
- Contains special characters

### Step 2: Start SQL Server Container

Use the provided PowerShell script to start the container:

```powershell
.\scripts\start-sql-server.ps1
```

This script will:
- Check for required files
- Start the SQL Server container using Docker Compose
- Wait for the container to be healthy
- Confirm when SQL Server is ready

Alternatively, use Docker Compose directly (all platforms):

```bash
docker compose --env-file .env.docker up -d
```

### Step 3: Install SqlPackage.exe (if not already installed)

The BACPAC import requires SqlPackage.exe. Install it using one of these methods:

**Option 1: Download from Microsoft**
- Visit: https://aka.ms/sqlpackage
- Download the Windows x64 version
- Extract and add to your PATH, or note the location

**Option 2: Install via winget**
```powershell
winget install Microsoft.SqlPackage
```

**Option 3: Install SQL Server Data Tools (SSDT)**
- SSDT includes SqlPackage.exe
- Download from: https://aka.ms/ssdt

The import script will automatically search common installation locations.

### Step 4: Import BACPAC File

Once SQL Server is running and SqlPackage.exe is installed, import the database:

```powershell
.\scripts\import-bacpac.ps1
```

This script will:
- Verify SQL Server container is ready
- Locate SqlPackage.exe
- Import `prod-backup-20251117.bacpac` into the database
- Provide progress feedback

**Note:** The import process may take several minutes depending on the database size.

### Step 5: Verify Database

You can verify the database was imported successfully by connecting to SQL Server:

```powershell
# Using sqlcmd (if installed)
sqlcmd -S localhost,1433 -U sa -P YourPassword -Q "SELECT name FROM sys.databases"
```

Or use Azure Data Studio, SQL Server Management Studio, or any SQL client.

## Available Scripts

### start-sql-server.ps1
Starts the SQL Server Docker container and waits for it to be healthy.

**Usage:**
```powershell
.\scripts\start-sql-server.ps1
```

**Options:**
- `-EnvFile` - Specify custom env file (default: `.env.docker`)

### stop-sql-server.ps1
Stops the SQL Server Docker container.

**Usage:**
```powershell
.\scripts\stop-sql-server.ps1
```

**Options:**
- `-EnvFile` - Specify custom env file (default: `.env.docker`)

### wait-for-sql.ps1
Waits for the SQL Server container to be ready and healthy.

**Usage:**
```powershell
.\scripts\wait-for-sql.ps1
```

**Options:**
- `-TimeoutSeconds` - Maximum time to wait (default: 300)
- `-ContainerName` - Container name (default: `mssql-server`)

### import-bacpac.ps1
Imports a BACPAC file into the SQL Server database.

**Usage:**
```powershell
.\scripts\import-bacpac.ps1
```

**Options:**
- `-BacpacPath` - Path to BACPAC file (default: `prod-backup-20251117.bacpac`)
- `-EnvFile` - Path to env file (default: `.env.docker`)
- `-SkipDrop` - Skip dropping existing database if it exists (not recommended)

**Note:** The script will automatically check if the target database exists and drop it before importing. This ensures a clean import. Use `-SkipDrop` only if you want to preserve the existing database (import will fail if database contains objects).

## Connection Strings

After setup, update your application's `.env` file to connect to the Docker SQL Server:

```env
# MSSQL Connection Configuration
MSSQL_USER=SA
MSSQL_PASSWORD=YourComplex!P4ssw0rd
MSSQL_HOST=localhost
MSSQL_PORT=1433
MSSQL_DATABASE=talent_finder

# Connection String for MSSQL
MSSQL_CONNECTION_STRING=mssql://SA:YourComplex!P4ssw0rd@localhost:1433/talent_finder
DATABASE_URL="sqlserver://localhost:1433;database=talent_finder;user=SA;password=YourComplex!P4ssw0rd;encrypt=false;trustServerCertificate=true"
```

## DB Anonymization (PII)

If you imported a production BACPAC locally, you can anonymize PII in your Docker DB using:

- [`docs/DB_ANONYMIZATION.md`](docs/DB_ANONYMIZATION.md)

## Docker Compose Configuration

The `docker-compose.yml` file includes:

- **Image:** `mcr.microsoft.com/mssql/server:2025-latest` (Developer edition)
- **Port:** Mapped from container 1433 to host (configurable via `MSSQL_PORT`)
- **Volumes:**
  - `mssql_data` - Persistent storage for database files
  - BACPAC file mounted as read-only
- **Health Check:** Automatically verifies SQL Server is ready
- **Restart Policy:** `unless-stopped`

## Troubleshooting

### Container won't start

**Check Docker is running:**
```powershell
docker ps
```

**Check container logs:**
```powershell
docker logs mssql-server
```

**Verify environment variables:**
- Ensure `.env.docker` exists and has valid values
- Password must meet complexity requirements

### SqlPackage.exe not found

The import script searches common installation locations. If not found:

1. Verify SqlPackage.exe is installed
2. Add SqlPackage.exe location to your PATH
3. Or specify the full path in the import script

**Common locations:**
- `C:\Program Files\Microsoft SQL Server\160\DAC\bin\SqlPackage.exe`
- `C:\Program Files (x86)\Microsoft SQL Server\160\DAC\bin\SqlPackage.exe`

### Import fails with timeout

Large databases may take time to import. The script sets `CommandTimeout=0` to allow unlimited time. If issues persist:

1. Check SQL Server container is healthy: `docker ps`
2. Verify sufficient disk space
3. Check container logs: `docker logs mssql-server`

### Connection refused errors

**Verify container is running:**
```powershell
docker ps --filter "name=mssql-server"
```

**Check port is not in use:**

Windows:
```powershell
netstat -an | findstr :1433
```

Linux / macOS:
```bash
lsof -i :1433
# or: ss -tlnp | grep 1433
```

**Verify health check:**
```powershell
docker inspect mssql-server --format='{{.State.Health.Status}}'
```

### Password complexity errors

SQL Server requires strong passwords. Ensure your `MSSQL_SA_PASSWORD` includes:
- At least 8 characters
- Uppercase letters
- Lowercase letters
- Numbers
- Special characters (!, @, #, $, etc.)

### Database already exists error

The import script automatically handles this by dropping the existing database before import. If you see this error:

```
Error SQL71659: Data cannot be imported into target because it contains one or more user objects.
```

This means the automatic drop failed. You can manually drop the database:

**Option 1: Use the import script (automatic)**
The script will automatically detect and drop the database. Just run:
```powershell
.\scripts\import-bacpac.ps1
```

**Option 2: Manually drop via Docker**
```powershell
docker exec mssql-server /opt/mssql-tools18/bin/sqlcmd -S localhost -U sa -P YourPassword -d master -C -Q "ALTER DATABASE [talent_finder] SET SINGLE_USER WITH ROLLBACK IMMEDIATE; DROP DATABASE [talent_finder];"
```

**Option 3: Use a different database name**
Change `MSSQL_DATABASE` in `.env.docker` to a different name.

## Data Persistence

Database data is stored in a Docker volume named `mssql_data`. This means:

- Data persists across container restarts
- Data persists even if the container is removed (unless you use `docker-compose down -v`)
- To start fresh, remove the volume: `docker volume rm <project>_mssql_data` (project name may vary by directory, e.g. `frontend-cfa_mssql_data`)

## Stopping and Cleaning Up

**Stop the container:**

Windows:
```powershell
.\scripts\stop-sql-server.ps1
```

Linux / macOS:
```bash
docker compose --env-file .env.docker down
```

**Stop and remove container:**
```bash
docker compose --env-file .env.docker down
```

**Stop and remove container + volumes (⚠️ deletes database):**
```bash
docker compose --env-file .env.docker down -v
```

## Additional Resources

- [SQL Server on Linux Documentation](https://docs.microsoft.com/en-us/sql/linux/)
- [Docker Compose Documentation](https://docs.docker.com/compose/)
- [SqlPackage.exe Documentation](https://docs.microsoft.com/en-us/sql/tools/sqlpackage)
- [BACPAC Import/Export](https://docs.microsoft.com/en-us/sql/relational-databases/data-tier-applications/data-tier-applications)

## Security Notes

- The `.env.docker` file contains sensitive credentials
- Do not commit `.env.docker` to version control (it should be in `.gitignore`)
- Use strong, unique passwords for production environments
- The Developer edition is free but should not be used in production
- Consider using Docker secrets or environment variable management for production deployments
