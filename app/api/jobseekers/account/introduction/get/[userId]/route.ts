import { NextResponse } from "next/server";
import { PrismaClient } from "@prisma/client";
import { JsIntroDTO } from "@/data/dtos/JobSeekerProfileCreationDTOs";
import getPrismaClient from "@/app/lib/prismaClient.mjs";

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
        { error: "User email is required" },
        { status: 400 },
      );
    }
    // Fetch the users data
    const user = await prisma.user.findUnique({
      where: {
        id: userId,
      },
      select: {
        id: true,
        role: true,
        first_name: true,
        last_name: true,
        birthdate: true,
        email: true,
        emailVerified: true,
        phoneCountryCode: true,
        phone: true,
        photo_url: true,
        createdAt: true,
        locationData: {
          select: {
            zip: true,
            state: true,
            stateCode: true,
            county: true,
            city: true,
          },
        },
        jobseekers: {
          select: {
            jobseeker_id: true,
            is_enrolled_ed_program: true,
            highest_level_of_study_completed: true,
            current_grade_level: true,
            current_enrolled_ed_program: true,
            intern_hours_required: true,
            intro_headline: true,
            current_job_title: true,
            years_work_exp: true,
            portfolio_url: true,
            video_url: true,
            is_marked_deletion: true,
            employment_type_sought: true,
            pathways: {
              select: {
                pathway_id: true,
                pathway_title: true,
              },
            },
            CareerPrepAssessment: {
              select: {
                streetAddress: true,
                pronouns: true,
              },
            },
          },
        },
      },
    });
    if (!user) {
      return NextResponse.json(
        { error: "Jobseeker not found" },
        { status: 404 },
      );
    }

    const jobseeker =
      user.jobseekers && user.jobseekers.length > 0
        ? user.jobseekers?.[0]
        : null;

    // Map the jobseeker data to JsIntroDTO
    const loadIntroPage: JsIntroDTO = {
      userId: user.id,
      photoUrl: user.photo_url,
      firstName: user?.first_name,
      lastName: user?.last_name,
      birthDate: user.birthdate,
      phoneCountryCode: user.phoneCountryCode,
      phone: user.phone ?? null,
      zipCode: user.locationData?.zip,
      state: user.locationData?.state,
      city: user.locationData?.city,
      county: user.locationData?.county,
      email: user.email,
      introHeadline: jobseeker?.intro_headline,
      currentJobTitle: jobseeker?.current_job_title,
      CareerPrepAssessment: {
        streetAddress:
          jobseeker?.CareerPrepAssessment &&
          jobseeker.CareerPrepAssessment.length > 0
            ? jobseeker.CareerPrepAssessment[0].streetAddress
            : null,
        pronouns:
          jobseeker?.CareerPrepAssessment &&
          jobseeker.CareerPrepAssessment.length > 0
            ? jobseeker.CareerPrepAssessment[0].pronouns
            : null,
      },
    };

    // metadata that may be needed
    const meta = {
      emailVerified: user.emailVerified,
      createdAt: user.createdAt,
      pathwayId: jobseeker?.pathways?.pathway_id,
      jobseekerId: jobseeker?.jobseeker_id,
      isMarkedDeletion: jobseeker?.is_marked_deletion,
    };
    const result = { loadIntroPage, meta };
    return NextResponse.json(
      {
        success: true,
        result,
      },
      { status: 200 },
    );
  } catch (error: any) {
    console.error("Error reading job seeker intro:", error);
    return NextResponse.json(
      { error: "Failed to read job seeker intro" },
      { status: 500 },
    );
  } finally {
    await prisma.$disconnect();
  }
}
