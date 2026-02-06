const { DefaultAzureCredential } = require("@azure/identity");
const { SecretClient } = require("@azure/keyvault-secrets");
require("dotenv").config();

const getSecret = async (secretName) => {
  const vaultName = process.env.KEY_VAULT_NAME;
  const url = `https://${vaultName}.vault.azure.net`;

  const credential = new DefaultAzureCredential();
  const client = new SecretClient(url, credential);

  const retrievedSecret = await client.getSecret(secretName);
  return retrievedSecret.value;
};

const loadConfig = async () => {
  const config = {
    mssqlUser: process.env.MSSQL_USER,
    mssqlHost: process.env.MSSQL_HOST,
    mssqlPort: process.env.MSSQL_PORT,
    mssqlDatabase: process.env.MSSQL_DATABASE,
    nextAuthUrl: process.env.NEXTAUTH_URL,
    authTrustHost: process.env.AUTH_TRUST_HOST,
  };

  // Fetch sensitive variables from Azure Key Vault
  config.mssqlPassword = await getSecret("MSSQL_PASSWORD");
  config.authSecret = await getSecret("AUTH_SECRET");
  config.authGithubId = await getSecret("AUTH_GITHUB_ID");
  config.authGithubSecret = await getSecret("AUTH_GITHUB_SECRET");
  config.nextAuthSecret = await getSecret("NEXTAUTH_SECRET");
  config.nextAuthSalt = await getSecret("NEXTAUTH_SALT");

  // Construct connection strings with the sensitive information
  config.mssqlConnectionString = `mssql://SA:${config.mssqlPassword}@${config.mssqlHost}:${config.mssqlPort}/${config.mssqlDatabase}`;
  config.databaseUrl = `sqlserver://${config.mssqlHost}:${config.mssqlPort};database=${config.mssqlDatabase};user=SA;password=${config.mssqlPassword};encrypt=false;trustServerCertificate=true`;

  return config;
};

module.exports = loadConfig;
