import { auth } from "@/auth";
import {
  JobseekerPoolVars,
  selectJobseekerPoolCategory,
  SelectJobseekerPoolCatResult,
} from "@/app/lib/poolAssignment";
import getPrismaClient from "@/app/lib/prismaClient.mjs";
import { Prisma, PrismaClient } from "@prisma/client";
import {
  CollegeDegreeType,
  EducationLevel,
  educationRank,
  HighestCompletedEducationLevel,
  HighSchoolDegreeType,
  ProgramEnrollmentStatus,
} from "@/data/dtos/JobSeekerProfileCreationDTOs";
import { devLog } from "@/app/lib/utils";
import { Role } from "@/data/dtos/UserInfoDTO";
import { v4 as uuidv4 } from "uuid";
import { CareerPrepPathways } from "./admin/careerPrep";
import { getAllIndustrySectors } from "./employer";
import { getTechnologyAreas } from "./prisma";
import { getSkillSubcategories } from "./admin/skill";
import { getCompletionsClient } from "./openAiClients";

const prisma: PrismaClient = getPrismaClient();

/**
 * Asynchronously aggregates jobseeker pool variables based on the provided jobseekerId.
 *
 * @param {string} jobseekerId - The unique identifier of the jobseeker.
 * @returns {Promise<JobseekerPoolVars>} - A Promise that resolves with the aggregated JobseekerPoolVars object.
 */
export const aggregateJobseekerPoolVars = async (
  jobseekerId: string,
): Promise<JobseekerPoolVars> => {
  if (!jobseekerId) {
    throw new TypeError(
      `A uuidv4 jobseekerId is required which is not present in session data`,
    );
  }

  // Fetch jobseeker education and work experience details
  const education = await prisma.jobseekers_education.findMany({
    where: {
      jobseekerId: jobseekerId,
    },
    select: {
      jobseekers: {
        select: {
          careerPrepComplete: true,
        },
      },
      enrollmentStatus: true,
      degreeType: true,
      eduProviders: {
        select: {
          isCoalitionMember: true, // Fetch isCoalitionMember flag
        },
      },
    },
  });

  const workExperience = await prisma.workExperience.findMany({
    where: {
      jobseekerId: jobseekerId,
    },
    select: {
      techArea: {
        select: {
          title: true,
        },
      },
    },
  });

  devLog("aggregated data:", { education, workExperience });

  // Evaluate the JobseekerPoolVars values based on the fetched data
  const jobseekerPoolVars: JobseekerPoolVars = {
    enrolledWithPartner: education.some(
      (edu) =>
        edu.eduProviders?.isCoalitionMember &&
        edu.enrollmentStatus === ProgramEnrollmentStatus.Enrolled,
    ),
    //TODO: include jobseeker/signup value instead
    completedPartnerProgram: education.some(
      (edu) =>
        edu.eduProviders?.isCoalitionMember &&
        edu.enrollmentStatus === ProgramEnrollmentStatus.Graduated,
    ),
    prevTechExperience: workExperience.some(
      (exp) =>
        exp.techArea &&
        exp.techArea.title &&
        exp.techArea.title !== "N/A Not an IT role",
    ),
    hasDegreeOrTechProgram: education.some(
      (edu) =>
        educationRank[edu.degreeType as HighestCompletedEducationLevel] >=
        educationRank[HighestCompletedEducationLevel.Certificate],
    ),
    // TODO: store Career Prep program completion in database.
    careerPrepComplete: education.some(
      (edu) => edu.jobseekers?.careerPrepComplete ?? false,
    ),
  };

  devLog("Calculated Pool Vars\n", jobseekerPoolVars);

  return jobseekerPoolVars;
};

/**
 * Updates the pool assignments for a jobseeker by unflagging the deletion of the assigned pools.
 *
 * @param {string} jobseekerId - The ID of the jobseeker.
 * @param {SelectJobseekerPoolCatResult} poolCategoryResult - The pool assignment details to update.
 * @returns {Promise<void>} - A Promise that resolves once the pool assignments are updated.
 */
const updatePool = async (
  jobseekerId: string,
  poolCategoryResult: SelectJobseekerPoolCatResult,
): Promise<void> => {
  await prisma.jobseekers.update({
    where: {
      jobseeker_id: jobseekerId,
    },
    data: {
      assignedPool: poolCategoryResult.poolAssignment,
      careerPrepTrackRecommendation:
        poolCategoryResult.careerPrepTrackRecommendation,
    },
  });
};

