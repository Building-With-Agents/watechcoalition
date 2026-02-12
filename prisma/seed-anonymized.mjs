import "dotenv/config";
import fs from "node:fs/promises";
import path from "node:path";
import { PrismaClient, Prisma } from "@prisma/client";

const DEFAULT_COMPANY_CREATED_BY_USER_ID = "aa181331-0693-446d-9c2e-134782a4865e";

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

function buildIdSet(rows, idField) {
  return new Set((rows ?? []).map((row) => row[idField]).filter(Boolean));
}

function firstId(rows, idField, label) {
  const id = rows?.[0]?.[idField];
  if (!id) {
    throw new Error(`Cannot determine fallback for ${label}; no parent rows found.`);
  }
  return id;
}

function repairFkRows(rows, options) {
  const { rowLabel, field, parentIds, fallbackId, nullable = false, report } = options;
  let repaired = 0;

  const nextRows = rows.map((row) => {
    const value = row[field];
    if (value == null) return row;
    if (parentIds.has(value)) return row;

    if (!fallbackId && nullable) {
      repaired++;
      return { ...row, [field]: null };
    }

    if (!fallbackId) {
      throw new Error(
        `No fallback available to repair ${rowLabel}.${field} value "${String(value)}".`,
      );
    }

    repaired++;
    return { ...row, [field]: fallbackId };
  });

  if (repaired > 0) {
    report.push({
      model: rowLabel,
      field,
      repaired,
      fallbackId: fallbackId ?? null,
    });
  }

  return nextRows;
}

function validateFkRows(rows, options) {
  const { rowLabel, field, parentIds, nullable = false } = options;
  const unresolved = rows.filter((row) => {
    const value = row[field];
    if (value == null) return !nullable;
    return !parentIds.has(value);
  });
  if (unresolved.length > 0) {
    const sample = unresolved[0]?.[field];
    throw new Error(
      `Unresolved FK after repair: ${rowLabel}.${field} (count=${unresolved.length}, sample=${String(sample)}).`,
    );
  }
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
      let skippedDuplicates = 0;
      let skippedFk = 0;
      for (const row of rows) {
        try {
          await model.create({ data: row });
          created++;
        } catch (inner) {
          if (
            inner instanceof Prisma.PrismaClientKnownRequestError &&
            inner.code === "P2002"
          ) {
            if (inner.code === "P2002") skippedDuplicates++;
            continue;
          }
          throw inner;
        }
      }
      if (skippedDuplicates || skippedFk) {
        console.warn("seed_createManySafe_skips", {
          model: model?.name ?? "unknown",
          skippedDuplicates,
          skippedFk: 0,
        });
      }
      return created;
    }
    throw e;
  }
}

