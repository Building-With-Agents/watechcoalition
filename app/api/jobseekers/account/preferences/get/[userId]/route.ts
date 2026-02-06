import getPrismaClient from "@/app/lib/prismaClient.mjs";
import { PrismaClient } from "@prisma/client";
import { NextResponse } from "next/server";
import { JsPreferencesDTO } from "@/data/dtos/JobSeekerProfileCreationDTOs";

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
        { error: "Invalid input. Requires userId." },
        { status: 400 },
      );
    }

    // Find the jobseekerId based on the userId
    const jobseeker = await prisma.jobseekers.findUnique({
      where: { user_id: userId },
      select: { jobseeker_id: true },
    });

    if (!jobseeker) {
      return NextResponse.json(
        { error: "Jobseeker not found" },
        { status: 404 },
      );
    }

    const jobseekerId = jobseeker.jobseeker_id;
    const preferences = await prisma.jobseekers.findUnique({
      where: { jobseeker_id: jobseekerId },
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

    if (!preferences) {
      return NextResponse.json(
        { error: `Jobseeker record not found for id: ${jobseekerId}` },
        { status: 400 },
      );
    }

    const result: JsPreferencesDTO = {
      userId: preferences.user_id,
      targetedPathwayId: preferences.targeted_pathway,
      targetedPathway: preferences.pathways?.pathway_title,
      preferredEmploymentType: preferences.employment_type_sought,
    };

    return NextResponse.json({ success: true, result }, { status: 200 });
  } catch (error: any) {
    return NextResponse.json(
      { error: `Failed to update skills: ${error.message}` },
      { status: 500 },
    );
  } finally {
    await prisma.$disconnect();
  }
}
