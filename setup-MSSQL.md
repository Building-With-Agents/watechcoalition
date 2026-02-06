# If you're running your own MSSQL Server, follow these steps.

Your .env file should look similar to this:

```env
# MSSQL Connection Configuration
MSSQL_USER=SA
MSSQL_PASSWORD=YourComplex!P4ssw0rd
MSSQL_HOST=localhost
MSSQL_PORT=1433
MSSQL_DATABASE=CoreDB

# Connection String for MSSQL (if using libraries that accept connection strings)
MSSQL_CONNECTION_STRING=mssql://SA:YourComplex!P4ssw0rd@localhost:1433/CoreDB
DATABASE_URL="sqlserver://localhost:1433;database=CoreDB;user=SA;password=YourComplex!P4ssw0rd;encrypt=false;trustServerCertificate=true"

# Generate this secret by running the following command: openssl rand -base64 32
AUTH_SECRET=<your generated base64 auth secret>
```

Don't forget to generate your Base64 Auth Secret and save!

### 4. Setting Up MSSQL Server

#### 4.1. Install MSSQL Server

Follow the
official [installation guide for SQL Server](https://docs.microsoft.com/en-us/sql/linux/quickstart-install-connect-ubuntu)
to install MSSQL Server on your system.

#### 4.2. Start MSSQL Server

Start the MSSQL Server service:

```bash
sudo systemctl start mssql-server
```

Enable MSSQL Server to start on boot:

```bash
sudo systemctl enable mssql-server
```

#### 4.3. Configure MSSQL Server

Run the setup command and follow the prompts to configure your MSSQL Server:

```bash
sudo /opt/mssql/bin/mssql-conf setup
```

#### 4.4. Install MSSQL Tools

To interact with your MSSQL Server instance, install the MSSQL tools:

```bash
curl -o- https://packages.microsoft.com/keys/microsoft.asc | sudo apt-key add -
sudo curl -o /etc/apt/sources.list.d/mssql-tools.list https://packages.microsoft.com/config/ubuntu/20.04/prod.list
sudo apt-get update
sudo apt-get install mssql-tools unixodbc-dev
```

#### 4.5. Connect to MSSQL Server

Use `sqlcmd` to connect to your MSSQL Server instance:

```bash
sqlcmd -S localhost -U SA -P YourComplex!P4ssw0rd
```

#### 4.6. Create the Database

Once connected, create your database:

```sql
CREATE
DATABASE CoreDB;
GO
```

### 5. Set Up the Database

Generate Prisma client and push the schema to your MSSQL database:

```bash
npx prisma generate
npx prisma db push
```

### 6. Seed the Database

To seed the database with initial data, run:

```bash
npm run seed
```