async function main() {
  const opts = parseArgs(process.argv);
  const prisma = new PrismaClient();
  const [targetDb] = await prisma.$queryRawUnsafe(
    "SELECT DB_NAME() AS dbName, @@SERVERNAME AS serverName",
  );
  console.log("seed_target_db", targetDb);

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
  const repairReport = [];

  const preferredCreatedByUserId =
    process.env.SEED_COMPANY_CREATED_BY_USER_ID ?? DEFAULT_COMPANY_CREATED_BY_USER_ID;
  const selectedCreatedByUser = users.find((u) => u.id === preferredCreatedByUserId);
  if (!selectedCreatedByUser?.email) {
    throw new Error(
      `SEED_COMPANY_CREATED_BY_USER_ID (${preferredCreatedByUserId}) not found in users fixtures.`,
    );
  }

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

  // Resolve an existing user ID for companies.createdBy:
  // prefer the configured fixture user, fall back to same-email row, then any user.
  let existingCreatedByUser = await prisma.user.findUnique({
    where: { id: preferredCreatedByUserId },
    select: { id: true },
  });
  if (!existingCreatedByUser) {
    existingCreatedByUser = await prisma.user.findUnique({
      where: { email: selectedCreatedByUser.email },
      select: { id: true },
    });
  }
  if (!existingCreatedByUser) {
    existingCreatedByUser = await prisma.user.findFirst({
      select: { id: true },
    });
  }
  if (!existingCreatedByUser?.id) {
    throw new Error("No users exist in DB after user seed; cannot satisfy companies.createdBy FK.");
  }

  const companiesWithFixedCreatedBy = companies.map((company) => ({
    ...company,
    createdBy: existingCreatedByUser.id,
  }));

  // FK normalization/repair before insert; no FK violations should be skipped later.
  const companyIds = buildIdSet(companiesWithFixedCreatedBy, "company_id");
  const userIds = buildIdSet(users, "id");
  const employerIds = buildIdSet(employers, "employer_id");
  const jobseekerIds = buildIdSet(jobseekers, "jobseeker_id");
  const eduProviderIds = buildIdSet(edu_providers, "id");
  const programIds = buildIdSet(programs, "id");
  const companyAddressIds = buildIdSet(company_addresses, "company_address_id");
  const techAreaIds = buildIdSet(technology_areas, "id");
  const sectorIds = buildIdSet(industry_sectors, "industry_sector_id");

  const fallbackUserId = existingCreatedByUser.id;
  const fallbackCompanyId = firstId(companiesWithFixedCreatedBy, "company_id", "companies");
  const fallbackEmployerId = firstId(employers, "employer_id", "employers");
  const fallbackJobseekerId = firstId(jobseekers, "jobseeker_id", "jobseekers");
  const fallbackEduProviderId = firstId(edu_providers, "id", "edu_providers");
  const fallbackProgramId = firstId(programs, "id", "programs");
  const fallbackCompanyAddressId = firstId(
    company_addresses,
    "company_address_id",
    "company_addresses",
  );
  const fallbackTechAreaId = firstId(technology_areas, "id", "technology_areas");
  const fallbackSectorId = firstId(industry_sectors, "industry_sector_id", "industry_sectors");

  const employersRepairedUser = repairFkRows(employers, {
    rowLabel: "employers",
    field: "user_id",
    parentIds: userIds,
    fallbackId: fallbackUserId,
    report: repairReport,
  });
  const employersRepaired = repairFkRows(employersRepairedUser, {
    rowLabel: "employers",
    field: "company_id",
    parentIds: companyIds,
    fallbackId: fallbackCompanyId,
    nullable: true,
    report: repairReport,
  });

  const jobseekersRepaired = repairFkRows(jobseekers, {
    rowLabel: "jobseekers",
    field: "user_id",
    parentIds: userIds,
    fallbackId: fallbackUserId,
    report: repairReport,
  });

  const jobseekersEducationRepairedJobseeker = repairFkRows(jobseekers_education, {
    rowLabel: "jobseekers_education",
    field: "jobseekerId",
    parentIds: jobseekerIds,
    fallbackId: fallbackJobseekerId,
    report: repairReport,
  });
  const jobseekersEducationRepairedProvider = repairFkRows(
    jobseekersEducationRepairedJobseeker,
    {
      rowLabel: "jobseekers_education",
      field: "eduProviderId",
      parentIds: eduProviderIds,
      fallbackId: fallbackEduProviderId,
      report: repairReport,
    },
  );
  const jobseekersEducationRepaired = repairFkRows(jobseekersEducationRepairedProvider, {
    rowLabel: "jobseekers_education",
    field: "programId",
    parentIds: programIds,
    fallbackId: fallbackProgramId,
    nullable: true,
    report: repairReport,
  });

  const jobPostingsRepairedEmployer = repairFkRows(job_postings, {
    rowLabel: "job_postings",
    field: "employer_id",
    parentIds: employerIds,
    fallbackId: fallbackEmployerId,
    nullable: true,
    report: repairReport,
  });
  const jobPostingsRepairedCompany = repairFkRows(jobPostingsRepairedEmployer, {
    rowLabel: "job_postings",
    field: "company_id",
    parentIds: companyIds,
    fallbackId: fallbackCompanyId,
    report: repairReport,
  });
  const jobPostingsRepairedLocation = repairFkRows(jobPostingsRepairedCompany, {
    rowLabel: "job_postings",
    field: "location_id",
    parentIds: companyAddressIds,
    fallbackId: fallbackCompanyAddressId,
    report: repairReport,
  });
  const jobPostingsRepairedTechArea = repairFkRows(jobPostingsRepairedLocation, {
    rowLabel: "job_postings",
    field: "tech_area_id",
    parentIds: techAreaIds,
    fallbackId: fallbackTechAreaId,
    nullable: true,
    report: repairReport,
  });
  const jobPostingsRepaired = repairFkRows(jobPostingsRepairedTechArea, {
    rowLabel: "job_postings",
    field: "sector_id",
    parentIds: sectorIds,
    fallbackId: fallbackSectorId,
    nullable: true,
    report: repairReport,
  });

  validateFkRows(employersRepaired, {
    rowLabel: "employers",
    field: "user_id",
    parentIds: userIds,
  });
  validateFkRows(employersRepaired, {
    rowLabel: "employers",
    field: "company_id",
    parentIds: companyIds,
    nullable: true,
  });
  validateFkRows(jobseekersRepaired, {
    rowLabel: "jobseekers",
    field: "user_id",
    parentIds: userIds,
  });
  validateFkRows(jobseekersEducationRepaired, {
    rowLabel: "jobseekers_education",
    field: "jobseekerId",
    parentIds: jobseekerIds,
  });
  validateFkRows(jobseekersEducationRepaired, {
    rowLabel: "jobseekers_education",
    field: "eduProviderId",
    parentIds: eduProviderIds,
  });
  validateFkRows(jobseekersEducationRepaired, {
    rowLabel: "jobseekers_education",
    field: "programId",
    parentIds: programIds,
    nullable: true,
  });
  validateFkRows(jobPostingsRepaired, {
    rowLabel: "job_postings",
    field: "company_id",
    parentIds: companyIds,
  });
  validateFkRows(jobPostingsRepaired, {
    rowLabel: "job_postings",
    field: "employer_id",
    parentIds: employerIds,
    nullable: true,
  });

  counts.companies = await createManySafe(prisma.companies, companiesWithFixedCreatedBy, {
    idempotent: opts.idempotent,
  });
  counts.company_addresses = await createManySafe(
    prisma.company_addresses,
    company_addresses,
    { idempotent: opts.idempotent },
  );
  counts.employers = await createManySafe(prisma.employers, employersRepaired, {
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

  counts.jobseekers = await createManySafe(prisma.jobseekers, jobseekersRepaired, {
    idempotent: opts.idempotent,
  });
  counts.jobseekers_education = await createManySafe(
    prisma.jobseekers_education,
    jobseekersEducationRepaired,
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

    for (const jp of jobPostingsRepaired) {
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

  if (repairReport.length > 0) {
    console.log("seed_fk_repairs_applied", repairReport);
  } else {
    console.log("seed_fk_repairs_applied", []);
  }

  console.log("seed_anonymized_ok", counts);
  await prisma.$disconnect();
}

await main();

