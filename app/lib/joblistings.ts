import { Prisma, PrismaClient } from "@prisma/client";
import getPrismaClient from "@/app/lib/prismaClient.mjs";

import { v4 as uuidv4 } from "uuid";
import { auth } from "@/auth";
import { JobPostCreationDTO } from "@/data/dtos/JobListingDTO";
import { NextResponse } from "next/server";
import { Role } from "@/data/dtos/UserInfoDTO";
import { JobStatus } from "./jobseekerJobTracking";
import { JobListingCardViewDTO } from "@/data/dtos/JobListingCardViewDTO";
// used singleton pattern to avoid connection timeouts due to reaching connection limit
const prisma: PrismaClient = getPrismaClient();
export async function createJobListingWithSkills(jobData: JobPostCreationDTO) {
  const Session = await auth();
  let company_id = Session?.user.companyId;
  if (
    Session?.user.roles.includes(Role.ADMIN) ||
    Session?.user.roles.includes(Role.CASE_MANAGER)
  ) {
    company_id = jobData.company_id;
  }
  if (
    !Session?.user.roles.includes(Role.ADMIN) &&
    Session?.user.roles.includes(Role.EMPLOYER)
  ) {
    if (!Session?.user.employeeIsApproved || !Session?.user.companyIsApproved) {
      throw new Error("Either company or employee not approved");
    }
  }
  try {
    if (!company_id) {
      throw new Error("Failed to create job listing Company id not found");
    }
    let companyAddress = await prisma.company_addresses.findFirst({
      where: {
        AND: {
          zip: jobData.zip,
          company_id: company_id,
        },
      },
    });
    if (!companyAddress) {
      companyAddress = await prisma.company_addresses.create({
        data: {
          company_id: company_id,
          company_address_id: uuidv4(),
          zip: jobData.zip,
        },
      });
    }

    const postalGeoData = await prisma.postalGeoData.findFirst({
      where: { zip: jobData.zip },
    });

    const now = new Date();
    const jobListingId = uuidv4();
    const newJobListing = await prisma.job_postings.create({
      data: {
        job_posting_id: jobListingId,
        company_id: company_id,
        location_id: companyAddress.company_address_id,
        tech_area_id: jobData.tech_area_id,
        sector_id: jobData.sector_id,
        employer_id: Session?.user.employerId ?? null,
        job_title: jobData.job_title,
        job_description: jobData.job_description,
        is_internship: jobData.is_internship ?? false,
        is_paid: jobData.is_paid ?? true,
        relocation_services_available: jobData.relocation_services_available,
        offer_visa_sponsorship: jobData.offer_visa_sponsorship,
        zip: jobData.zip,
        employment_type: jobData.employment_type || "full-time",
        is_apprenticeship: jobData.is_apprenticeship,
        location: jobData.location,
        salary_range: jobData.salary_range,
        county: postalGeoData?.county ?? "",
        publish_date: now,
        unpublish_date:
          jobData.unpublish_date ??
          new Date(now.getFullYear() + 1, now.getMonth(), now.getDate()), //if closing date is not provided auto set to 1 year in the futrue
        job_post_url: jobData.job_post_url,
        assessment_url: jobData.assessment_url,
        earn_and_learn_type: jobData.earn_and_learn_type,
        occupation_code: jobData.occupation_code,
        employment_duration: jobData.employment_duration,
        start_date: jobData.start_date,
        end_date: jobData.end_date,
        career_services_offered:
          Session?.user.roles.includes(Role.ADMIN) ||
          Session?.user.roles.includes(Role.CASE_MANAGER)
            ? jobData.career_services_offered
            : true,
        trainingRequirements: jobData.trainingRequirements,
        requiredCertifications: jobData.requiredCertifications,
        minimumEducationLevel: jobData.minimumEducationLevel,
        skills: {
          connect: jobData.skillIds?.map((skillId: string) => ({
            skill_id: skillId,
          })),
        },
      },
      include: {
        industry_sectors: true,
        techArea: true,
        companies: true,
        skills: true,
      },
    });

    return newJobListing;
  } catch (error) {
    console.error("Error creating job listing with skills:", error);
    // throw new Error('Failed to create job listing with associated skills');
  }
}
export async function updateJobListing(jobData: JobPostCreationDTO) {
  if (!jobData.job_posting_id) {
    return;
  }
  const Session = await auth();
  let company_id = Session?.user.companyId;
  if (
    Session?.user.roles.includes(Role.ADMIN) ||
    Session?.user.roles.includes(Role.CASE_MANAGER)
  ) {
    company_id = jobData.company_id;
  }
  if (
    !Session?.user.roles.includes(Role.ADMIN) &&
    Session?.user.roles.includes(Role.EMPLOYER)
  ) {
    if (!Session?.user.employeeIsApproved || !Session?.user.companyIsApproved) {
      throw new Error("Either company or employee not approved");
    }
  }
  const now = new Date();
  try {
    if (!company_id) {
      throw new Error("Failed to create job listing Company id not found");
    }
    let companyAddress = await prisma.company_addresses.findFirst({
      where: {
        AND: {
          zip: jobData.zip,
          company_id: company_id,
        },
      },
    });
    if (!companyAddress) {
      companyAddress = await prisma.company_addresses.create({
        data: {
          company_id: company_id,
          company_address_id: uuidv4(),
          zip: jobData.zip,
        },
      });
    }
    const postalGeoData = await prisma.postalGeoData.findFirst({
      where: { zip: jobData.zip },
    });

    const res = await prisma.job_postings.update({
      where: {
        job_posting_id: jobData.job_posting_id,
      },
      data: {
        job_posting_id: jobData.job_posting_id,
        company_id: company_id,
        location_id: companyAddress.company_address_id,
        tech_area_id: jobData.tech_area_id,
        sector_id: jobData.sector_id,
        employer_id: Session?.user.employerId ?? null,
        job_title: jobData.job_title,
        job_description: jobData.job_description,
        is_internship: jobData.is_internship ?? false,
        is_paid: jobData.is_paid ?? true,
        relocation_services_available: jobData.relocation_services_available,
        offer_visa_sponsorship: jobData.offer_visa_sponsorship,
        zip: jobData.zip,
        employment_type: jobData.employment_type || "full-time",
        earn_and_learn_type: jobData.earn_and_learn_type,
        is_apprenticeship: jobData.is_apprenticeship,
        location: jobData.location,
        career_services_offered:
          Session?.user.roles.includes(Role.ADMIN) ||
          Session?.user.roles.includes(Role.CASE_MANAGER)
            ? jobData.career_services_offered
            : undefined,
        salary_range: jobData.salary_range,
        county: postalGeoData?.county ?? "",
        publish_date: now,
        unpublish_date:
          jobData.unpublish_date ??
          new Date(now.getFullYear() + 1, now.getMonth(), now.getDate()), //if closing date is not provided auto set to 1 year in the futrue
        employment_duration: jobData.employment_duration,
        start_date: jobData.start_date,
        end_date: jobData.end_date,
        job_post_url: jobData.job_post_url,
        assessment_url: jobData.assessment_url,
        occupation_code: jobData.occupation_code,
        trainingRequirements: jobData.trainingRequirements,
        requiredCertifications: jobData.requiredCertifications,
        minimumEducationLevel: jobData.minimumEducationLevel,
        skills: {
          set: jobData.skillIds?.map((skillId: string) => ({
            skill_id: skillId,
          })),
        },
      },
      include: {
        industry_sectors: true,
        techArea: true,
        companies: true,
        skills: true,
      },
    });
    return res;
  } catch (error) {
    console.log(error);
  }
}
export async function getJobListingById(
  joblistingId: string,
  jobseekerId?: string,
) {
  try {
    const include: any = {
      skills: true,
      industry_sectors: {
        select: {
          sector_title: true,
        },
      },
      company_addresses: {
        include: {
          locationData: true,
        },
      },
      companies: true,
      techArea: {
        select: {
          title: true,
        },
      },
    };

    if (jobseekerId) {
      include.jobApplications = {
        where: { jobseekerId },
        select: {
          isBookmarked: true,
          jobPostId: true,
          jobseekerId: true,
          jobStatus: true,
        },
      };
    }

    const joblisting = await prisma.job_postings.findUnique({
      where: {
        job_posting_id: joblistingId,
      },
      include,
    });
    return joblisting;
  } catch (e) {
    console.error(e);
  }
}
export async function getCompanyJobListings() {
  const Session = await auth();
  if (!Session?.user.roles.includes(Role.EMPLOYER)) {
    throw new Error("User is not an employer");
  }
  if (!Session?.user.companyId) {
    throw new Error("Employee not part of a company");
  }
  if (!Session?.user.employeeIsApproved) {
    throw new Error("Employee not approved");
  }
  if (!Session?.user.companyIsApproved) throw new Error("Company not approved");
  try {
    const results = await prisma.job_postings.findMany({
      where: {
        company_id: Session?.user.companyId,
      },
      include: {
        industry_sectors: true,
        techArea: true,
        companies: true,
        skills: true,
        jobApplications: {
          where: {
            jobStatus: {
              in: [
                JobStatus.Recommended,
                JobStatus.Interviewing,
                JobStatus.Negotiating,
              ],
            },
          },
          include: {
            Jobseekers: {
              include: {
                users: true,
                pathways: true,
                jobseeker_has_skills: {
                  include: {
                    skills: true,
                  },
                },
              },
            },
          },
        },
      },
    });
    return results;
  } catch (e) {
    console.error(e);
    return [];
  }
}
export async function getMyJobListings() {
  const Session = await auth();
  if (!Session?.user.employerId) {
    throw new Error(
      "Failed to create job listing employer id not found in session",
    );
  }
  try {
    const results = await prisma.job_postings.findMany({
      where: {
        employer_id: Session?.user.employerId,
      },
      include: {
        industry_sectors: true,
        techArea: true,
        companies: true,
        skills: true,
        jobApplications: {
          where: {
            jobStatus: {
              in: [
                JobStatus.Recommended,
                JobStatus.Interviewing,
                JobStatus.Negotiating,
              ],
            },
          },
          include: {
            Jobseekers: {
              include: {
                users: true,
                pathways: true,
                jobseeker_has_skills: {
                  include: {
                    skills: true,
                  },
                },
              },
            },
          },
        },
      },
    });
    return results;
  } catch (e) {
    console.error(e);
    return [];
  }
}
export async function deleteJobListing(jobPostingId: string) {
  const Session = await auth();
  if (!Session?.user.employerId && !Session?.user.roles.includes(Role.ADMIN)) {
    throw new Error(
      "Failed to delete job listing: employer ID not found in session",
    );
  }
  if (!Session.user.companyId && !Session?.user.roles.includes(Role.ADMIN)) {
    throw new Error(
      "Failed to delete job listing: company ID not found in session",
    );
  }
  if (!Session?.user.employeeIsApproved) {
    throw new Error("Employee not approved");
  }

  try {
    const job = await prisma.job_postings.findUnique({
      where: {
        job_posting_id: jobPostingId,
      },
    });
    if (
      job?.company_id != Session.user.companyId &&
      !Session?.user.roles.includes(Role.ADMIN)
    ) {
      throw new Error("not an employer of this company");
    }
    const result = await prisma.job_postings.delete({
      where: {
        job_posting_id: jobPostingId,
      },
    });
    return result;
  } catch (e) {
    console.error(e);
  }
}

