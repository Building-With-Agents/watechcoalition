import { NextResponse } from "next/server";
import { Prisma, PrismaClient } from "@prisma/client";
import getPrismaClient from "@/app/lib/prismaClient.mjs";
import { auth } from "@/auth";
import {
  getIndustrySectors,
  getTechnologyAreas,
  vectorSearchSkills,
} from "@/app/lib/prisma";
import { ProgramEnrollmentStatus } from "@/data/dtos/JobSeekerProfileCreationDTOs";
import { v4 as uuidv4 } from "uuid";

const prisma: PrismaClient = getPrismaClient();

function parseDateInput(dateInput: string | Date | null | undefined): Date {
  if (dateInput === null || dateInput === undefined) {
    return new Date();
  }

  if (dateInput instanceof Date) {
    if (!isNaN(dateInput.getTime())) {
      return dateInput;
    } else {
      console.warn(
        `Invalid Date object encountered during parsing. Returning current date.`,
      );
      return new Date();
    }
  }

  if (typeof dateInput === "string") {
    const trimmedInput = dateInput.trim();

    if (trimmedInput === "") {
      return new Date();
    }

    const lowerTrimmed = trimmedInput.toLowerCase();
    if (lowerTrimmed === "present" || lowerTrimmed === "current") {
      return new Date();
    }

    const mmYYYYRegex = /^\s*(\d{1,2})\/(\d{4})\s*$/;
    const matchMmYyyy = trimmedInput.match(mmYYYYRegex);
    if (matchMmYyyy) {
      const month = parseInt(matchMmYyyy[1], 10);
      const year = parseInt(matchMmYyyy[2], 10);
      if (month >= 1 && month <= 12 && year > 1900 && year < 3000) {
        const potentialDate = new Date(Date.UTC(year, month - 1, 1));
        if (!isNaN(potentialDate.getTime())) {
          return potentialDate;
        } else {
          console.warn(
            `Could not create valid date from MM/YYYY: ${trimmedInput}. Returning current date.`,
          );
          return new Date();
        }
      } else {
        console.warn(
          `Invalid month or year in MM/YYYY: ${trimmedInput}. Returning current date.`,
        );
        return new Date();
      }
    }

    try {
      const potentialDate = new Date(trimmedInput);
      if (!isNaN(potentialDate.getTime())) {
        return potentialDate;
      } else {
        console.warn(
          `Could not parse date string: "${trimmedInput}". Returning current date.`,
        );
        return new Date();
      }
    } catch (error) {
      console.warn(
        `Error parsing date string: "${trimmedInput}". Returning current date.`,
        error,
      );
      return new Date();
    }
  }
  console.warn(
    `Unexpected input type encountered: ${typeof dateInput}. Returning current date.`,
  );
  return new Date();
}

async function findPathwayId(
  pathwayTitle: string | null | undefined,
): Promise<string | null> {
  if (!pathwayTitle) return null;
  try {
    const pathway = await prisma.pathways.findUnique({
      where: { pathway_title: pathwayTitle },
      select: { pathway_id: true },
    });
    return pathway?.pathway_id ?? null;
  } catch (error) {
    console.error(
      `Error finding pathway ID for title "${pathwayTitle}":`,
      error,
    );
    return null;
  }
}

async function findOrCreateEduProvider(
  institutionName: string,
): Promise<string | null> {
  if (!institutionName) return null;
  try {
    const provider = await prisma.edu_providers.upsert({
      where: { name: institutionName },
      update: {},
      create: {
        name: institutionName,
        isAdminReviewed: false,
        isCoalitionMember: false,
      },
      select: { id: true },
    });
    return provider.id;
  } catch (error) {
    console.error(
      `Error finding or creating education provider "${institutionName}":`,
      error,
    );
    return null;
  }
}

