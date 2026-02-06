import { NextResponse } from "next/server";
import { Prisma, PrismaClient, WorkExperience } from "@prisma/client";
import { v4 as uuidv4 } from "uuid";
import getPrismaClient from "@/app/lib/prismaClient.mjs";
import { JsWorkExpDTO } from "@/data/dtos/JobSeekerProfileCreationDTOs";
import { auth } from "@/auth";
import { setPoolWithSession } from "@/app/lib/jobseeker";

const prisma: PrismaClient = getPrismaClient();

export async function POST(request: Request) {
  try {
    // Get essentials from session, not the request
    const session = await auth();
    const userId: string = session?.user.id!;

    const body: JsWorkExpDTO = await request.json();

    const {
      yearsWorkExperience,
      monthsInternshipExperience,
      isAuthorizedToWorkUsa,
      CareerPrepAssessment,
      requiresSponsorship,
      workExperiences,
    } = body;

    console.log("BOOG: ", CareerPrepAssessment);

    const result: JsWorkExpDTO = await prisma.$transaction(async (prisma) => {
      // Update the jobseeker table with the provided properties
      const updatedJobseeker = await prisma.jobseekers.update({
        where: { user_id: userId },
        data: {
          years_work_exp: yearsWorkExperience
            ? parseInt(yearsWorkExperience, 10)
            : 0,
          months_internship_exp: monthsInternshipExperience
            ? parseInt(monthsInternshipExperience, 10)
            : null,
          updatedAt: new Date(),
        },
      });

      const careerPrep = await prisma.careerPrepAssessment.upsert({
        where: { jobseekerId: updatedJobseeker.jobseeker_id },
        create: {
          jobseekerId: updatedJobseeker.jobseeker_id,
          pronouns: "",
          expectedEduCompletion: "",
          experienceWithApplying:
            CareerPrepAssessment.experienceWithApplying ?? false,
          experienceWithInterview:
            CareerPrepAssessment.experienceWithInterview ?? false,
          prevWorkExperience:
            updatedJobseeker.years_work_exp &&
            updatedJobseeker.years_work_exp > 0
              ? true
              : false,
        },
        update: {
          experienceWithApplying:
            CareerPrepAssessment.experienceWithApplying ?? false,
          experienceWithInterview:
            CareerPrepAssessment.experienceWithInterview ?? false,
          prevWorkExperience:
            updatedJobseeker.years_work_exp &&
            updatedJobseeker.years_work_exp > 0
              ? true
              : false,
        },
      });

      // TODO: encryption of private data
      const updatedPrivateData = await prisma.jobseekers_private_data.upsert({
        where: {
          jobseeker_id: updatedJobseeker.jobseeker_id,
        },
        update: {
          is_authorized_to_work_in_usa: isAuthorizedToWorkUsa,
          job_sponsorship_required: requiresSponsorship,
        },
        create: {
          jobseeker_private_data_id: uuidv4(),
          jobseeker_id: updatedJobseeker.jobseeker_id,
          ssn: undefined,
          is_authorized_to_work_in_usa: isAuthorizedToWorkUsa,
          job_sponsorship_required: requiresSponsorship,
        },
      });

      // Remove work experiences that are not in the latest data
      if (workExperiences) {
        const existingWorkExperiences = await prisma.workExperience.findMany({
          where: {
            jobseekerId: updatedJobseeker.jobseeker_id,
          },
        });
        if (existingWorkExperiences && existingWorkExperiences.length !== 0) {
          const removableExperiences = existingWorkExperiences.filter(
            (existingExperience) =>
              workExperiences.findIndex(
                (incomingExperience) =>
                  incomingExperience.workId === existingExperience.workId,
              ) === -1,
          );

          await prisma.workExperience.deleteMany({
            where: {
              OR: removableExperiences.map((removableExperience) => ({
                workId: { equals: removableExperience.workId },
              })),
            },
          });
        }
      }

      const createdWorkExperiences: WorkExperience[] = [];
      const workExpPromises = workExperiences?.map(async (workExperience) => {
        const existingWorkExperience = await prisma.workExperience.findUnique({
          where: {
            workId: workExperience.workId,
          },
        });

        const updateData: Partial<WorkExperience> = {
          company: workExperience.company,
          jobTitle: workExperience.jobTitle,
          isCurrentJob: workExperience.isCurrentJob,
          startDate: new Date(workExperience.startDate),
          endDate: workExperience.endDate
            ? new Date(workExperience.endDate)
            : null,
          responsibilities: workExperience.responsibilities,
          isInternship: workExperience.isInternship,
          techAreaId: workExperience.techAreaId || null,
          sectorId: workExperience.sectorId || null,
        };

        if (existingWorkExperience) {
          const updatedWorkExperience = await prisma.workExperience.update({
            where: { workId: existingWorkExperience.workId },
            data: updateData,
          });
          createdWorkExperiences.push(updatedWorkExperience);
        } else {
          const createdWorkExperience = await prisma.workExperience.create({
            data: {
              workId: workExperience.workId,
              company: workExperience.company,
              jobTitle: workExperience.jobTitle,
              isCurrentJob: workExperience.isCurrentJob,
              startDate: new Date(workExperience.startDate),
              endDate: workExperience.endDate
                ? new Date(workExperience.endDate)
                : null,
              responsibilities: workExperience.responsibilities,
              isInternship: workExperience.isInternship,
              jobseekers: {
                connect: {
                  jobseeker_id: updatedJobseeker?.jobseeker_id ?? undefined,
                },
              },
              techArea: workExperience?.techAreaId
                ? { connect: { id: workExperience.techAreaId } }
                : undefined, // Skip connection if techAreaId is undefined,
              industrySector: workExperience.sectorId
                ? { connect: { industry_sector_id: workExperience.sectorId } }
                : undefined,
            },
          });
          createdWorkExperiences.push(createdWorkExperience);
        }
      });
      if (workExpPromises) {
        await Promise.all(workExpPromises);
      }

      return {
        userId: updatedJobseeker.user_id,
        yearsWorkExperience: updatedJobseeker?.years_work_exp?.toString() ?? "",
        monthsInternshipExperience:
          updatedJobseeker?.months_internship_exp?.toString() ?? "",
        isAuthorizedToWorkUsa: updatedPrivateData.is_authorized_to_work_in_usa,
        requiresSponsorship: updatedPrivateData.job_sponsorship_required,
        CareerPrepAssessment: {
          experienceWithInterview: careerPrep.experienceWithInterview,
          experienceWithApplying: careerPrep.experienceWithApplying,
        },
        workExperiences: createdWorkExperiences,
      };
    });
    // Trigger setPoolWithSession in the background
    setPoolWithSession().catch((error) =>
      console.error("Error in setPoolWithSession:", error),
    );
    return NextResponse.json(
      {
        success: true,
        result,
      },
      { status: 200 },
    );
  } catch (e: any) {
    if (e instanceof Prisma.PrismaClientKnownRequestError) {
      // Handle unique constraint violation
      if (e.code === "P2002") {
        console.error(e);
        return NextResponse.json(
          { error: "Unique constraint violation. This data already exists." },
          { status: 409 },
        );
      }
      // Handle foreign key constraint violation
      if (e.code === "P2025") {
        return NextResponse.json(
          { error: "No record found that matches the provided foreign key." },
          { status: 404 },
        );
      }
      // Add other specific Prisma errors as needed
    }
    console.error("Unexpected error:", e);
    return NextResponse.json(
      { error: `Failed to create work experiences.\n${e.message} ` },
      { status: 500 },
    );
  }
}
