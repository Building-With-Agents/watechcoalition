import getPrismaClient from "@/app/lib/prismaClient.mjs";
import { PrismaClient } from "@prisma/client";
import { NextResponse } from "next/server";
import {
  JsDisclosuresDTO,
  JsDisclosuresPostDTO,
} from "@/data/dtos/JobSeekerProfileCreationDTOs";
import { auth } from "@/auth";

const prisma: PrismaClient = getPrismaClient();

export async function POST(request: Request) {
  try {
    // Get essentials from session, not the request
    const session = await auth();
    const userId: string = session?.user.id!;

    const body: JsDisclosuresPostDTO = await request.json();
    const {
      isVeteran,
      disabilityStatus,
      disability,
      gender,
      race,
      ethnicity,
      CareerPrepAssessment,
    } = body;

    if (!userId) {
      return NextResponse.json({
        success: false,
        error: `A userId must be provided.`,
      });
    }

    // use this to get jobseeker id by user id.
    const jobseekerRecord = await prisma.jobseekers.findUnique({
      where: {
        user_id: userId,
      },
      select: {
        jobseeker_id: true,
      },
    });
    if (!jobseekerRecord) {
      return NextResponse.json(
        {
          success: false,
          error: `Jobseeker record does not exist for userId: ${userId}`,
        },
        { status: 400 },
      );
    }
    const jobseekerId = jobseekerRecord.jobseeker_id;

    const user = await prisma.user.update({
      where: {
        id: userId,
      },
      data: {
        jobseekers: {
          update: {
            where: {
              jobseeker_id: jobseekerId,
            },
            data: {
              jobseekers_private_data: {
                update: {
                  where: {
                    jobseeker_id: jobseekerId,
                  },
                  data: {
                    is_veteran: isVeteran,
                    disability_status: disabilityStatus,
                    disability: disability,
                    gender: gender,
                    race: race,
                    ethnicity: ethnicity,
                  },
                },
              },
              CareerPrepAssessment: {
                upsert: {
                  where: { jobseekerId: jobseekerId },
                  create: {
                    priorityPopulations:
                      CareerPrepAssessment.priorityPopulations,
                    pronouns: "",
                    expectedEduCompletion: "",
                    experienceWithApplying: false,
                    experienceWithInterview: false,
                  },
                  update: {
                    priorityPopulations:
                      CareerPrepAssessment.priorityPopulations,
                  },
                },
              },
            },
          },
        },
      },
      select: {
        jobseekers: {
          select: {
            jobseeker_id: true,
            jobseekers_private_data: {
              select: {
                is_veteran: true,
                disability_status: true,
                disability: true,
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
        has_agreed_terms: true,
      },
    });

    const { jobseekers } = user;
    const jobseekerDetails = jobseekers?.[0] || {};
    const privateDetails = jobseekerDetails.jobseekers_private_data?.[0] || {};

    const result: JsDisclosuresDTO = {
      jobseekerId: jobseekerDetails.jobseeker_id || null,
      gender: privateDetails.gender || null,
      race: privateDetails.race || null,
      ethnicity: privateDetails?.ethnicity || null,
      isVeteran: privateDetails?.is_veteran || null,
      disabilityStatus: privateDetails?.disability_status || null,
      disability: privateDetails?.disability || null,
      CareerPrepAssessment: {
        priorityPopulations:
          jobseekerDetails.CareerPrepAssessment &&
          jobseekerDetails.CareerPrepAssessment.length > 0
            ? jobseekerDetails.CareerPrepAssessment[0].priorityPopulations
            : undefined,
      },
    };

    return NextResponse.json({ success: true, result }, { status: 200 });
  } catch (e: any) {
    return NextResponse.json(
      { error: `Failed to upsert disclosures: ${e.message}` },
      { status: 500 },
    );
  }
}
