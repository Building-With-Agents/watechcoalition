import "dotenv/config";
import sql from "mssql";
import { faker } from "@faker-js/faker";

/**
 * Anonymize PII in the local Docker MSSQL database.
 *
 * Safety:
 * - Defaults to dry-run.
 * - Requires --apply AND ANONYMIZE_CONFIRM=YES.
 * - Refuses to run unless connection string appears to target localhost.
 *
 * Usage:
 *   node scripts/anonymize-docker-db.mjs --dry-run
 *   ANONYMIZE_CONFIRM=YES node scripts/anonymize-docker-db.mjs --apply
 *
 * Env:
 * - DATABASE_URL or MSSQL_CONNECTION_STRING
 * - ANONYMIZE_EMAIL_ALLOWLIST (comma-separated emails to preserve)
 */

function parseArgs(argv) {
  const args = new Set(argv.slice(2));
  const getValue = (flag) => {
    const idx = argv.indexOf(flag);
    if (idx === -1) return null;
    return argv[idx + 1] ?? null;
  };

  const apply = args.has("--apply");
  const dryRun = args.has("--dry-run") || !apply;
  const limitRaw = getValue("--limit");
  const limit = limitRaw ? Number(limitRaw) : null;
  const verifyCountRaw = getValue("--verify-count");
  const verifyCount = verifyCountRaw ? Number(verifyCountRaw) : 10;

  return { apply, dryRun, limit, verifyCount };
}

function requireEnvAny(names) {
  for (const name of names) {
    const v = process.env[name];
    if (v) return { name, value: v };
  }
  throw new Error(`Missing env var: one of ${names.join(", ")}`);
}

function toBool(v, defaultValue = false) {
  if (v === undefined || v === null) return defaultValue;
  const s = String(v).trim().toLowerCase();
  if (["1", "true", "yes", "y"].includes(s)) return true;
  if (["0", "false", "no", "n"].includes(s)) return false;
  return defaultValue;
}

function parseAdoStyleSqlServerString(conn) {
  // Example (repo docs):
  // sqlserver://localhost:1433;database=talent_finder;user=SA;password=...;encrypt=false;trustServerCertificate=true
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

  const database = kv["database"] || kv["initial catalog"];
  const user = kv["user"] || kv["user id"] || kv["uid"];
  const password = kv["password"] || kv["pwd"];
  const encrypt = toBool(kv["encrypt"], false);
  const trustServerCertificate = toBool(kv["trustservercertificate"], true);

  if (!server || !user || !password || !database) return null;

  return {
    server,
    port,
    user,
    password,
    database,
    options: { encrypt, trustServerCertificate },
  };
}