export async function ApplyToJob(jobPostingId: string) {
  const Session = await auth();
  try {
    if (!Session?.user.jobseekerId) {
      throw new Error(
        "Failed to apply to job: jobseeker ID not found in session",
      );
    }

    const jobPosting = await prisma.job_postings.findUnique({
      where: { job_posting_id: jobPostingId },
    });

    if (!jobPosting) {
      throw new Error("Job posting not found");
    }

    const currentDate = new Date();
    if (currentDate > jobPosting.unpublish_date) {
      throw new Error("Cannot apply to job: the unpublish date has passed");
    }

    const existingApplication = await prisma.jobseekerJobPosting.findFirst({
      where: {
        jobPostId: jobPostingId,
        jobseekerId: Session.user.jobseekerId,
      },
    });

    if (existingApplication) {
      if (
        existingApplication.jobStatus.length !== 0 &&
        existingApplication.jobStatus !== JobStatus.Applied &&
        existingApplication.jobStatus !== JobStatus.IWithdrew
      ) {
        throw new Error(
          " Cannot change job status to apply: application is already being processed.",
        );
      }
      return await prisma.jobseekerJobPosting.update({
        where: {
          id: existingApplication.id,
        },
        data: {
          jobStatus: JobStatus.Applied,
          appliedDate: new Date(),
        },
        include: {
          job_posting: {
            include: {
              companies: true,
            },
          },
          Jobseekers: {
            include: {
              users: true,
            },
          },
        },
      });
    } else {
      return await prisma.jobseekerJobPosting.create({
        data: {
          id: uuidv4(),
          jobPostId: jobPostingId,
          jobseekerId: Session.user.jobseekerId,
          jobStatus: JobStatus.Applied,
          appliedDate: new Date(),
          isBookmarked: false,
        },
        include: {
          job_posting: {
            include: {
              companies: true,
            },
          },
          Jobseekers: {
            include: {
              users: {
                select: {
                  first_name: true,
                  last_name: true,
                },
              },
            },
          },
        },
      });
    }
  } catch (error) {
    console.error("Error in ApplyToJob:", error);
    throw error;
  }
}

