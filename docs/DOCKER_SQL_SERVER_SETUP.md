# SQL Server Docker Setup Guide

This guide explains how to set up SQL Server Developer edition in a Docker container. Use [ONBOARDING.md](../ONBOARDING.md) for full setup; after the container is running, seed the database with `npm run db:seed:anonymized` (fixtures in **prisma/mock-data/**).

## Prerequisites

- Docker Desktop installed and running

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

3. **Apply schema and seed database** — See [ONBOARDING.md](../ONBOARDING.md) for `npx prisma db push`, `npx prisma generate`, and `npm run db:seed:anonymized` (uses JSON fixtures in **prisma/mock-data/**).

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

### Step 3: Verify Database

You can verify SQL Server is running by connecting:

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

## Docker Compose Configuration

The `docker-compose.yml` file includes:

- **Image:** `mcr.microsoft.com/mssql/server:2025-latest` (Developer edition)
- **Port:** Mapped from container 1433 to host (configurable via `MSSQL_PORT`)
- **Volumes:**
  - `mssql_data` - Persistent storage for database files
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

## Security Notes

- The `.env.docker` file contains sensitive credentials
- Do not commit `.env.docker` to version control (it should be in `.gitignore`)
- Use strong, unique passwords for production environments
- The Developer edition is free but should not be used in production
- Consider using Docker secrets or environment variable management for production deployments
