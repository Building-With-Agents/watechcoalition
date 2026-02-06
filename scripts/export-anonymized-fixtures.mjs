import "dotenv/config";
import fs from "node:fs/promises";
import path from "node:path";
import { PrismaClient } from "@prisma/client";

/**
 * Export a small anonymized subset of data from the current DATABASE_URL into JSON fixtures.
 *
 * Intended workflow:
 * 1) Import + anonymize a local Docker DB (see scripts/anonymize-docker-db.mjs)
 * 2) Run this exporter to produce fixtures in prisma/mock-data/
 * 3) Interns run: prisma db push -> prisma generate -> node prisma/seed-anonymized.mjs
 */

function parseArgs(argv) {
  const args = argv.slice(2);
  const get = (name, fallback = null) => {
    const idx = args.indexOf(name);
    if (idx === -1) return fallback;
    return args[idx + 1] ?? fallback;
  };
  const toInt = (v, def) => {
    const n = Number(v);
    return Number.isFinite(n) ? n : def;
  };

  return {
    outDir: get("--outDir", "prisma/mock-data"),
    jobseekers: toInt(get("--jobseekers", "25"), 25),
    employers: toInt(get("--employers", "10"), 10),
    companies: toInt(get("--companies", "10"), 10),
    jobPostings: toInt(get("--jobPostings", "25"), 25),
    skillsCap: toInt(get("--skillsCap", "500"), 500),
  };
}

function jsonReplacer(_k, v) {
  if (typeof v === "bigint") return v.toString();
  if (v instanceof Date) return v.toISOString();
  return v;
}

async function writeJson(outDir, filename, data) {
  await fs.mkdir(outDir, { recursive: true });
  const p = path.join(outDir, filename);
  const text = JSON.stringify(data, jsonReplacer, 2) + "\n";
  await fs.writeFile(p, text, "utf8");
}

function uniq(arr) {
  return Array.from(new Set(arr.filter(Boolean)));
}