export async function WithdrawFromJob(jobPostingId: string) {
  const Session = await auth();
  try {
    if (!Session?.user.jobseekerId) {
      throw new Error(
        "Failed to Withdraw from job: jobseeker ID not found in session",
      );
    }

    const jobPosting = await prisma.job_postings.findUnique({
      where: { job_posting_id: jobPostingId },
    });

    if (!jobPosting) {
      throw new Error("Job posting not found");
    }

    const currentDate = new Date();
    if (currentDate > jobPosting.unpublish_date) {
      throw new Error("Cannot withdraw from job: unpublish date has passed");
    }

    const existingApplication = await prisma.jobseekerJobPosting.findFirst({
      where: {
        jobPostId: jobPostingId,
        jobseekerId: Session.user.jobseekerId,
      },
    });

    if (existingApplication) {
      if (
        existingApplication.jobStatus.length !== 0 &&
        existingApplication.jobStatus !== JobStatus.Applied &&
        existingApplication.jobStatus !== JobStatus.IWithdrew
      ) {
        throw new Error(
          " Cannot withdraw from job: application is already being processed.",
        );
      }
      return await prisma.jobseekerJobPosting.update({
        where: {
          id: existingApplication.id,
        },
        data: {
          jobStatus: JobStatus.IWithdrew,
          appliedDate: new Date(),
        },
      });
    } else {
      return await prisma.jobseekerJobPosting.create({
        data: {
          id: uuidv4(),
          jobPostId: jobPostingId,
          jobseekerId: Session.user.jobseekerId,
          jobStatus: JobStatus.IWithdrew,
          appliedDate: new Date(),
          isBookmarked: false,
        },
      });
    }
  } catch (error) {
    console.error("Error in WithdrawFromJob:", error);
    throw error;
  }
}