/**
 * Assigns a jobseeker session to a connection pool, if the user is authenticated.
 * @returns {Promise<NextResponse>} A promise that resolves to the next response after setting the pool with the session.
 */
export const setPoolWithSession = async (): Promise<void> => {
  const session = await auth();
  try {
    if (!session?.user?.jobseekerId) {
      throw new Error("No jobseeker id found in session");
    }
    const jobseekerId = session.user.jobseekerId;
    await setPool(jobseekerId);
  } catch (error: any) {
    console.error("Error setting jobseeker pool:", error);
    throw error;
  }
};

/**
 * Asynchronously sets the jobseeker pool for a given jobseeker ID.
 * This function aggregates jobseeker pool variables, selects the jobseeker pool category,
 * and updates the pool in the database.
 *
 * @param {string} jobseekerId - The ID of the jobseeker for whom the pool needs to be set.
 * @returns {Promise<NextResponse>} A Promise that resolves to a NextResponse object indicating the success or failure of setting the jobseeker pool.
 */
export const setPool = async (jobseekerId: string): Promise<void> => {
  try {
    await prisma.$transaction(async () => {
      const poolVars = await aggregateJobseekerPoolVars(jobseekerId);
      const categoryOutput = selectJobseekerPoolCategory(poolVars);
      await updatePool(jobseekerId, categoryOutput);
    });
  } catch (e: any) {
    // Log the error for debugging
    console.error("Error setting jobseeker pool:", e);
    throw new Error("Failed to set jobseeker pool. Please try again later.", e);
  }
};

export async function getPoolWithSession() {
  const session = await auth();

  try {
    if (session?.user.jobseekerId == null) {
      return;
    }
    const res = await prisma.jobseekers.findUnique({
      where: {
        jobseeker_id: session?.user.jobseekerId,
      },
      select: {
        assignedPool: true,
      },
    });
    return res;
  } catch (error) {
    console.error(error);
  }
}

export async function getCareerPrepAssementStatus() {
  try {
    const session = await auth();
    if (session?.user.jobseekerId == null) {
      return;
    }
    const res = await prisma.jobseekers.findUnique({
      where: {
        jobseeker_id: session?.user.jobseekerId,
      },
      select: {
        CareerPrepAssessment: {
          select: {
            assessmentDate: true,
          },
        },
      },
    });
    if (res == undefined) {
      return {
        CareerPrepAssessment: [],
      };
    }
    return res;
  } catch (error) {
    console.error(error);
  }
}

/**
 * Create a jobseeker (for an existing user) and associated data from the database.
 *
 * @param {string} userId - The ID of the user to become a jobseeker.
 * @param {object} checkboxes - {jobNotifications: boolean, opportunities: boolean, termsAgree: boolean}
 * @returns {Promise<jobseekers>}
 * @throws {Error} If user creation fails
 */
export async function createJobseeker(
  userId: string,
  checkboxes: {
    jobNotifications: boolean;
    opportunities: boolean;
    termsAgree: boolean;
  },
): Promise<Prisma.jobseekersGetPayload<object>> {
  const { jobNotifications, opportunities, termsAgree } = checkboxes;
  try {
    const result = await prisma.$transaction(async (prisma) => {
      await prisma.user.update({
        where: { id: userId },
        data: {
          role: Role.JOBSEEKER,
          has_agreed_terms: termsAgree,
          sendCareerOpportunities: opportunities,
          sendNewJobPosts: jobNotifications,
          updatedAt: new Date(),
        },
      });

      const jobseeker = await prisma.jobseekers.create({
        data: {
          jobseeker_id: uuidv4(),
          user_id: userId,
          is_enrolled_ed_program: false,
          intern_hours_required: 0,
          careerPrepComplete: false,
          createdAt: new Date(),
          updatedAt: new Date(),
        },
      });

      return jobseeker;
    });

    return result;
  } catch (error) {
    console.log(error);
    if (error instanceof Prisma.PrismaClientKnownRequestError) {
      // Handle known Prisma errors (e.g., unique constraint violations)
      if (error.code === "P2002") {
        throw new Error("A jobseeker profile already exists for this user");
      }
    }
    throw error;
  }
}

