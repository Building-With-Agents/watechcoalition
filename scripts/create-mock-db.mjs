import "dotenv/config";
import sql from "mssql";

function parseArgs(argv) {
  const args = argv.slice(2);
  const get = (flag, fallback = null) => {
    const i = args.indexOf(flag);
    return i === -1 ? fallback : args[i + 1] ?? fallback;
  };
  return {
    db: get("--db", "talent_finder_mock"),
  };
}

function toBool(v, def = false) {
  if (v === undefined || v === null) return def;
  const s = String(v).trim().toLowerCase();
  if (["1", "true", "yes", "y"].includes(s)) return true;
  if (["0", "false", "no", "n"].includes(s)) return false;
  return def;
}

function parseAdoStyleSqlServerString(conn) {
  const [prefix, ...rest] = conn.split(";");
  const prefixMatch = prefix.match(/^sqlserver:\/\/([^:;]+)(?::(\d+))?$/i);
  if (!prefixMatch) return null;

  const server = prefixMatch[1];
  const port = prefixMatch[2] ? Number(prefixMatch[2]) : 1433;
  const kv = {};
  for (const part of rest) {
    const idx = part.indexOf("=");
    if (idx === -1) continue;
    const key = part.slice(0, idx).trim().toLowerCase();
    const value = part.slice(idx + 1).trim();
    kv[key] = value;
  }

  const user = kv["user"] || kv["user id"] || kv["uid"];
  const password = kv["password"] || kv["pwd"];
  const encrypt = toBool(kv["encrypt"], false);
  const trustServerCertificate = toBool(kv["trustservercertificate"], true);

  if (!server || !user || !password) return null;
  return { server, port, user, password, options: { encrypt, trustServerCertificate } };
}

function parseMssqlUrlString(conn) {
  try {
    const u = new URL(conn);
    if (u.protocol !== "mssql:") return null;
    const server = u.hostname;
    const port = u.port ? Number(u.port) : 1433;
    const user = decodeURIComponent(u.username);
    const password = decodeURIComponent(u.password);
    const encrypt = toBool(u.searchParams.get("encrypt"), false);
    const trustServerCertificate = toBool(
      u.searchParams.get("trustServerCertificate"),
      true,
    );
    if (!server || !user || !password) return null;
    return { server, port, user, password, options: { encrypt, trustServerCertificate } };
  } catch {
    return null;
  }
}

function toMssqlConfig(conn, sourceVar) {
  const trimmed = String(conn).trim();
  const byUrl = parseMssqlUrlString(trimmed);
  if (byUrl) return { config: byUrl, normalizedFrom: `${sourceVar}:mssql_url` };
  const byAdo = parseAdoStyleSqlServerString(trimmed);
  if (byAdo) return { config: byAdo, normalizedFrom: `${sourceVar}:sqlserver_ado` };
  throw new Error(`Unsupported connection string format in ${sourceVar}`);
}

async function main() {
  const { db } = parseArgs(process.argv);
  const connVar = process.env.DATABASE_URL
    ? "DATABASE_URL"
    : process.env.MSSQL_CONNECTION_STRING
      ? "MSSQL_CONNECTION_STRING"
      : null;
  if (!connVar) {
    throw new Error("Set DATABASE_URL or MSSQL_CONNECTION_STRING");
  }

  const resolved = toMssqlConfig(process.env[connVar], connVar);
  const cfg = { ...resolved.config, database: "master" };

  const pool = await sql.connect(cfg);
  const escaped = db.replace(/]/g, "]]");
  const q = `IF DB_ID('${db.replace(/'/g, "''")}') IS NULL CREATE DATABASE [${escaped}];`;
  await pool.request().query(q);
  await pool.close();

  console.log("db_ready", { db, connFormat: resolved.normalizedFrom, server: cfg.server, port: cfg.port });
}

await main();