export async function bookmarkJobPosting(jobPostId: string) {
  const Session = await auth();
  try {
    if (!Session?.user.jobseekerId) {
      throw new Error("Failed to bookmark: jobseeker ID not found in session");
    }
    const existingRecord = await prisma.jobseekerJobPosting.findFirst({
      where: {
        jobPostId: jobPostId,
        jobseekerId: Session.user.jobseekerId,
      },
    });

    if (existingRecord) {
      return await prisma.jobseekerJobPosting.update({
        where: {
          id: existingRecord.id,
        },
        data: {
          isBookmarked: true,
          savedAt: new Date(),
        },
      });
    } else {
      return await prisma.jobseekerJobPosting.create({
        data: {
          id: uuidv4(),
          jobPostId: jobPostId,
          jobseekerId: Session.user.jobseekerId,
          isBookmarked: true,
          jobStatus: "",
          savedAt: new Date(),
        },
      });
    }
  } catch (error) {
    if (error instanceof Prisma.PrismaClientKnownRequestError) {
      console.error("Prisma error:", error);
      if (error.code === "P2002") {
        return NextResponse.json(
          { error: "Unique constraint violation. This data already exists." },
          { status: 409 },
        );
      }
      return NextResponse.json(
        { error: `Failed to bookmark job post: ${error.message}` },
        { status: 500 },
      );
    }
    throw error;
  }
}
export async function unbookmarkJobPosting(jobPostId: string) {
  const Session = await auth();
  try {
    if (!Session?.user.jobseekerId) {
      throw new Error(
        "Failed to unbookmark: jobseeker ID not found in session",
      );
    }

    const existingRecord = await prisma.jobseekerJobPosting.findFirst({
      where: {
        jobPostId: jobPostId,
        jobseekerId: Session.user.jobseekerId,
      },
    });

    if (!existingRecord) {
      return NextResponse.json({ error: "Record not found" }, { status: 404 });
    }

    if (existingRecord.jobStatus !== "") {
      return await prisma.jobseekerJobPosting.update({
        where: {
          id: existingRecord.id,
        },
        data: {
          isBookmarked: false,
        },
      });
    } else {
      return await prisma.jobseekerJobPosting.delete({
        where: {
          id: existingRecord.id,
        },
      });
    }
  } catch (error) {
    console.error("Error in unbookmarkJobPosting:", error);
    throw error;
  }
}