/**
 * Delete a jobseeker and associated data from the database.
 * If the jobseeker is a coalition member, perform a soft delete by marking deletion date.
 * If the jobseeker is not a coalition member, delete all related data to avoid foreign key constraints.
 * Check if the user has other roles and delete the user if no other roles exist.
 * If the user has other roles, update the user's role field to remove the jobseeker role.
 *
 * @param {string} userId - The ID of the user associated with the jobseeker to be deleted.
 * @returns {Promise<void>}
 */
export const deleteJobseeker = async (userId: string) => {
  // Find the jobseeker by userId
  const jobseeker = await prisma.jobseekers.findUnique({
    where: { user_id: userId },
  });

  if (!jobseeker) {
    throw new Error("User associated with jobseeker id not found");
  }

  const jobseeker_id = jobseeker.jobseeker_id;

  // Check if any EduProvider is a coalition member
  const coalitionMemberExists = await prisma.jobseekers_education.findFirst({
    where: {
      jobseekerId: jobseeker_id,
      eduProviders: {
        isCoalitionMember: true,
      },
    },
  });

  if (coalitionMemberExists) {
    // Perform soft delete
    await prisma.jobseekers.update({
      where: { jobseeker_id: jobseeker_id },
      data: { is_marked_deletion: new Date() },
    });
    return true;
  } else {
    try {
      // Start a transaction
      await prisma.$transaction(async (prisma) => {
        // Delete the jobseeker record
        await prisma.jobseekers.delete({ where: { user_id: userId } });

        // Fetch the user's roles
        const user = await prisma.user.findUnique({
          where: { id: userId },
          select: {
            role: true, // Returns string -> comma-separated list of roles
          },
        });

        if (!user) {
          throw new Error("User not found");
        }

        // Split the comma-separated list of roles and check for specific roles
        const userRolesArray: Role[] = user.role
          .split(",")
          .map((role: string) => role.trim() as Role);

        // Remove the JOBSEEKER role
        const filteredRolesArray = userRolesArray.filter(
          (role) => role !== Role.JOBSEEKER,
        );

        if (filteredRolesArray.length === 0) {
          // Delete the user if no roles are left
          await prisma.user.delete({ where: { id: userId } });
        } else {
          // Update the user's roles
          await prisma.user.update({
            where: { id: userId },
            data: { role: filteredRolesArray.join(",") },
          });
        }
      });
      return true;
    } catch (error) {
      console.error("Error deleting jobseeker: ", error);
      return false;
    }
  }
};

export const deleteJobseekerWithSession = async (): Promise<void> => {
  const session = await auth();
  try {
    const userId = session?.user.id;
    if (!userId) {
      throw new Error("User id not found in session. ");
    }
    await deleteJobseeker(userId);
  } catch (error: any) {
    console.error("Error deleting jobseeker with session:", error);
    throw error;
  }
};

