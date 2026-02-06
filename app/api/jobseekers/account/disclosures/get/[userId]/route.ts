import getPrismaClient from "@/app/lib/prismaClient.mjs";
import { jobseekers_private_data, PrismaClient } from "@prisma/client";
import { NextResponse } from "next/server";
import { JsDisclosuresDTO } from "@/data/dtos/JobSeekerProfileCreationDTOs";

const prisma: PrismaClient = getPrismaClient();

export async function GET(
  request: Request,
  props: { params: Promise<{ userId: string }> },
) {
  const params = await props.params;
  try {
    const userId = params.userId;

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
            jobseekers_private_data: {
              select: {
                is_veteran: true,
                disability: true,
                disability_status: true,
                gender: true,
                race: true,
                ethnicity: true,
              },
            },
            CareerPrepAssessment: {
              select: {
                priorityPopulations: true,
              },
            },
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

    if (user.role.toLowerCase().trim() !== "jobseeker") {
      return NextResponse.json(
        { success: false, error: `UserId is not related to a jobseeker` },
        { status: 404 },
      );
    }

    const result: JsDisclosuresDTO = {
      jobseekerId: null, // users.jobseekers[0].jobseeker_id
      isVeteran: null, // jobseekers[0].jobseekers_private_data[0].is_veteran
      disability: null, // jobseekers[0].jobseekers_private_data[0].has_disability
      disabilityStatus: null,
      gender: null, // users.gender
      race: null, //users.race
      ethnicity: null,
      CareerPrepAssessment: {
        priorityPopulations: undefined,
      },
    };

    if (user?.jobseekers && user?.jobseekers.length > 0) {
      const jobseekerDetails = user?.jobseekers?.[0] || null;
      result.jobseekerId = jobseekerDetails?.jobseeker_id;
      if (
        jobseekerDetails.jobseekers_private_data &&
        jobseekerDetails.jobseekers_private_data.length > 0
      ) {
        const privateDetails: Partial<jobseekers_private_data> =
          jobseekerDetails.jobseekers_private_data[0];
        result.isVeteran = privateDetails.is_veteran;
        result.disability = privateDetails.disability;
        result.disabilityStatus = privateDetails.disability_status;
        result.gender = privateDetails.gender;
        result.race = privateDetails.race;
        result.ethnicity = privateDetails.ethnicity;
        result.CareerPrepAssessment.priorityPopulations =
          jobseekerDetails.CareerPrepAssessment &&
          jobseekerDetails.CareerPrepAssessment.length > 0
            ? jobseekerDetails.CareerPrepAssessment[0].priorityPopulations
            : undefined;
      }
    }

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