export async function getAllJobPosts() {
  try {
    const results = prisma.job_postings.findMany({
      include: {
        jobApplications: {
          include: {
            Jobseekers: {
              include: {
                users: true,
              },
            },
          },
        },
        companies: true,
        skills: true,
      },
    });
    return results;
  } catch (error) {
    console.error(error);
  }
}

export async function getJobListingsFiltered(request: Request) {
  const session = await auth();
  const jobseekerId = session?.user?.jobseekerId;

  const {
    jobTitle = "",
    bookmarked = false,
    skills = [],
    city = [],
    profession = "",
    careerServicesOffered = false,
    industrySector = [],
    employmentType = [],
    sortBy = "publish_date", // eslint-disable-line @typescript-eslint/no-unused-vars
    page = 1,
    maxResults = 50,
  } = await request.json();

  const andConditions: any[] = [];
  const orderBy = [
    { career_services_offered: "desc" as const },
    { publish_date: "desc" as const },
  ];
  // Determine the number of results to skip based on the page number and maxResults
  const skip = (page - 1) * maxResults;

  const normalizedSkills: string[] = skills.filter(
    (skill: string) => skill && skill.trim() !== "",
  );

  andConditions.push({
    unpublish_date: { gte: new Date() },
  });

  if (bookmarked) {
    if (!jobseekerId) {
      return {
        filteredJobPostings: [],
        totalCount: 0,
      };
    }
    andConditions.push({
      jobApplications: {
        some: {
          jobseekerId: jobseekerId,
          isBookmarked: true,
        },
      },
    });
  }

  if (jobTitle) {
    andConditions.push({
      job_title: {
        contains: jobTitle,
      },
    });
  }

  if (normalizedSkills.length > 0) {
    const orConditions = [
      {
        skills: {
          some: {
            skill_name: {
              in: normalizedSkills,
            },
          },
        },
      },
    ];
    andConditions.push({ OR: orConditions });
  }

  if (industrySector.length > 0) {
    andConditions.push({
      industry_sectors: {
        sector_title: {
          in: industrySector,
        },
      },
    });
  }

  if (employmentType.length > 0) {
    andConditions.push({
      employment_type: {
        in: employmentType,
      },
    });
  }

  if (profession.length > 0) {
    andConditions.push({
      techArea: {
        title: {
          equals: profession,
        },
      },
    });
  }

  andConditions.push({
    career_services_offered: {
      equals: careerServicesOffered === true ? true : undefined,
    },
  });

  if (city.length > 0) {
    andConditions.push({
      company_addresses: {
        locationData: {
          city: {
            in: city,
          },
        },
      },
    });
  }

  const [filteredJobPostings, totalCount] = await prisma.$transaction([
    prisma.job_postings.findMany({
      where: andConditions.length > 0 ? { AND: andConditions } : undefined,
      include: {
        skills: true,
        industry_sectors: {
          select: {
            sector_title: true,
          },
        },
        companies: true,
        techArea: {
          select: {
            title: true,
          },
        },
        company_addresses: {
          include: {
            locationData: true,
          },
        },
        jobApplications: jobseekerId
          ? {
              where: {
                jobseekerId: jobseekerId,
              },
              select: {
                jobStatus: true,
                isBookmarked: true,
              },
            }
          : false,
      },
      take: maxResults,
      skip: skip,
      orderBy: orderBy,
    }),
    prisma.job_postings.count({
      where: andConditions.length > 0 ? { AND: andConditions } : undefined,
    }),
  ]);

  const transformedJobPostings = filteredJobPostings.map((posting) => {
    if (posting.jobApplications && posting.jobApplications.length > 0) {
      const jobStatus = posting.jobApplications?.[0].jobStatus;
      const isBookmarked = posting.jobApplications?.[0].isBookmarked || false;
      return {
        ...posting,
        jobStatus: jobStatus,
        isBookmarked: isBookmarked,
        jobApplications: undefined,
      };
    }
    return {
      ...posting,
    };
  });
  return {
    filteredJobPostings: transformedJobPostings,
    totalCount,
  };
}

