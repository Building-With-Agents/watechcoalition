import { NextResponse } from "next/server";
import getPrismaClient from "@/app/lib/prismaClient.mjs";
import { PrismaClient } from "@prisma/client";
import { SkillDTO } from "@/data/dtos/SkillDTO";
import { auth } from "@/auth";

const prisma: PrismaClient = getPrismaClient();

export async function DELETE(request: Request) {
  try {
    // Get essentials from session, not the request
    const session = await auth();
    const userId: string = session?.user.id!;

    const body = await request.json();
    const { skillIds } = body;
    if (!userId || !Array.isArray(skillIds) || skillIds.length === 0) {
      return NextResponse.json(
        {
          success: false,
          error: "Need to provide both jobseekerId and an array of skillIds",
        },
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

    const deletedSkills = await prisma.jobseeker_has_skills.deleteMany({
      where: {
        jobseeker_id: jobseekerId,
        skill_id: {
          in: skillIds,
        },
      },
    });

    if (deletedSkills.count === 0) {
      return NextResponse.json(
        {
          success: false,
          error:
            "No skills were deleted. Please check the provided jobseekerId and skillIds.",
        },
        { status: 400 },
      );
    }

    const deletedSkillsDetails = await prisma.skills.findMany({
      where: {
        skill_id: {
          in: skillIds,
        },
      },
      select: {
        skill_id: true,
        skill_name: true,
        skill_info_url: true,
      },
    });

    const result: SkillDTO[] = deletedSkillsDetails.map((skill) => ({
      skill_id: skill.skill_id,
      skill_name: skill.skill_name,
      skill_info_url: skill.skill_info_url,
    }));

    return NextResponse.json({ success: true, result }, { status: 200 });
  } catch (e: any) {
    console.log(e.message);
    return NextResponse.json(
      { error: `Failed to delete skills.\n${e.message} ` },
      { status: 500 },
    );
  } finally {
    prisma.$disconnect();
  }
}