export async function parseResumeText(resumeText: string) {
  const industry_sectors = (await getAllIndustrySectors()).flatMap(
    (industry) => industry.sector_title,
  );
  const technology_areas = (await getTechnologyAreas()).flatMap(
    (techArea) => techArea.title,
  );
  const skill_subcategories = (await getSkillSubcategories()).flatMap(
    (subcategory) => subcategory.subcategory_name,
  );

  try {
    const client = getCompletionsClient();
    const completion = await client.chat.completions.create({
      messages: [
        {
          role: "system",
          content: `Extract the resume information into the provided JSON schema.
          Ensure all specified fields in the schema are populated accurately based *only* on the provided resume text.
          If information for a specific field is not present in the text, use null or an empty string/array as appropriate for the field type,
          unless the field is marked as required in the schema, in which case, make the best possible inference.
          Make your best guess for degreeType, do not set it to the empty string. For projects, infer the skills used from the description.`,
        },
        {
          role: "user",
          content: resumeText,
        },
      ],
      response_format: {
        type: "json_schema",
        json_schema: {
          name: "ResumeExtractionResponse",
          // strict: true,
          description: "Schema for extracting structured data from a resume.",
          schema: {
            type: "object",
            properties: {
              generalInfo: {
                type: "object",
                description: "Contact information extracted from the resume.",
                properties: {
                  firstName: {
                    type: ["string", "null"],
                    description:
                      "The jobseeker's first name. Infer from 'YOUR NAME' if possible.",
                  },
                  lastName: {
                    type: ["string", "null"],
                    description:
                      "The jobseeker's last name. Infer from 'YOUR NAME' if possible.",
                  },
                  email: {
                    type: ["string", "null"],
                    format: "email",
                    description: "The jobseeker's email address.",
                  },
                  highestLevelOfStudyCompleted: {
                    type: "string",
                    enum: Object.values(HighestCompletedEducationLevel),
                  },
                  targetedPathway: {
                    type: ["string", "null"],
                    description:
                      "The specific career preparation pathway the user is interested in.",
                    enum: Object.values(CareerPrepPathways),
                  },
                  phone: {
                    type: ["string", "null"],
                    description: "The jobseeker's phone number.",
                  },
                  location: {
                    type: ["string", "null"],
                    description:
                      "The jobseeker's location (e.g., 'Hammond, LA'). Zip code might be separate or included here.",
                  },
                  linkedInUrl: {
                    type: ["string", "null"],
                    format: "uri",
                    description:
                      "URL to the jobseeker's LinkedIn profile, if available.",
                  },
                  portfolioUrl: {
                    type: ["string", "null"],
                    format: "uri",
                    description:
                      "URL to the jobseeker's personal portfolio or website (like GitHub), if available.",
                  },
                  videoUrl: {
                    type: ["string", "null"],
                    description:
                      "URL to a personal introduction, if available.",
                  },
                },
                required: [
                  "firstName",
                  "lastName",
                  "targetedPathway",
                  "highestLevelOfStudyCompleted",
                ],
                additionalProperties: false,
              },
              summary: {
                type: ["string", "null"],
                description:
                  "A brief professional summary or qualifications statement from the resume.",
              },
              workExperience: {
                type: "array",
                description:
                  "List of previous or current jobs held by the jobseeker.",
                items: {
                  type: "object",
                  properties: {
                    company: {
                      type: "string",
                      description: "Name of the company or organization.",
                    },
                    jobTitle: {
                      type: "string",
                      description: "Job title held.",
                    },
                    industrySector: {
                      type: "string",
                      enum: industry_sectors,
                    },
                    techArea: {
                      type: "string",
                      enum: technology_areas,
                    },
                    location: {
                      type: ["string", "null"],
                      description:
                        "Location of the job (e.g., 'Hammond, LA', 'Sydney, Australia').",
                    },
                    isInternship: {
                      type: "boolean",
                      description:
                        "True if the job is an intership, false otherwise.",
                    },
                    isCurrentJob: {
                      type: "boolean",
                      description:
                        "True if the job dates indicate it is the current job (e.g., end date is 'Present'). Default to false if unsure.",
                    },
                    startDate: {
                      type: "string",
                      format: "date",
                      description:
                        "Start date (e.g., 'August 2020', 'June 2019'). Use the format found in the text.",
                    },
                    endDate: {
                      type: ["string", "null"],
                      format: "date",
                      description:
                        "End date (e.g., 'Present', 'May 2021', 'August 2019'). Use the format found in the text. Null if not specified.",
                    },
                    responsibilities: {
                      type: "string",
                      description:
                        "Description of responsibilities and achievements, often presented as bullet points in the resume. Combine bullet points into a single string, perhaps separated by newlines.",
                    },
                  },
                  required: [
                    "company",
                    "jobTitle",
                    "isInternship",
                    "startDate",
                    "responsibilities",
                  ],
                  additionalProperties: false,
                },
              },
              projects: {
                type: "array",
                description:
                  "List of personal, academic, or professional projects.",
                items: {
                  type: "object",
                  properties: {
                    projectTitle: {
                      type: "string",
                      description:
                        "Name or title of the project (e.g., 'Tangi Humane Society Website'). Context might be needed (e.g. 'Web Programming Class project').",
                    },
                    projectRole: {
                      type: "string",
                      description:
                        "The jobseeker's role in the project (if specified).",
                    },
                    startDate: {
                      type: ["string", "null"],
                      format: "date",
                      description:
                        "Project start date (e.g., 'January 2020'). Use the format found in the text.",
                    },
                    completionDate: {
                      type: ["string", "null"],
                      format: "date",
                      description:
                        "Project completion date (e.g., 'June 2020'). Use the format found in the text.",
                    },
                    description: {
                      type: "string",
                      description:
                        "Description of the project, tasks performed, and achievements. Combine bullet points into a single string, perhaps separated by newlines.",
                    },
                    teamSize: {
                      type: "integer",
                      description:
                        "Number of people on the project team (if specified).",
                    },
                    repoUrl: {
                      type: "string",
                      format: "uri",
                      description:
                        "URL to the project's code repository (e.g., GitHub).",
                    },
                    demoUrl: {
                      type: "string",
                      format: "uri",
                      description:
                        "URL to a live demo or presentation of the project.",
                    },
                    skillsUsed: {
                      type: "array",
                      description:
                        "List of key skills or technologies used in the project mentioned in its description (e.g., 'Visual Basic', 'Java', 'HTML', 'Flash').",
                      items: {
                        type: "object",
                        properties: {
                          skillName: { type: "string" },
                          subcategory: {
                            type: "string",
                            enum: skill_subcategories,
                          },
                        },
                        uniqueItems: true,
                      },
                    },
                  },
                  required: ["projectTitle", "projectRole", "description"],
                  additionalProperties: false,
                },
              },
              education: {
                type: "array",
                description: "List of educational qualifications.",
                items: {
                  type: "object",
                  properties: {
                    institutionName: {
                      type: "string",
                    },
                    edLevel: {
                      type: "string",
                      enum: Object.values(EducationLevel),
                    },
                    degreeType: {
                      type: ["string", "null"],
                      enum:
                        Object.values(CollegeDegreeType) ||
                        Object.values(HighSchoolDegreeType),
                    },
                    enrollmentStatus: {
                      type: "string",
                      enum: Object.values(ProgramEnrollmentStatus),
                    },
                    isEnrolled: {
                      type: "boolean",
                    },
                    major: {
                      type: "string",
                      description: "Field of study (e.g., 'Computer Science').",
                    },
                    isTechDegree: {
                      type: "boolean",
                    },
                    startDate: {
                      type: ["string", "null"],
                      format: "date",
                      description: "Start date (e.g., YYYY or Month YYYY).",
                    },
                    endDate: {
                      type: ["string", "null"],
                      format: "date",
                      description:
                        "Graduation date (e.g., 'May 2021'). Use the format found in the text.",
                    },
                    gpa: {
                      type: ["string", "null"],
                      description:
                        "Grade Point Average, if mentioned (e.g., '3.84/4.00').",
                    },
                    description: {
                      type: ["string", "null"],
                      description:
                        "Additional details like Thesis title, scholarships, honors, relevant activities mentioned under education.",
                    },
                  },
                  required: [
                    "institutionName",
                    "degreeType",
                    "major",
                    "graduationDate",
                  ],
                  additionalProperties: false,
                },
              },
              certificates: {
                type: "array",
                description: "List of certifications .",
                items: {
                  type: "object",
                  properties: {
                    name: {
                      type: "string",
                      description:
                        "Name of the certification (e.g., 'AWS Certified Solutions Architect - Associate').",
                    },
                    issuingOrg: {
                      type: "string",
                      description:
                        "Name of the issuing organization (e.g., 'Amazon Web Services', 'Project Management Institute').",
                    },
                    credentialId: {
                      type: ["string", "null"],
                      description:
                        "Credential ID associated with the certification, if provided.",
                    },
                    credentialUrl: {
                      type: ["string", "null"],
                      format: "uri",
                      description:
                        "URL to the credential verification page or certificate details, if provided.",
                    },
                    issueDate: {
                      type: ["string", "null"],
                      format: "date",
                      description:
                        "Date the certification was issued (e.g., 'May 2020', '2021'). Use the format found in the text. Attempt to parse into YYYY-MM-DD if possible, otherwise keep original string.",
                    },
                    expiryDate: {
                      type: ["string", "null"],
                      format: "date",
                      description:
                        "Date the certification expires (e.g., 'May 2025', 'Does not expire'). Use the format found in the text. Attempt to parse into YYYY-MM-DD if possible, otherwise keep original string.",
                    },
                    description: {
                      type: ["string", "null"],
                      description:
                        "Any additional description or details provided about the certification.",
                    },
                  },
                  required: ["name", "issuingOrg"],
                  additionalProperties: false,
                },
              },
              skills: {
                type: "array",
                description: "List of technical skills.",
                items: {
                  type: "object",
                  properties: {
                    skillName: { type: "string" },
                    subcategory: {
                      type: "string",
                      enum: skill_subcategories,
                    },
                  },
                },
                uniqueItems: true,
              },
            },
            required: [
              "contactInfo",
              "workExperience",
              "education",
              "skills",
              "summary",
              "projects",
            ],
            additionalProperties: false,
          },
        },
      },
      model: "",
      max_completion_tokens: 32768,
      temperature: 0.2,
      stream: false,
    });
    return completion.choices[0]?.message?.content;
  } catch (error) {
    console.error("Error calling Azure OpenAI API:", error);
  }
}