function parseMssqlUrlString(conn) {
  // Example (repo docs): mssql://SA:pass@localhost:1433/talent_finder
  try {
    const u = new URL(conn);
    if (u.protocol !== "mssql:") return null;
    const server = u.hostname;
    const port = u.port ? Number(u.port) : 1433;
    const user = decodeURIComponent(u.username);
    const password = decodeURIComponent(u.password);
    const database = u.pathname?.replace(/^\//, "");
    const encrypt = toBool(u.searchParams.get("encrypt"), false);
    const trustServerCertificate = toBool(
      u.searchParams.get("trustServerCertificate"),
      true,
    );
    if (!server || !user || !password || !database) return null;
    return {
      server,
      port,
      user,
      password,
      database,
      options: { encrypt, trustServerCertificate },
    };
  } catch {
    return null;
  }
}

function toMssqlConfig(conn, sourceVar) {
  // Prefer explicit MSSQL_CONNECTION_STRING if present, but accept DATABASE_URL (Prisma style).
  const trimmed = String(conn).trim();
  const byUrl = parseMssqlUrlString(trimmed);
  if (byUrl) return { config: byUrl, normalizedFrom: `${sourceVar}:mssql_url` };

  const byAdo = parseAdoStyleSqlServerString(trimmed);
  if (byAdo) return { config: byAdo, normalizedFrom: `${sourceVar}:sqlserver_ado` };

  throw new Error(
    `Unsupported connection string format in ${sourceVar}. ` +
      `Expected either MSSQL url (mssql://user:pass@host:port/db) ` +
      `or ADO-style sqlserver://host:port;database=...;user=...;password=...;`,
  );
}

function assertLocalTarget(config) {
  const s = String(config.server).toLowerCase();
  if (!["localhost", "127.0.0.1", "(local)"].includes(s)) {
    throw new Error(
      `Refusing to run: target server "${config.server}" is not a local host.`,
    );
  }
}

function csvToSet(csv) {
  if (!csv) return new Set();
  return new Set(
    csv
      .split(",")
      .map((s) => s.trim().toLowerCase())
      .filter(Boolean),
  );
}

function guidSeed(guid) {
  // Deterministic 32-bit seed derived from first 8 hex chars of GUID (ignoring hyphens)
  const hex = String(guid).replace(/-/g, "").slice(0, 8);
  const n = Number.parseInt(hex, 16);
  return Number.isFinite(n) ? n : 0;
}

function stableEmailForGuid(guid) {
  const prefix = String(guid).replace(/-/g, "").slice(0, 12).toLowerCase();
  return `user-${prefix}@example.test`;
}

function stableCompanyNameForGuid(guid) {
  const prefix = String(guid).replace(/-/g, "").slice(0, 10).toUpperCase();
  return `Company ${prefix}`;
}

function stableUrl(tag, guid) {
  const prefix = String(guid).replace(/-/g, "").slice(0, 10).toLowerCase();
  return `https://example.test/${tag}/${prefix}`;
}

function stableRandomUserPhotoUrl(guid) {
  // Mirror the style used in prisma/seed.mjs: https://randomuser.me/api/portraits/{men|women}/{0..99}.jpg
  const seed = guidSeed(String(guid));
  const gender = seed % 2 === 0 ? "men" : "women";
  const number = seed % 100;
  return `https://randomuser.me/api/portraits/${gender}/${number}.jpg`;
}

function stablePhone(seed) {
  // US-ish, 10 digits; keep it digits-only to fit varchar(16) reliably.
  faker.seed(seed);
  const area = faker.number.int({ min: 200, max: 999 });
  const prefix = faker.number.int({ min: 200, max: 999 });
  const line = faker.number.int({ min: 0, max: 9999 }).toString().padStart(4, "0");
  return `${area}${prefix}${line}`;
}

function expectedUserAnonymization({ id, validZips, preserveEmail, emailBefore }) {
  const seed = guidSeed(String(id));
  // IMPORTANT: Must mirror the exact sequence used in the UPDATE loop.
  faker.seed(seed);
  const first_name = faker.person.firstName();
  const last_name = faker.person.lastName();
  const phone = stablePhone(seed); // re-seeds internally; matches updater behavior
  const zip = validZips[seed % validZips.length];
  const photo_url = stableRandomUserPhotoUrl(id);
  const email = preserveEmail ? emailBefore : stableEmailForGuid(id);
  return { first_name, last_name, phone, zip, photo_url, email };
}

async function queryAll(pool, query, params = {}) {
  const req = pool.request();
  for (const [k, v] of Object.entries(params)) req.input(k, v);
  const res = await req.query(query);
  return res.recordset ?? [];
}

async function exec(pool, query, params = {}) {
  const req = pool.request();
  for (const [k, v] of Object.entries(params)) req.input(k, v);
  await req.query(query);
}

async function main() {
  const { apply, dryRun, limit, verifyCount } = parseArgs(process.argv);
  if (apply && process.env.ANONYMIZE_CONFIRM !== "YES") {
    throw new Error(
      "Refusing to apply changes: set ANONYMIZE_CONFIRM=YES and rerun with --apply.",
    );
  }

  const connSource = requireEnvAny(["DATABASE_URL", "MSSQL_CONNECTION_STRING"]);
  const resolved = toMssqlConfig(connSource.value, connSource.name);
  const mssqlConfig = resolved.config;
  assertLocalTarget(mssqlConfig);

  // Built-in preserved logins (project-specific). Keep these emails unchanged.
  // You can add more at runtime via ANONYMIZE_EMAIL_ALLOWLIST.
  const defaultPreserveEmails = new Set(["gary.larson@computingforall.org"]);
  const allowlist = csvToSet(process.env.ANONYMIZE_EMAIL_ALLOWLIST);
  const preserveEmails = new Set([
    ...Array.from(defaultPreserveEmails),
    ...Array.from(allowlist),
  ]);

  const pool = await sql.connect(mssqlConfig);
  const tx = new sql.Transaction(pool);

  const zipRows = await queryAll(pool, "SELECT zip FROM postal_geo_data");
  const validZips = zipRows.map((r) => String(r.zip)).filter(Boolean);
  if (validZips.length === 0) {
    throw new Error("postal_geo_data is empty; cannot safely randomize zip fields.");
  }

  const adminRows = await queryAll(
    pool,
    `
      SELECT u.id as userId, u.email as email
      FROM cfa_admin a
      INNER JOIN users u ON u.id = a.user_id
    `,
  );
  const adminUserIds = new Set(adminRows.map((r) => String(r.userId)));
  const adminEmails = new Set(adminRows.map((r) => String(r.email).toLowerCase()));

  // Fallback: some environments may not populate cfa_admin; also detect admins by role.
  // We use a broad match, but only to *preserve emails* (low risk).
  try {
    const roleAdminRows = await queryAll(
      pool,
      `
        SELECT id as userId, email
        FROM users
        WHERE LOWER(role) LIKE '%admin%'
      `,
    );
    for (const r of roleAdminRows) {
      adminUserIds.add(String(r.userId));
      adminEmails.add(String(r.email).toLowerCase());
    }
  } catch {
    // Ignore if query fails for any reason.
  }

  console.log("anonymize_config", {
    mode: dryRun ? "dry-run" : "apply",
    connVar: connSource.name,
    connFormat: resolved.normalizedFrom,
    server: mssqlConfig.server,
    port: mssqlConfig.port,
    database: mssqlConfig.database,
    adminsFound: adminUserIds.size,
    allowlistCount: allowlist.size,
    preserveEmailsCount: preserveEmails.size,
    limit,
    verifyCount,
  });

  // Collect target rows
  const users = await queryAll(
    pool,
    `
      SELECT TOP (@limit) id, email, first_name, last_name, phone, zip
      FROM users
      ORDER BY created_at ASC
    `,
    { limit: limit ?? 2147483647 },
  );

  const companies = await queryAll(
    pool,
    `
      SELECT TOP (@limit) company_id
      FROM companies
      ORDER BY createdAt ASC
    `,
    { limit: limit ?? 2147483647 },
  );

  const jobseekers = await queryAll(
    pool,
    `
      SELECT TOP (@limit) jobseeker_id
      FROM jobseekers
      ORDER BY created_at ASC
    `,
    { limit: limit ?? 2147483647 },
  );

  const eduProviders = await queryAll(
    pool,
    `
      SELECT TOP (@limit) id
      FROM edu_providers
      ORDER BY created_at ASC
    `,
    { limit: limit ?? 2147483647 },
  );

  const eduAddresses = await queryAll(
    pool,
    `
      SELECT TOP (@limit) edu_address_id
      FROM edu_addresses
      ORDER BY created_at ASC
    `,
    { limit: limit ?? 2147483647 },
  );

  const careerPrep = await queryAll(
    pool,
    `
      SELECT TOP (@limit) jobseekerId
      FROM CareerPrepAssessment
      ORDER BY createdAt ASC
    `,
    { limit: limit ?? 2147483647 },
  );

  const samples = {
    users: users.slice(0, 3).map((u) => ({
      id: u.id,
      emailBefore: u.email,
      firstNameBefore: u.first_name,
      lastNameBefore: u.last_name,
      phoneBefore: u.phone,
      zipBefore: u.zip,
      ...(() => {
        const id = String(u.id);
        const emailBefore = String(u.email);
        const emailLower = emailBefore.toLowerCase();
        const preserveEmail =
          adminUserIds.has(id) ||
          adminEmails.has(emailLower) ||
          preserveEmails.has(emailLower);
        const exp = expectedUserAnonymization({
          id,
          validZips,
          preserveEmail,
          emailBefore,
        });
        return {
          emailAfter: exp.email,
          firstNameAfter: exp.first_name,
          lastNameAfter: exp.last_name,
          phoneAfter: exp.phone,
          zipAfter: exp.zip,
          photoUrlAfter: exp.photo_url,
        };
      })(),
    })),
    companies: companies.slice(0, 3).map((c) => ({
      id: c.company_id,
      nameAfter: stableCompanyNameForGuid(c.company_id),
    })),
  };

  console.log("anonymize_dry_run_preview", samples);

  if (dryRun) {
    // Heuristic check: how many user emails are "non-test" (excluding preserved emails)?
    try {
      const res = await pool.request().query(`
        SELECT COUNT(*) as cnt
        FROM users
        WHERE LOWER(email) NOT LIKE '%@example.test'
      `);
      console.log("anonymize_dry_run_email_non_test_count", {
        nonTestEmailCount: res.recordset?.[0]?.cnt ?? null,
        preservedEmailsAreExcludedByPolicy: true,
      });
    } catch {
      // ignore
    }
    console.log("anonymize_dry_run_counts", {
      users: users.length,
      companies: companies.length,
      jobseekers: jobseekers.length,
      eduProviders: eduProviders.length,
      eduAddresses: eduAddresses.length,
      careerPrepAssessments: careerPrep.length,
    });
    await pool.close();
    return;
  }

  await tx.begin();
  try {
    // 1) users (preserve admin + allowlist emails, but anonymize other PII)
    for (const u of users) {
      const id = String(u.id);
      const seed = guidSeed(id);

      const emailBefore = String(u.email);
      const emailLower = emailBefore.toLowerCase();
      const preserveEmail =
        adminUserIds.has(id) ||
        adminEmails.has(emailLower) ||
        preserveEmails.has(emailLower);
      const expected = expectedUserAnonymization({
        id,
        validZips,
        preserveEmail,
        emailBefore,
      });

      // NOTE: Original data is NOT kept anywhere. Run against only non-prod copies.
      await exec(
        tx,
        `
          UPDATE users
          SET
            first_name = @first,
            last_name = @last,
            phoneCountryCode = @cc,
            phone = @phone,
            zip = @zip,
            photo_url = @photo,
            email = @email,
            updated_at = GETDATE()
          WHERE id = @id
        `,
        {
          id,
          first: expected.first_name,
          last: expected.last_name,
          cc: "+1",
          phone: expected.phone,
          zip: expected.zip,
          photo: expected.photo_url,
          email: expected.email,
        },
      );
    }

    // 2) jobseekers (social links, headlines)
    for (const js of jobseekers) {
      const id = String(js.jobseeker_id);
      const seed = guidSeed(id);
      await exec(
        tx,
        `
          UPDATE jobseekers
          SET
            linkedin_url = @li,
            portfolio_url = @pf,
            video_url = @vid,
            intro_headline = @headline,
            updated_at = GETDATE()
          WHERE jobseeker_id = @id
        `,
        {
          id,
          li: stableUrl("linkedin", id),
          pf: stableUrl("portfolio", id),
          vid: stableUrl("video", id),
          headline: `Profile summary ${seed}`,
        },
      );
    }

    // 3) jobseekers_private_data (SSN)
    await exec(
      tx,
      `
        UPDATE jobseekers_private_data
        SET ssn = NULL, updatedAt = GETDATE()
      `,
    );

    // 4) companies
    for (const c of companies) {
      const id = String(c.company_id);
      const seed = guidSeed(id);
      faker.seed(seed);
      await exec(
        tx,
        `
          UPDATE companies
          SET
            company_name = @name,
            company_email = @email,
            contact_name = @contact,
            company_phone = @phone,
            company_website_url = @site,
            company_video_url = @video,
            company_mission = @mission,
            company_vision = @vision,
            about_us = @about,
            updatedAt = GETDATE()
          WHERE company_id = @id
        `,
        {
          id,
          name: stableCompanyNameForGuid(id),
          email: `contact+${id.replace(/-/g, "").slice(0, 8)}@example.test`,
          contact: `${faker.person.firstName()} ${faker.person.lastName()}`,
          phone: stablePhone(seed),
          site: stableUrl("company", id),
          video: stableUrl("company-video", id),
          mission: `Mission ${seed}`,
          vision: `Vision ${seed}`,
          about: `About ${seed}`,
        },
      );
    }

    // 5) edu_providers
    for (const p of eduProviders) {
      const id = String(p.id);
      const seed = guidSeed(id);
      faker.seed(seed);
      await exec(
        tx,
        `
          UPDATE edu_providers
          SET
            contact = @contact,
            contact_email = @email,
            edu_url = @url,
            updated_at = GETDATE()
          WHERE id = @id
        `,
        {
          id,
          contact: `${faker.person.firstName()} ${faker.person.lastName()}`,
          email: `edu+${id.replace(/-/g, "").slice(0, 8)}@example.test`,
          url: stableUrl("edu", id),
        },
      );
    }

    // 6) edu_addresses
    for (const a of eduAddresses) {
      const id = String(a.edu_address_id);
      const seed = guidSeed(id);
      faker.seed(seed);
      const zip = validZips[seed % validZips.length];
      await exec(
        tx,
        `
          UPDATE edu_addresses
          SET
            street1 = @s1,
            street2 = @s2,
            zip = @zip,
            updated_at = GETDATE()
          WHERE edu_address_id = @id
        `,
        {
          id,
          s1: `${faker.location.streetAddress()}`,
          s2: faker.datatype.boolean() ? faker.location.secondaryAddress() : null,
          zip,
        },
      );
    }

    // 7) CareerPrepAssessment.streetAddress
    for (const a of careerPrep) {
      const id = String(a.jobseekerId);
      const seed = guidSeed(id);
      faker.seed(seed);
      await exec(
        tx,
        `
          UPDATE CareerPrepAssessment
          SET streetAddress = @addr, updatedAt = GETDATE()
          WHERE jobseekerId = @id
        `,
        {
          id,
          addr: faker.location.streetAddress(),
        },
      );
    }

    await tx.commit();

    // Post-apply deterministic verification on a few sampled user IDs.
    const verifyN = Math.max(0, Math.min(verifyCount, users.length));
    if (verifyN > 0) {
      const verifyIds = users.slice(0, verifyN).map((u) => String(u.id));
      const placeholders = verifyIds.map((_, i) => `@id${i}`).join(", ");
      const req = pool.request();
      verifyIds.forEach((id, i) => req.input(`id${i}`, id));
      const afterRows = await req.query(
        `
          SELECT id, email, first_name, last_name, phone, zip
          FROM users
          WHERE id IN (${placeholders})
        `,
      );
      const byId = new Map(
        (afterRows.recordset ?? []).map((r) => [String(r.id), r]),
      );

      const mismatches = [];
      for (const id of verifyIds) {
        const after = byId.get(id);
        if (!after) {
          mismatches.push({ id, error: "missing_row_after_update" });
          continue;
        }
        const emailLower = String(after.email).toLowerCase();
        const preserveEmail =
          adminUserIds.has(id) ||
          adminEmails.has(emailLower) ||
          preserveEmails.has(emailLower);
        const expected = expectedUserAnonymization({
          id,
          validZips,
          preserveEmail,
          emailBefore: String(after.email),
        });

        if (
          String(after.first_name ?? "") !== expected.first_name ||
          String(after.last_name ?? "") !== expected.last_name ||
          String(after.phone ?? "") !== expected.phone ||
          String(after.zip ?? "") !== expected.zip ||
          (!preserveEmail && String(after.email) !== expected.email)
        ) {
          mismatches.push({
            id,
            actual: {
              email: after.email,
              first_name: after.first_name,
              last_name: after.last_name,
              phone: after.phone,
              zip: after.zip,
            },
            expected: {
              email: preserveEmail ? "(preserved)" : expected.email,
              first_name: expected.first_name,
              last_name: expected.last_name,
              phone: expected.phone,
              zip: expected.zip,
            },
          });
        }
      }

      if (mismatches.length) {
        console.error("anonymize_verify_failed", { mismatches });
        throw new Error(
          `Anonymize verification failed for ${mismatches.length} user(s).`,
        );
      }
      console.log("anonymize_verify_ok", { verifiedUsers: verifyN });
    }

    console.log("anonymize_apply_ok", {
      users: users.length,
      companies: companies.length,
      jobseekers: jobseekers.length,
      eduProviders: eduProviders.length,
      eduAddresses: eduAddresses.length,
      careerPrepAssessments: careerPrep.length,
    });
  } catch (e) {
    try {
      await tx.rollback();
    } catch {
      // ignore rollback errors
    }
    throw e;
  } finally {
    await pool.close();
  }
}

await main();

