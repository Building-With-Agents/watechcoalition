import getPrismaClient from "@/app/lib/prismaClient.mjs";
import { PrismaClient } from "@prisma/client";
import { NextResponse } from "next/server";
import { JsPreferencesDTO } from "@/data/dtos/JobSeekerProfileCreationDTOs";
import { auth } from "@/auth";

const prisma: PrismaClient = getPrismaClient();

export async function POST(request: Request) {
  try {
    // Get essentials from session, not the request
    const session = await auth();
    const userId: string = session?.user.id!;
    const jobseekerId = session?.user.jobseekerId;

    const body: JsPreferencesDTO = await request.json();
    const { preferredEmploymentType, targetedPathwayId, targetedPathway } =
      body;

    if (!userId || !jobseekerId || !preferredEmploymentType) {
      return NextResponse.json(
        {
          error: "Invalid input. Requires userId and preferredEmploymentType",
        },
        { status: 400 },
      );
    }
    let pw = null;
    if (!targetedPathwayId && targetedPathway) {
      pw = await prisma.pathways.findUnique({
        where: {
          pathway_title: targetedPathway,
        },
      });

      if (!pw) {
        return NextResponse.json(
          { error: `No record exists for pathway : ${targetedPathway}.` },
          { status: 404 },
        );
      }
    }

    const upsertedPreferences = await prisma.jobseekers.update({
      where: { user_id: userId },
      data: {
        employment_type_sought: preferredEmploymentType,
        targeted_pathway: targetedPathwayId || pw?.pathway_id,
        updatedAt: new Date(),
      },
      select: {
        user_id: true,
        targeted_pathway: true,
        employment_type_sought: true,
        pathways: {
          select: {
            pathway_title: true,
          },
        },
      },
    });

    await prisma.careerPrepAssessment.upsert({
      where: { jobseekerId: jobseekerId },
      create: {
        jobseekerId: jobseekerId,
        interestPathway: targetedPathway,
        pronouns: "",
        expectedEduCompletion: "",
        experienceWithApplying: false,
        experienceWithInterview: false,
        prevWorkExperience: false,
      },
      update: {
        interestPathway: targetedPathway,
      },
    });

    const result: JsPreferencesDTO = {
      userId: upsertedPreferences.user_id,
      targetedPathwayId: upsertedPreferences.targeted_pathway,
      targetedPathway: upsertedPreferences.pathways?.pathway_title,
      preferredEmploymentType: upsertedPreferences.employment_type_sought,
    };

    return NextResponse.json({ success: true, result }, { status: 200 });
  } catch (error: any) {
    return NextResponse.json(
      { error: `Failed to update skills: ${error.message}` },
      { status: 500 },
    );
  }
}