interface AiGeneralInfo {
  firstName: string | null;
  lastName: string | null;
  yearsOfWorkExperience: number;
  email: string | null;
  targetedPathway: string | null;
  highestLevelOfStudy: string | null;
  phone: string | null;
  location: string | null;
  linkedInUrl: string | null;
  portfolioUrl: string | null;
  videoUrl: string | null;
}

interface AiWorkExperience {
  company: string;
  jobTitle: string;
  location: string | null;
  isInternship: boolean;
  isCurrentJob: boolean;
  startDate: string | null;
  endDate: string | null;
  techArea: string;
  industrySector: string;
  responsibilities: string | null;
}

interface AiProject {
  projectTitle: string;
  projectRole: string | null;
  startDate: string | null;
  completionDate: string | null;
  description: string | null;
  teamSize: number | null;
  repoUrl: string | null;
  demoUrl: string | null;
  skillsUsed: { skillName: string; subcategory: string }[];
}

interface AiEducation {
  institutionName: string;
  location: string | null;
  edLevel: string;
  degreeType: string;
  major: string;
  enrollmentStatus: string;
  isEnrolled: boolean;
  startDate: string | null;
  endDate: string | null;
  isTechDegree: boolean;
  gpa: string | null;
  description: string | null;
}

interface AiCertificate {
  name: string;
  issuingOrg: string | null;
  credentialId: string | null;
  credentialUrl: string | null;
  issueDate: string | null;
  expiryDate: string | null;
  description: string | null;
}

interface AiResumeData {
  generalInfo: AiGeneralInfo;
  summary: string | null;
  workExperience: AiWorkExperience[];
  projects: AiProject[];
  education: AiEducation[];
  certificates: AiCertificate[];
  skills: { skillName: string; subcategory: string }[];
}