export async function getJobSeekerBookmarkedJobs() {
  const session = await auth();
  if (!session?.user.jobseekerId) {
    return;
  }
  try {
    const result = await prisma.jobseekerJobPosting.findMany({
      include: {
        job_posting: {
          include: {
            companies: true,
            skills: true,
            industry_sectors: {
              select: {
                sector_title: true,
              },
            },
          },
        },
      },
      where: {
        jobseekerId: session.user.jobseekerId,
        job_posting: { unpublish_date: { gte: new Date() } },
        isBookmarked: true,
      },
    });

    const transformedJobPostings = result.map((posting) => {
      const jobStatus = posting.jobStatus;
      const isBookmarked = posting.isBookmarked || false;
      return {
        ...posting.job_posting,
        jobStatus: jobStatus,
        isBookmarked: isBookmarked,
        jobApplications: undefined,
      };
    });

    return transformedJobPostings;
  } catch (error) {
    console.error(error);
  }
}

export async function getJobSeekerAppliedJobs() {
  // fixme: will probably want to get all jobs...
  const session = await auth();
  if (!session?.user.jobseekerId) {
    return;
  }
  try {
    const result = await prisma.jobseekerJobPosting.findMany({
      where: {
        jobseekerId: session.user.jobseekerId,
      },
      include: {
        job_posting: {
          include: {
            companies: true,
            skills: true,
            industry_sectors: {
              select: {
                sector_title: true,
              },
            },
          },
        },
      },
    });

    const transformedJobPostings = result
      .filter((posting) => posting.jobStatus !== "")
      .map((posting) => ({
        ...posting.job_posting,
        jobStatus: posting.jobStatus,
        isBookmarked: posting.isBookmarked || false,
        jobApplications: undefined,
      })) as JobListingCardViewDTO[];

    return transformedJobPostings;
  } catch (error) {
    console.error(error);
  }
}

