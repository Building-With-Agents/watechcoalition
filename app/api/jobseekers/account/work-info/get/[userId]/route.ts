import { NextResponse } from "next/server";
import { PrismaClient, WorkExperience } from "@prisma/client";
import getPrismaClient from "@/app/lib/prismaClient.mjs";
import { JsWorkExpDTO } from "@/data/dtos/JobSeekerProfileCreationDTOs";

const prisma: PrismaClient = getPrismaClient();

export async function GET(
  request: Request,
  props: { params: Promise<{ userId: string }> },
) {
  const params = await props.params;
  try {
    const userId = params.userId;

    if (!userId) {
      return NextResponse.json(
        { error: "User ID is required" },
        { status: 400 },
      );
    }

    const user = await prisma.user.findUnique({
      where: {
        id: userId,
      },
      select: {
        id: true,
        jobseekers: {
          select: {
            jobseeker_id: true,
            years_work_exp: true,
            months_internship_exp: true,
            work_experiences: true,
            jobseekers_private_data: {
              select: {
                is_authorized_to_work_in_usa: true,
                job_sponsorship_required: true,
              },
            },
            CareerPrepAssessment: {
              select: {
                experienceWithApplying: true,
                experienceWithInterview: true,
              },
            },
          },
        },
      },
    });

    if (!user) {
      return NextResponse.json(
        { error: `Record does not exist for userId: ${userId}` },
        { status: 400 },
      );
    } else {
      // Assuming there is only one jobseeker per user
      const jobseeker = user.jobseekers?.[0];

      const privateData = jobseeker?.jobseekers_private_data[0]; // There's only one private data record per jobseeker

      const workExperiences: WorkExperience[] = jobseeker?.work_experiences.map(
        (w) => ({
          workId: w.workId,
          jobseekerId: w.jobseekerId,
          sectorId: w.sectorId,
          company: w.company,
          jobTitle: w.jobTitle,
          isCurrentJob: w.isCurrentJob,
          startDate: w.startDate,
          endDate: w.endDate,
          responsibilities: w.responsibilities,
          isInternship: w.isInternship,
          techAreaId: w.techAreaId,
          updatedAt: w.updatedAt,
          createdAt: w.createdAt,
        }),
      );

      const result: JsWorkExpDTO = {
        userId: user.id,
        yearsWorkExperience: jobseeker.years_work_exp?.toString() ?? "",
        monthsInternshipExperience:
          jobseeker.months_internship_exp?.toString() ?? "",
        ...(privateData?.is_authorized_to_work_in_usa !== undefined && {
          isAuthorizedToWorkUsa: privateData.is_authorized_to_work_in_usa,
        }),
        ...(privateData?.job_sponsorship_required !== undefined && {
          requiresSponsorship: privateData.job_sponsorship_required,
        }),
        CareerPrepAssessment: {
          experienceWithApplying:
            jobseeker.CareerPrepAssessment.length > 0
              ? jobseeker.CareerPrepAssessment[0].experienceWithApplying
              : false,
          experienceWithInterview:
            jobseeker.CareerPrepAssessment.length > 0
              ? jobseeker.CareerPrepAssessment[0].experienceWithInterview
              : false,
        },
        workExperiences,
      };

      return NextResponse.json(
        {
          success: true,
          result,
        },
        { status: 200 },
      );
    }
  } catch (e: any) {
    console.log(e.message);
    return NextResponse.json(
      { error: `Failed to read work experiences.\n${e.message} ` },
      { status: 500 },
    );
  } finally {
    await prisma.$disconnect();
  }
}