export async function POST(request: Request) {
  try {
    const session = await auth();
    if (!session?.user?.id || !session?.user?.jobseekerId) {
      console.error("AI Upsert: Unauthorized - Session or IDs missing");
      return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
    }
    const userId: string = session.user.id;
    const jobseekerId: string = session.user.jobseekerId;

    const body: AiResumeData = await request.json();

    const result = await prisma.$transaction(
      async (tx) => {
        const user = await tx.user.update({
          where: { id: userId },
          data: {
            first_name: body.generalInfo.firstName,
            last_name: body.generalInfo.lastName,
            phone: body.generalInfo.phone,
            updatedAt: new Date(),
          },
        });

        const pathwayId = await findPathwayId(body.generalInfo.targetedPathway);

        let linkedInOriginalUrl = body.generalInfo.linkedInUrl;
        let linkedInFinalUrl = "";
        if (linkedInOriginalUrl && typeof linkedInOriginalUrl === "string") {
          linkedInOriginalUrl = linkedInOriginalUrl.trim();
          if (linkedInOriginalUrl.startsWith("https://")) {
            linkedInFinalUrl = linkedInOriginalUrl;
          } else if (linkedInOriginalUrl.startsWith("http://")) {
            linkedInFinalUrl = linkedInOriginalUrl.replace(/^http:/, "https:");
          } else if (linkedInOriginalUrl.length > 0) {
            linkedInFinalUrl = "https://" + linkedInOriginalUrl;
          }
        }

        let portfolioOriginalUrl = body.generalInfo.portfolioUrl;
        let portfolioFinalUrl = "";
        if (portfolioOriginalUrl && typeof portfolioOriginalUrl === "string") {
          portfolioOriginalUrl = portfolioOriginalUrl.trim();
          if (portfolioOriginalUrl.startsWith("https://")) {
            portfolioFinalUrl = portfolioOriginalUrl;
          } else if (portfolioOriginalUrl.startsWith("http://")) {
            portfolioFinalUrl = portfolioOriginalUrl.replace(
              /^http:/,
              "https:",
            );
          } else if (portfolioOriginalUrl.length > 0) {
            portfolioFinalUrl = "https://" + portfolioOriginalUrl;
          }
        }

        let videoUrlOriginalUrl = body.generalInfo.videoUrl;
        let videoUrlFinalUrl = "";
        if (videoUrlOriginalUrl && typeof videoUrlOriginalUrl === "string") {
          videoUrlOriginalUrl = videoUrlOriginalUrl.trim();
          if (videoUrlOriginalUrl.startsWith("https://")) {
            videoUrlFinalUrl = videoUrlOriginalUrl;
          } else if (videoUrlOriginalUrl.startsWith("http://")) {
            videoUrlFinalUrl = videoUrlOriginalUrl.replace(/^http:/, "https:");
          } else if (videoUrlOriginalUrl.length > 0) {
            videoUrlFinalUrl = "https://" + videoUrlOriginalUrl;
          }
        }

        await tx.jobseekers.upsert({
          where: { user_id: userId },
          update: {
            intro_headline: body.summary,
            linkedin_url: linkedInFinalUrl,
            portfolio_url: portfolioFinalUrl,
            video_url: videoUrlFinalUrl,
            highest_level_of_study_completed:
              body.generalInfo.highestLevelOfStudy,
            targeted_pathway: pathwayId,
            updatedAt: new Date(),
          },
          create: {
            jobseeker_id: jobseekerId,
            user_id: userId,
            targeted_pathway: pathwayId,
            is_enrolled_ed_program: false,
            intro_headline: body.summary,
            linkedin_url: linkedInFinalUrl,
            portfolio_url: portfolioFinalUrl,
            video_url: videoUrlFinalUrl,
            createdAt: new Date(),
          },
          select: { jobseeker_id: true },
        });

        await tx.workExperience.deleteMany({
          where: { jobseekerId: jobseekerId },
        });

        let currentJobTitle: string | null = null;
        if (body.workExperience && body.workExperience.length > 0) {
          const workExperiencesToCreate: Prisma.WorkExperienceCreateManyInput[] =
            [];
          for (const exp of body.workExperience) {
            const startDate = parseDateInput(exp.startDate);
            const endDate = parseDateInput(exp.endDate);
            const isCurrent =
              exp.isCurrentJob || exp.endDate?.toLowerCase() === "present";

            // Determine current job title from the most recent 'current' job
            if (isCurrent && !currentJobTitle) {
              currentJobTitle = exp.jobTitle;
            } else if (
              isCurrent &&
              startDate &&
              workExperiencesToCreate.length > 0
            ) {
              const latestStartDate = workExperiencesToCreate
                .filter((w) => w.isCurrentJob)
                .reduce(
                  (latest, current) => {
                    const processedStartDate = parseDateInput(
                      current.startDate,
                    );
                    if (!processedStartDate) {
                      return latest;
                    }
                    if (!latest || processedStartDate > latest) {
                      return processedStartDate;
                    } else {
                      return latest;
                    }
                  },
                  null as Date | null,
                );

              if (startDate > (latestStartDate ?? new Date())) {
                currentJobTitle = exp.jobTitle;
              }
            }

            const allTechAreas = await getTechnologyAreas();
            const allSectors = await getIndustrySectors();

            if (startDate) {
              workExperiencesToCreate.push({
                workId: uuidv4(),
                jobseekerId: jobseekerId,
                company: exp.company,
                jobTitle: exp.jobTitle,
                isInternship: exp.isInternship ?? false,
                isCurrentJob: isCurrent,
                startDate: startDate,
                endDate: endDate,
                responsibilities: exp.responsibilities ?? "",
                techAreaId: allTechAreas.find(
                  (area) => area.title == exp.techArea,
                )?.id,
                sectorId: allSectors.find(
                  (sector) => sector.sector_title == exp.industrySector,
                )?.industry_sector_id,
              });
            } else {
              console.warn(
                `Skipping work experience for ${exp.company} due to invalid start date: ${exp.startDate}`,
              );
            }
          }
          if (workExperiencesToCreate.length > 0) {
            await tx.workExperience.createMany({
              data: workExperiencesToCreate,
            });
          }

          if (currentJobTitle) {
            await tx.jobseekers.update({
              where: { jobseeker_id: jobseekerId },
              data: { current_job_title: currentJobTitle },
            });
          }
        }

        await tx.projectExperiences.deleteMany({
          where: { jobseekerId: jobseekerId },
        });

        if (body.projects && body.projects.length > 0) {
          for (const proj of body.projects) {
            const startDate = parseDateInput(proj.startDate);
            const completionDate = parseDateInput(proj.completionDate);

            if (!startDate || !completionDate) {
              console.warn(
                `Skipping project "${proj.projectTitle}" due to invalid dates.`,
              );
              continue;
            }

            const projectSkillIdsToConnect: string[] = [];
            if (proj.skillsUsed && proj.skillsUsed.length > 0) {
              for (const skill of proj.skillsUsed) {
                if (
                  skill.skillName &&
                  typeof skill.skillName === "string" &&
                  skill.skillName.trim()
                ) {
                  try {
                    const searchResults = await vectorSearchSkills(
                      skill.skillName.trim(),
                      1,
                    );
                    if (searchResults.length > 0) {
                      projectSkillIdsToConnect.push(searchResults[0].skill_id);
                    }
                  } catch (error) {
                    console.error(
                      `Error during vector search for project skill "${skill.skillName}":`,
                      error,
                    );
                  }
                } else {
                  console.warn(
                    `Skipping invalid/empty skill entry for project "${proj.projectTitle}".`,
                  );
                }
              }
            }
            // Ensure skill IDs for this specific project are unique
            const uniqueProjectSkillIds = Array.from(
              new Set(projectSkillIdsToConnect),
            );

            await tx.projectExperiences.create({
              data: {
                jobseekerId: jobseekerId,
                projTitle: proj.projectTitle,
                projectRole: proj.projectRole ?? "Contributor",
                startDate: startDate,
                completionDate: completionDate,
                problemSolvedDescription: proj.description ?? "",
                teamSize: proj.teamSize ?? 1,
                repoUrl: proj.repoUrl,
                demoUrl: proj.demoUrl,
                project_has_skills: {
                  createMany: {
                    data: uniqueProjectSkillIds.map((skillId) => ({
                      skill_id: skillId,
                    })),
                  },
                },
              },
            });
          }
        }

        await tx.jobseekers_education.deleteMany({
          where: { jobseekerId: jobseekerId },
        });

        let isEnrolledInProgram = false;
        if (body.education && body.education.length > 0) {
          const educationToCreate: Prisma.jobseekers_educationCreateManyInput[] =
            [];
          for (const edu of body.education) {
            const eduProviderId = await findOrCreateEduProvider(
              edu.institutionName,
            );
            const startDate = parseDateInput(edu.startDate);
            const gradDate = parseDateInput(edu.endDate);
            const isCurrentlyEnrolled =
              edu.isEnrolled ||
              edu.enrollmentStatus == ProgramEnrollmentStatus.Enrolled ||
              edu.endDate?.toLowerCase() === "present" ||
              edu.endDate?.toLowerCase() === "current";

            if (isCurrentlyEnrolled) {
              isEnrolledInProgram = true;
            }

            let program;
            if (edu.major) {
              program = await tx.programs.findFirst({
                where: { title: { contains: edu.major } },
              });
              if (!program) {
                program = await tx.programs.create({
                  data: {
                    title: edu.major,
                  },
                });
              }
            }

            if (eduProviderId && startDate) {
              educationToCreate.push({
                jobseekerId: jobseekerId,
                eduProviderId: eduProviderId,
                programId: program ? program.id : null,
                edLevel: edu.edLevel,
                degreeType: edu.degreeType,
                major: edu.major,
                isEnrolled: isCurrentlyEnrolled,
                enrollmentStatus: edu.enrollmentStatus,
                startDate: startDate,
                gradDate: gradDate,
                gpa: edu.gpa,
                description: edu.description,
                isTechDegree: edu.isTechDegree,
              });
            } else {
              console.warn(
                `Skipping education record for ${edu.institutionName} due to missing provider ID or invalid start date.`,
              );
            }
          }
          if (educationToCreate.length > 0) {
            await tx.jobseekers_education.createMany({
              data: educationToCreate,
            });
            await tx.jobseekers.update({
              where: { jobseeker_id: jobseekerId },
              data: { is_enrolled_ed_program: isEnrolledInProgram },
            });
          }
        }

        await tx.certificates.deleteMany({
          where: { jobSeekerId: jobseekerId },
        });

        if (body.certificates && body.certificates.length > 0) {
          const certsToCreate: Prisma.certificatesCreateManyInput[] = [];
          for (const cert of body.certificates) {
            const issueDate = parseDateInput(cert.issueDate);
            const expiryDate = parseDateInput(cert.expiryDate);

            if (cert.name && issueDate) {
              certsToCreate.push({
                certId: uuidv4(),
                jobSeekerId: jobseekerId,
                name: cert.name,
                issuingOrg: cert.issuingOrg ?? "Unknown",
                credentialId: cert.credentialId,
                credentialUrl: cert.credentialUrl,
                issueDate: issueDate,
                expiryDate: expiryDate,
                description: cert.description,
              });
            } else {
              console.warn(
                `Skipping certificate "${cert.name}" due to missing name or invalid issue date.`,
              );
            }
          }
          if (certsToCreate.length > 0) {
            await tx.certificates.createMany({
              data: certsToCreate,
            });
          }
        }

        const jobseekerSkillIdsToConnect: string[] = [];
        if (body.skills && body.skills.length > 0) {
          for (const skill of body.skills) {
            if (
              skill.skillName &&
              typeof skill.skillName === "string" &&
              skill.skillName.trim()
            ) {
              try {
                const searchResults = await vectorSearchSkills(
                  skill.skillName.trim(),
                  1,
                );
                if (searchResults.length > 0) {
                  jobseekerSkillIdsToConnect.push(searchResults[0].skill_id);
                }
              } catch (error) {
                console.error(
                  `Error during vector search for jobseeker skill "${skill.skillName}":`,
                  error,
                );
              }
            } else {
              console.warn(`Skipping invalid/empty skill entry for jobseeker.`);
            }
          }
        }
        const uniqueJobseekerSkillIds = Array.from(
          new Set(jobseekerSkillIdsToConnect),
        );
        await tx.jobseekers.update({
          where: { jobseeker_id: jobseekerId },
          data: {
            jobseeker_has_skills: {
              deleteMany: {
                jobseeker_id: jobseekerId,
              },
              create: uniqueJobseekerSkillIds.map((skillId) => ({
                skills: {
                  connect: {
                    skill_id: skillId,
                  },
                },
              })),
            },
          },
        });

        return {
          jobseekerId: jobseekerId,
          introduction: {
            firstName: user.first_name,
            lastName: user.last_name,
            phoneNumber: user.phone,
          },
        };
      },
      {
        maxWait: 15000,
        timeout: 30000,
      },
    );

    return NextResponse.json(
      {
        success: true,
        introduction: result.introduction,
        jobseekerId: result.jobseekerId,
      },
      { status: 200 },
    );
  } catch (error: any) {
    console.error("Error processing AI resume upsert:", error);
    if (error instanceof Prisma.PrismaClientKnownRequestError) {
      console.error("Prisma Error Code:", error.code);
      console.error("Prisma Error Meta:", error.meta);
    }
    if (error.message) {
      console.error("Error Message:", error.message);
    }
    if (error.stack) {
      console.error("Error Stack:", error.stack);
    }
    return NextResponse.json(
      {
        success: false,
        error: "Failed to process AI resume data",
        details: error.message || "Unknown error",
      },
      { status: 500 },
    );
  }
}
