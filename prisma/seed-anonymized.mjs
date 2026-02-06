import "dotenv/config";
import fs from "node:fs/promises";
import path from "node:path";
import { PrismaClient, Prisma } from "@prisma/client";

/**
 * Seed anonymized fixtures into the current DATABASE_URL.
 *
 * Expected intern flow:
 *   prisma db push
 *   prisma generate
 *   node prisma/seed-anonymized.mjs
 *
 * Fixtures are read from prisma/mock-data/*.json
 */

function parseArgs(argv) {
  const args = new Set(argv.slice(2));
  return {
    outDir: (() => {
      const idx = argv.indexOf("--dir");
      return idx === -1 ? "prisma/mock-data" : argv[idx + 1] ?? "prisma/mock-data";
    })(),
    skipJobPostSkillConnect: args.has("--skip-jobpost-skill-connect"),
    idempotent: args.has("--idempotent"),
  };
}

async function readJson(dir, name) {
  const p = path.join(dir, name);
  const text = await fs.readFile(p, "utf8");
  return JSON.parse(text);
}

function reviveDates(obj) {
  // Best-effort: convert ISO strings back to Date for Prisma DateTime fields.
  if (Array.isArray(obj)) return obj.map(reviveDates);
  if (!obj || typeof obj !== "object") return obj;
  const out = {};
  for (const [k, v] of Object.entries(obj)) {
    if (typeof v === "string" && /^\d{4}-\d{2}-\d{2}T/.test(v)) {
      out[k] = new Date(v);
    } else {
      out[k] = reviveDates(v);
    }
  }
  return out;
}

async function createManySafe(model, rows, opts = {}) {
  if (!rows?.length) return 0;
  try {
    const res = await model.createMany({
      data: rows,
    });
    return res.count ?? 0;
  } catch (e) {
    // SQL Server connector does not support createMany(skipDuplicates).
    // For convenience when re-running locally, allow an idempotent mode
    // that falls back to per-row create and ignores unique-constraint errors.
    if (opts.idempotent) {
      let created = 0;
      for (const row of rows) {
        try {
          await model.create({ data: row });
          created++;
        } catch (inner) {
          if (
            inner instanceof Prisma.PrismaClientKnownRequestError &&
            inner.code === "P2002"
          ) {
            continue;
          }
          throw inner;
        }
      }
      return created;
    }
    throw e;
  }
}