async function main() {
  const opts = parseArgs(process.argv);
  const prisma = new PrismaClient();

  const startedAt = new Date();
  const meta = {
    exportedAt: startedAt.toISOString(),
    opts,
    counts: {},
  };

  // 1) Pick jobseekers and include their user + skill links + some profile content
  const jobseekers = await prisma.jobseekers.findMany({
    take: opts.jobseekers,
    orderBy: { createdAt: "asc" },
    include: {
      users: true,
      pathways: true,
      jobseeker_has_skills: true,
      work_experiences: true,
      project_experiences: true,
      certificates: true,
      jobseeker_education: true,
    },
  });

  const jobseekerUserIds = uniq(jobseekers.map((j) => j.user_id));
  const pathwayIds = uniq(jobseekers.map((j) => j.targeted_pathway));
  const jobseekerSkillLinks = jobseekers.flatMap((j) => j.jobseeker_has_skills);
  const skillIdsFromJobseekers = uniq(jobseekerSkillLinks.map((l) => l.skill_id));

  // 2) Pick employers (and their users + companies)
  const employers = await prisma.employers.findMany({
    take: opts.employers,
    orderBy: { createdAt: "asc" },
    include: { users: true, companies: true, company_addresses: true },
  });

  const employerUserIds = uniq(employers.map((e) => e.user_id));
  const employerIds = uniq(employers.map((e) => e.employer_id));
  const companyIdsFromEmployers = uniq(employers.map((e) => e.company_id));
  const companyAddressIdsFromEmployers = uniq(employers.map((e) => e.work_address_id));

  // 3) Pick companies (prefer those connected to employers)
  const companyIdsPreferred = uniq(companyIdsFromEmployers);

  const preferredCompanies = companyIdsPreferred.length
    ? await prisma.companies.findMany({
        where: { company_id: { in: companyIdsPreferred } },
        orderBy: { createdAt: "asc" },
      })
    : [];

  const remainingCompanySlots = Math.max(0, opts.companies - preferredCompanies.length);
  const fillerCompanies = remainingCompanySlots
    ? await prisma.companies.findMany({
        take: remainingCompanySlots,
        where: preferredCompanies.length
          ? { company_id: { notIn: preferredCompanies.map((c) => c.company_id) } }
          : {},
        orderBy: { createdAt: "asc" },
      })
    : [];

  const companies = [...preferredCompanies, ...fillerCompanies];
  let companyIds = uniq(companies.map((c) => c.company_id));

  // Pull company addresses for selected companies
  const companyAddresses = await prisma.company_addresses.findMany({
    where: {
      OR: [
        { company_id: { in: companyIds } },
        { company_address_id: { in: companyAddressIdsFromEmployers } },
      ],
    },
  });

  let companyAddressIds = uniq(companyAddresses.map((a) => a.company_address_id));

  // 4) Job postings for selected companies
  const jobPostingsPrimary = companyIds.length
    ? await prisma.job_postings.findMany({
        take: opts.jobPostings,
        where: { company_id: { in: companyIds } },
        orderBy: { createdAt: "desc" },
        include: { skills: { select: { skill_id: true } } },
      })
    : [];

  const remainingJobPostingSlots = Math.max(0, opts.jobPostings - jobPostingsPrimary.length);
  const jobPostingsFallback = remainingJobPostingSlots
    ? await prisma.job_postings.findMany({
        take: remainingJobPostingSlots,
        where: {
          ...(jobPostingsPrimary.length
            ? { job_posting_id: { notIn: jobPostingsPrimary.map((j) => j.job_posting_id) } }
            : {}),
          // Prefer postings that don't introduce missing employer FKs.
          OR: [{ employer_id: null }, { employer_id: { in: employerIds } }],
        },
        orderBy: { createdAt: "desc" },
        include: { skills: { select: { skill_id: true } } },
      })
    : [];

  const jobPostings = [...jobPostingsPrimary, ...jobPostingsFallback];

  // Ensure we include any company_addresses referenced by the selected job postings (location_id FK)
  const locationIdsFromJobPostings = uniq(jobPostings.map((jp) => jp.location_id));
  const missingLocationIds = locationIdsFromJobPostings.filter(
    (id) => !companyAddressIds.includes(id),
  );
  if (missingLocationIds.length) {
    const moreAddresses = await prisma.company_addresses.findMany({
      where: { company_address_id: { in: missingLocationIds } },
    });
    companyAddresses.push(...moreAddresses);
    companyAddressIds = uniq(companyAddresses.map((a) => a.company_address_id));
  }

  // Ensure we include any employers referenced by the selected job postings
  const employerIdsFromJobPostings = uniq(
    jobPostings.map((jp) => jp.employer_id).filter(Boolean),
  );
  const missingEmployerIds = employerIdsFromJobPostings.filter(
    (id) => !employers.some((e) => e.employer_id === id),
  );
  if (missingEmployerIds.length) {
    const moreEmployers = await prisma.employers.findMany({
      where: { employer_id: { in: missingEmployerIds } },
      include: { users: true, companies: true, company_addresses: true },
    });
    employers.push(...moreEmployers);
  }

  // Ensure we include any companies/addresses needed by the selected job postings
  const companyIdsFromJobPostings = uniq(jobPostings.map((jp) => jp.company_id));
  companyIds = uniq([...companyIds, ...companyIdsFromJobPostings]);

  if (companyIdsFromJobPostings.length) {
    const missingCompanyIds = companyIdsFromJobPostings.filter(
      (id) => !companies.some((c) => c.company_id === id),
    );
    if (missingCompanyIds.length) {
      const moreCompanies = await prisma.companies.findMany({
        where: { company_id: { in: missingCompanyIds } },
      });
      companies.push(...moreCompanies);
    }
  }

  const skillIdsFromJobPostings = uniq(
    jobPostings.flatMap((jp) => jp.skills.map((s) => s.skill_id)),
  );

  // 4b) Reference tables required by FKs (industry sectors, tech areas, postal geo data)
  const industrySectorIds = uniq([
    ...companies.map((c) => c.industry_sector_id),
    ...jobPostings.map((j) => j.sector_id),
    ...jobseekers.flatMap((j) => j.work_experiences).map((w) => w.sectorId),
  ]);
  const industrySectors = industrySectorIds.length
    ? await prisma.industry_sectors.findMany({
        where: { industry_sector_id: { in: industrySectorIds } },
      })
    : [];

  const techAreaIds = uniq([
    ...jobPostings.map((j) => j.tech_area_id),
    ...jobseekers.flatMap((j) => j.work_experiences).map((w) => w.techAreaId),
  ]);
  const technologyAreas = techAreaIds.length
    ? await prisma.technology_areas.findMany({
        where: { id: { in: techAreaIds } },
      })
    : [];

  // 5) Pathways and their skill links (for selected jobseekers)
  const pathways = pathwayIds.length
    ? await prisma.pathways.findMany({
        where: { pathway_id: { in: pathwayIds } },
      })
    : [];

  const pathwaySkillLinks = pathwayIds.length
    ? await prisma.pathway_has_skills.findMany({
        where: { pathway_id: { in: pathwayIds } },
      })
    : [];

  const skillIdsFromPathways = uniq(pathwaySkillLinks.map((l) => l.skill_id));

  // 6) Skills needed for all selected links, plus a small cap for autocomplete usefulness
  const referencedSkillIds = uniq([
    ...skillIdsFromJobseekers,
    ...skillIdsFromJobPostings,
    ...skillIdsFromPathways,
  ]);

  const extraSkills = await prisma.skills.findMany({
    take: opts.skillsCap,
    orderBy: { createdAt: "asc" },
    select: {
      skill_id: true,
      skill_subcategory_id: true,
      skill_name: true,
      skill_info_url: true,
      skill_type: true,
      updatedAt: true,
      createdAt: true,
    },
  });

  const extraSkillIds = extraSkills.map((s) => s.skill_id);
  const skills = await prisma.skills.findMany({
    where: { skill_id: { in: uniq([...referencedSkillIds, ...extraSkillIds]) } },
    select: {
      skill_id: true,
      skill_subcategory_id: true,
      skill_name: true,
      skill_info_url: true,
      skill_type: true,
      updatedAt: true,
      createdAt: true,
      // NOTE: embedding is intentionally excluded from fixtures (Unsupported vector type).
    },
  });

  const skillSubcategoryIds = uniq(skills.map((s) => s.skill_subcategory_id));
  const skillSubcategories = await prisma.skill_subcategories.findMany({
    where: { skill_subcategory_id: { in: skillSubcategoryIds } },
  });

  // 7) Education tables referenced by selected jobseekers
  const education = jobseekers.flatMap((j) => j.jobseeker_education);
  const eduProviderIds = uniq(education.map((e) => e.eduProviderId));
  const programIds = uniq(education.map((e) => e.programId).filter(Boolean));

  const eduProviders = eduProviderIds.length
    ? await prisma.edu_providers.findMany({
        where: { id: { in: eduProviderIds } },
      })
    : [];

  const eduAddresses = eduProviderIds.length
    ? await prisma.edu_addresses.findMany({
        where: { edu_provider_id: { in: eduProviderIds } },
      })
    : [];

  const programs = programIds.length
    ? await prisma.programs.findMany({
        where: { id: { in: programIds } },
      })
    : [];

  // 8) Build a unique user set (jobseekers + employers + any company.createdBy)
  const allEmployerUserIds = uniq(employers.map((e) => e.user_id));
  const createdByUserIds = uniq(
    companies.map((c) => c.createdBy).filter(Boolean),
  );

  const allUserIds = uniq([
    ...jobseekerUserIds,
    ...allEmployerUserIds,
    ...createdByUserIds,
  ]);

  const users = allUserIds.length
    ? await prisma.user.findMany({
        where: { id: { in: allUserIds } },
      })
    : [];

  const zips = uniq([
    ...users.map((u) => u.zip),
    ...companyAddresses.map((a) => a.zip),
    ...eduAddresses.map((a) => a.zip),
  ]);
  const postalGeoData = zips.length
    ? await prisma.postalGeoData.findMany({
        where: { zip: { in: zips } },
      })
    : [];

  // 9) Transform for seeding: store connect arrays instead of nested objects
  const jobPostingsForSeed = jobPostings.map((jp) => {
    const { skills: jpSkills, ...rest } = jp;

    // Keep mock fixtures "alive" so listings always appear in the UI, which filters by:
    //   unpublish_date >= now
    const publish_date = new Date(startedAt);
    publish_date.setDate(publish_date.getDate() - 7);
    const unpublish_date = new Date(startedAt);
    unpublish_date.setFullYear(unpublish_date.getFullYear() + 1);

    return {
      ...rest,
      publish_date,
      unpublish_date,
      skillIds: jpSkills.map((s) => s.skill_id),
    };
  });

  // jobseekers include nested arrays from include; seed wants them as separate tables
  const jobseekersForSeed = jobseekers.map((j) => {
    // eslint-disable-next-line @typescript-eslint/no-unused-vars
    const {
      users: _u,
      pathways: _p,
      jobseeker_has_skills: _hs,
      work_experiences: _we,
      project_experiences: _pe,
      certificates: _c,
      jobseeker_education: _je,
      ...rest
    } = j;
    return rest;
  });

  const employersForSeed = employers.map((e) => {
    // eslint-disable-next-line @typescript-eslint/no-unused-vars
    const { users: _u, companies: _c, company_addresses: _a, ...rest } = e;
    return rest;
  });

  // company_addresses not included in companies query above; already separately fetched

  // 10) Write fixtures
  const outDir = opts.outDir;
  await writeJson(outDir, "metadata.json", meta);
  await writeJson(outDir, "industry_sectors.json", industrySectors);
  await writeJson(outDir, "technology_areas.json", technologyAreas);
  await writeJson(outDir, "postal_geo_data.json", postalGeoData);
  await writeJson(outDir, "users.json", users);
  await writeJson(outDir, "companies.json", companies);
  await writeJson(outDir, "company_addresses.json", companyAddresses);
  await writeJson(outDir, "employers.json", employersForSeed);
  await writeJson(outDir, "jobseekers.json", jobseekersForSeed);
  await writeJson(outDir, "jobseekers_education.json", education);
  await writeJson(outDir, "programs.json", programs);
  await writeJson(outDir, "edu_providers.json", eduProviders);
  await writeJson(outDir, "edu_addresses.json", eduAddresses);
  await writeJson(outDir, "certificates.json", jobseekers.flatMap((j) => j.certificates));
  await writeJson(outDir, "work_experiences.json", jobseekers.flatMap((j) => j.work_experiences));
  await writeJson(outDir, "project_experiences.json", jobseekers.flatMap((j) => j.project_experiences));
  await writeJson(outDir, "jobseeker_has_skills.json", jobseekerSkillLinks);
  await writeJson(outDir, "pathways.json", pathways);
  await writeJson(outDir, "pathway_has_skills.json", pathwaySkillLinks);
  await writeJson(outDir, "skill_subcategories.json", skillSubcategories);
  await writeJson(outDir, "skills.json", skills);
  await writeJson(outDir, "job_postings.json", jobPostingsForSeed);

  meta.counts = {
    industry_sectors: industrySectors.length,
    technology_areas: technologyAreas.length,
    postal_geo_data: postalGeoData.length,
    users: users.length,
    companies: companies.length,
    company_addresses: companyAddresses.length,
    employers: employersForSeed.length,
    jobseekers: jobseekersForSeed.length,
    jobseekers_education: education.length,
    programs: programs.length,
    edu_providers: eduProviders.length,
    edu_addresses: eduAddresses.length,
    certificates: jobseekers.flatMap((j) => j.certificates).length,
    work_experiences: jobseekers.flatMap((j) => j.work_experiences).length,
    project_experiences: jobseekers.flatMap((j) => j.project_experiences).length,
    jobseeker_has_skills: jobseekerSkillLinks.length,
    pathways: pathways.length,
    pathway_has_skills: pathwaySkillLinks.length,
    skill_subcategories: skillSubcategories.length,
    skills: skills.length,
    job_postings: jobPostingsForSeed.length,
  };
  await writeJson(outDir, "metadata.json", meta);

  await prisma.$disconnect();
  console.log("export_ok", { outDir, counts: meta.counts });
}

await main();