export async function feedbackToCandidate(
  jobseekerJobPostingId: string,
  rating: number,
  comment: string,
) {
  const session = await auth();
  if (!session?.user.employeeIsApproved || !session?.user.employerId) {
    return;
  }
  try {
    const jobseekerJobPosting = await prisma.jobseekerJobPosting.findUnique({
      where: {
        id: jobseekerJobPostingId,
      },
    });
    if (!jobseekerJobPosting) {
      throw new Error("No jobseeker job posting exists for the given id");
    }
    const job_posting = await prisma.job_postings.findUnique({
      where: {
        job_posting_id: jobseekerJobPosting.jobPostId,
      },
    });
    if (job_posting?.company_id !== session?.user.companyId) {
      throw new Error("Employer not from company that posted the job");
    }
    const result = await prisma.jobseekerJobPosting.update({
      where: {
        id: jobseekerJobPostingId,
      },
      data: {
        jobStatus: JobStatus.NotSelected,
        feedbackRating: rating,
        feedbackText: comment,
      },
    });

    return result;
  } catch (error) {
    console.error(error);
  }
}

export async function setJobStatus(
  jobPostingId: string,
  applicationId: string,
  jobStatus: JobStatus,
) {
  const session = await auth();
  const is_admin_or_case_manager =
    session?.user.roles.includes(Role.ADMIN) ||
    session?.user.roles.includes(Role.CASE_MANAGER);
  if (
    (!session?.user.employeeIsApproved || !session?.user.employerId) &&
    !is_admin_or_case_manager
  ) {
    return;
  }
  if (
    session?.user.roles.includes(Role.EMPLOYER) &&
    !is_admin_or_case_manager
  ) {
    if (
      jobStatus !== JobStatus.Interviewing &&
      jobStatus !== JobStatus.Negotiating &&
      jobStatus !== JobStatus.Accepted
    )
      return;
  }
  try {
    const job_posting = await prisma.job_postings.findUnique({
      where: {
        job_posting_id: jobPostingId,
      },
    });
    if (
      job_posting?.company_id !== session?.user.companyId &&
      !is_admin_or_case_manager
    ) {
      throw new Error("Employer not from company that posted the job");
    }
    const result = await prisma.jobseekerJobPosting.update({
      where: {
        id: applicationId,
      },
      data: {
        jobStatus: jobStatus,
      },
    });

    return result;
  } catch (error) {
    console.error(error);
  }
}

export async function setEmployerConnect(
  jobPostingId: string,
  applicationId: string,
  status: boolean,
) {
  const session = await auth();
  const is_admin_or_case_manager =
    session?.user.roles.includes(Role.ADMIN) ||
    session?.user.roles.includes(Role.CASE_MANAGER);
  if (
    (!session?.user.employeeIsApproved || !session?.user.employerId) &&
    !is_admin_or_case_manager
  ) {
    return;
  }
  if (
    session?.user.roles.includes(Role.EMPLOYER) &&
    !is_admin_or_case_manager
  ) {
    if (status == false) return;
  }
  try {
    const job_posting = await prisma.job_postings.findUnique({
      where: {
        job_posting_id: jobPostingId,
      },
    });
    if (
      job_posting?.company_id !== session?.user.companyId &&
      !is_admin_or_case_manager
    ) {
      throw new Error("Employer not from company that posted the job");
    }
    const result = await prisma.jobseekerJobPosting.update({
      where: {
        id: applicationId,
      },
      data: {
        employerClickedConnect: status,
      },
    });

    return result;
  } catch (error) {
    console.error(error);
  }
}
