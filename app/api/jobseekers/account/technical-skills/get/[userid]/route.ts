import getPrismaClient from "@/app/lib/prismaClient.mjs";
import { PrismaClient } from "@prisma/client";
import { NextResponse } from "next/server";
import { JsCareerPrepPathwaySkillsDTO } from "@/data/dtos/JobSeekerProfileCreationDTOs";
import { Role } from "@/data/dtos/UserInfoDTO";
import { CareerPrepPathways } from "@/app/lib/admin/careerPrep";

const prisma: PrismaClient = getPrismaClient();

export async function GET(
  request: Request,
  props: { params: Promise<{ userid: string }> },
) {
  const params = await props.params;
  console.log(params);
  try {
    const userId = params.userid;

    if (!userId) {
      return NextResponse.json({
        success: false,
        error: `A userId must be provided.`,
      });
    }

    const user = await prisma.user.findUnique({
      where: {
        id: userId,
      },
      select: {
        jobseekers: {
          select: {
            jobseeker_id: true,
          },
        },
        role: true,
      },
    });

    if (!user) {
      return NextResponse.json(
        { success: false, error: `Record not found for userId: ${userId}` },
        { status: 404 },
      );
    }

    if (!user.role.includes(Role.JOBSEEKER)) {
      return NextResponse.json(
        { success: false, error: `User is not a jobseeker` },
        { status: 404 },
      );
    }

    const jobseeker = await prisma.jobseekers.findUnique({
      where: { user_id: userId },
      select: {
        user_id: true,
        pathways: true,
        CareerPrepAssessment: {
          select: {
            CybersecurityRating: true,
            ITCloudRating: true,
            DataAnalyticsRating: true,
            SoftwareDevRating: true,
          },
        },
      },
    });

    if (!jobseeker) {
      return NextResponse.json(
        { error: `Failed to retrieve jobseeker` },
        { status: 404 },
      );
    }
    const result: JsCareerPrepPathwaySkillsDTO = {
      userId: userId,
      targetedPathway:
        (jobseeker.pathways?.pathway_title as CareerPrepPathways) || null,
      CareerPrepAssessment: {
        cybersecurity:
          jobseeker.CareerPrepAssessment.length > 0
            ? jobseeker.CareerPrepAssessment[0].CybersecurityRating[0]
            : null,
        itAndCloudComputing:
          jobseeker.CareerPrepAssessment.length > 0
            ? jobseeker.CareerPrepAssessment[0].ITCloudRating[0]
            : null,
        dataAnalytics:
          jobseeker.CareerPrepAssessment.length > 0
            ? jobseeker.CareerPrepAssessment[0].DataAnalyticsRating[0]
            : null,
        softwareDevelopment:
          jobseeker.CareerPrepAssessment.length > 0
            ? jobseeker.CareerPrepAssessment[0].SoftwareDevRating[0]
            : null,
      },
    };

    return NextResponse.json({ success: true, result }, { status: 200 });
  } catch (e: any) {
    return NextResponse.json(
      { error: `Failed to retrieve disclosures: ${e.message}` },
      { status: 500 },
    );
  } finally {
    await prisma.$disconnect();
  }
}