async function main() {
  const opts = parseArgs(process.argv);
  const prisma = new PrismaClient();

  const dir = opts.outDir;
  const metadata = await readJson(dir, "metadata.json").catch(() => null);
  console.log("seed_anonymized_start", { dir, metadata });

  const industry_sectors = reviveDates(await readJson(dir, "industry_sectors.json"));
  const technology_areas = reviveDates(await readJson(dir, "technology_areas.json"));
  const postal_geo_data = reviveDates(await readJson(dir, "postal_geo_data.json"));

  const skill_subcategories = reviveDates(
    await readJson(dir, "skill_subcategories.json"),
  );
  const skills = reviveDates(await readJson(dir, "skills.json"));
  const pathways = reviveDates(await readJson(dir, "pathways.json"));
  const companies = reviveDates(await readJson(dir, "companies.json"));
  const company_addresses = reviveDates(await readJson(dir, "company_addresses.json"));
  const users = reviveDates(await readJson(dir, "users.json"));
  const employers = reviveDates(await readJson(dir, "employers.json"));
  const edu_providers = reviveDates(await readJson(dir, "edu_providers.json"));
  const edu_addresses = reviveDates(await readJson(dir, "edu_addresses.json"));
  const programs = reviveDates(await readJson(dir, "programs.json"));
  const jobseekers = reviveDates(await readJson(dir, "jobseekers.json"));
  const jobseekers_education = reviveDates(
    await readJson(dir, "jobseekers_education.json"),
  );
  const certificates = reviveDates(await readJson(dir, "certificates.json"));
  const work_experiences = reviveDates(await readJson(dir, "work_experiences.json"));
  const project_experiences = reviveDates(await readJson(dir, "project_experiences.json"));
  const jobseeker_has_skills = reviveDates(
    await readJson(dir, "jobseeker_has_skills.json"),
  );
  const pathway_has_skills = reviveDates(
    await readJson(dir, "pathway_has_skills.json"),
  );
  const job_postings = reviveDates(await readJson(dir, "job_postings.json"));

  // Create in FK-safe order.
  const counts = {};
  counts.industry_sectors = await createManySafe(prisma.industry_sectors, industry_sectors, {
    idempotent: opts.idempotent,
  });
  counts.technology_areas = await createManySafe(
    prisma.technology_areas,
    technology_areas,
    { idempotent: opts.idempotent },
  );
  counts.postal_geo_data = await createManySafe(prisma.postalGeoData, postal_geo_data, {
    idempotent: opts.idempotent,
  });

  counts.skill_subcategories = await createManySafe(
    prisma.skill_subcategories,
    skill_subcategories,
    { idempotent: opts.idempotent },
  );
  counts.skills = await createManySafe(prisma.skills, skills, {
    idempotent: opts.idempotent,
  });
  counts.pathways = await createManySafe(prisma.pathways, pathways, {
    idempotent: opts.idempotent,
  });

  counts.users = await createManySafe(prisma.user, users, {
    idempotent: opts.idempotent,
  });

  counts.companies = await createManySafe(prisma.companies, companies, {
    idempotent: opts.idempotent,
  });
  counts.company_addresses = await createManySafe(
    prisma.company_addresses,
    company_addresses,
    { idempotent: opts.idempotent },
  );
  counts.employers = await createManySafe(prisma.employers, employers, {
    idempotent: opts.idempotent,
  });

  counts.edu_providers = await createManySafe(prisma.edu_providers, edu_providers, {
    idempotent: opts.idempotent,
  });
  counts.edu_addresses = await createManySafe(prisma.edu_addresses, edu_addresses, {
    idempotent: opts.idempotent,
  });
  counts.programs = await createManySafe(prisma.programs, programs, {
    idempotent: opts.idempotent,
  });

  counts.jobseekers = await createManySafe(prisma.jobseekers, jobseekers, {
    idempotent: opts.idempotent,
  });
  counts.jobseekers_education = await createManySafe(
    prisma.jobseekers_education,
    jobseekers_education,
    { idempotent: opts.idempotent },
  );

  counts.certificates = await createManySafe(prisma.certificates, certificates, {
    idempotent: opts.idempotent,
  });
  counts.work_experiences = await createManySafe(
    prisma.workExperience,
    work_experiences,
    { idempotent: opts.idempotent },
  );
  counts.project_experiences = await createManySafe(
    prisma.projectExperiences,
    project_experiences,
    { idempotent: opts.idempotent },
  );

  // Join tables
  counts.jobseeker_has_skills = await createManySafe(
    prisma.jobseeker_has_skills,
    jobseeker_has_skills,
    { idempotent: opts.idempotent },
  );
  counts.pathway_has_skills = await createManySafe(
    prisma.pathway_has_skills,
    pathway_has_skills,
    { idempotent: opts.idempotent },
  );

  // job_postings + connect to skills via implicit M2M relation
  if (job_postings?.length) {
    let created = 0;
    let connected = 0;

    for (const jp of job_postings) {
      const { skillIds, skills: _skills, ...data } = jp;
      // Don't attempt to update the PK directly.
      // (We *do* want to update publish/unpublish dates and other fields when re-seeding.)
      // eslint-disable-next-line @typescript-eslint/no-unused-vars
      const { job_posting_id: _id, ...updateData } = data;
      // Create posting row first
      await prisma.job_postings.upsert({
        where: { job_posting_id: data.job_posting_id },
        update: updateData,
        create: data,
      });
      created++;

      if (!opts.skipJobPostSkillConnect && Array.isArray(skillIds) && skillIds.length) {
        await prisma.job_postings.update({
          where: { job_posting_id: data.job_posting_id },
          data: {
            skills: {
              connect: skillIds.map((id) => ({ skill_id: id })),
            },
          },
        });
        connected++;
      }
    }

    counts.job_postings = created;
    counts.job_postings_skills_connected = connected;
  } else {
    counts.job_postings = 0;
    counts.job_postings_skills_connected = 0;
  }

  console.log("seed_anonymized_ok", counts);
  await prisma.$disconnect();
}

await main();

