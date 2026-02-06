import { NextResponse } from "next/server";
import { PrismaClient } from "@prisma/client";
import {
  JsIntroDTO,
  JsIntroPostDTO,
} from "@/data/dtos/JobSeekerProfileCreationDTOs";
import getPrismaClient from "@/app/lib/prismaClient.mjs";
import { auth } from "@/auth";
import { Role } from "@/data/dtos/UserInfoDTO";

const prisma: PrismaClient = getPrismaClient();

export async function POST(request: Request) {
  try {
    // Get essentials from session, not the request
    const session = await auth();
    const userId: string = session?.user.id!;
    const jobseekerId: string = session?.user.jobseekerId!;

    const body: JsIntroPostDTO = await request.json();

    // Destructure the DTO
    const {
      photoUrl,
      firstName,
      lastName,
      birthDate,
      phoneCountryCode,
      phone,
      zipCode,
      email,
      introHeadline,
      currentJobTitle,
      CareerPrepAssessment,
    } = body;

    // const formattedPhone = formatPhoneE164(phoneCountryCode, phone);

    const result = await prisma.$transaction(async (prisma) => {
      // Upsert user
      const user = await prisma.user.upsert({
        where: { id: userId },
        update: {
          first_name: firstName || null,
          last_name: lastName || null,
          birthdate: birthDate || null,
          phoneCountryCode: phoneCountryCode || null,
          phone: phone || null,
          email: email,
          photo_url: photoUrl || null,
          locationData: Boolean(zipCode)
            ? {
                connect: {
                  zip: zipCode,
                },
              }
            : {
                disconnect: true,
              },
          updatedAt: new Date(),
        },
        create: {
          id: userId,
          role: Role.JOBSEEKER,
          first_name: firstName,
          last_name: lastName,
          birthdate: birthDate ?? undefined,
          phoneCountryCode: phoneCountryCode,
          phone: phone ?? undefined,
          email: email,
          photo_url: photoUrl,
          createdAt: new Date(),
          updatedAt: undefined,
          emailVerified: undefined,
        },
        include: {
          locationData: true,
        },
      });

      // Upsert jobseeker
      // Find the jobseeker_id or generate a new one
      const js = await prisma.jobseekers.findUnique({
        where: { user_id: userId },
        select: {
          jobseeker_id: true,
          targeted_pathway: true,
          is_enrolled_ed_program: true,
        },
      });

      const isEnrolledInCollege = js?.is_enrolled_ed_program || false;

      const jobseeker = await prisma.jobseekers.upsert({
        where: { user_id: user.id },
        update: {
          intro_headline: introHeadline,
          current_job_title: currentJobTitle,
          CareerPrepAssessment: {
            upsert: {
              where: { jobseekerId: jobseekerId },
              create: {
                streetAddress: CareerPrepAssessment.streetAddress,
                pronouns: CareerPrepAssessment.pronouns ?? "",
                expectedEduCompletion: "",
                experienceWithApplying: false,
                experienceWithInterview: false,
              },
              update: {
                streetAddress: CareerPrepAssessment.streetAddress,
                pronouns: CareerPrepAssessment.pronouns ?? "",
              },
            },
          },
          users: {
            connect: {
              id: userId,
            },
          },
        },
        create: {
          jobseeker_id: jobseekerId,
          users: {
            connect: {
              id: userId,
            },
          },
          targeted_pathway: undefined,
          is_enrolled_ed_program: isEnrolledInCollege,
          highest_level_of_study_completed: undefined,
          current_grade_level: undefined,
          current_enrolled_ed_program: undefined,
          intern_hours_required: undefined,
          intro_headline: introHeadline, // TODO: remove and add to Showcase route
          current_job_title: currentJobTitle,
          years_work_exp: undefined,
          portfolio_url: undefined,
          video_url: undefined,
          employment_type_sought: undefined,
          CareerPrepAssessment: {
            create: {
              streetAddress: CareerPrepAssessment.streetAddress,
              pronouns: CareerPrepAssessment.pronouns ?? "",
              expectedEduCompletion: "",
              experienceWithApplying: false,
              experienceWithInterview: false,
            },
          },
        },
        include: {
          CareerPrepAssessment: {
            select: {
              streetAddress: true,
              pronouns: true,
            },
          },
        },
      });

      const loadIntroPage: JsIntroDTO = {
        userId: user.id,
        photoUrl: user.photo_url,
        firstName: user.first_name,
        lastName: user.last_name,
        CareerPrepAssessment: {
          streetAddress:
            jobseeker.CareerPrepAssessment.length > 0
              ? jobseeker.CareerPrepAssessment[0].streetAddress
              : null,
          pronouns:
            jobseeker.CareerPrepAssessment.length > 0
              ? jobseeker.CareerPrepAssessment[0].pronouns
              : null,
        },
        birthDate: user.birthdate,
        phoneCountryCode: user.phoneCountryCode,
        phone: user.phone ?? "",
        zipCode: user.locationData?.zip,
        state: user.locationData?.stateCode,
        city: user.locationData?.city,
        county: user.locationData?.county,
        email: user.email,
        introHeadline: jobseeker.intro_headline,
        currentJobTitle: jobseeker.current_job_title,
      };

      const meta = {
        emailVerified: user.emailVerified,
        createdAt: user.createdAt,
        pathwayId: jobseeker.targeted_pathway,
        jobseekerId: jobseeker.jobseeker_id,
        isMarkedDeletion: jobseeker.is_marked_deletion,
      };
      return { loadIntroPage, meta };
    });
    return NextResponse.json({ success: true, result }, { status: 200 });
  } catch (error) {
    console.error("Error creating job seeker intro:", error);
    return NextResponse.json(
      { error: "Failed to create job seeker intro" },
      { status: 500 },
    );
  }
}
