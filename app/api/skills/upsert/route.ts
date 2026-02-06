import getPrismaClient from "@/app/lib/prismaClient.mjs";
import { PrismaClient } from "@prisma/client";
import { NextResponse } from "next/server";
import { SkillDTO } from "@/data/dtos/SkillDTO";
import { JobseekerSkillDTO } from "@/data/dtos/JobseekerSkillDTO";
import { auth } from "@/auth";

const prisma: PrismaClient = getPrismaClient();

export async function POST(request: Request) {
  try {
    // Get essentials from session, not the request
    const session = await auth();
    const userId: string = session?.user.id!;

    const { skillIds } = await request.json();

    if (!userId || !Array.isArray(skillIds)) {
      return NextResponse.json(
        { error: "Invalid input. Requires jobseekerId and skillId[]" },
        { status: 400 },
      );
    }

    if (!userId || !Array.isArray(skillIds)) {
      return NextResponse.json(
        { error: "Invalid input. Requires userId and skillIds[]" },
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

    // Normalize skillIds array: remove blanks, trim spaces, and filter out empty strings
    const normalizedSkillIds: string[] = skillIds.filter(
      (id: string) => id && id.trim() !== "",
    );
    const upsertedSkills = [];

    for (const skillId of normalizedSkillIds) {
      const upsertedskill: JobseekerSkillDTO =
        await prisma.jobseeker_has_skills.upsert({
          where: {
            jobseeker_id_skill_id: {
              jobseeker_id: jobseekerId,
              skill_id: skillId,
            },
          },
          update: {},
          create: { jobseeker_id: jobseekerId, skill_id: skillId },
          select: {
            skills: {
              select: {
                skill_id: true,
                skill_name: true,
                skill_info_url: true,
              },
            },
          },
        });
      upsertedSkills.push(upsertedskill);
    }
    const result: SkillDTO[] = upsertedSkills.map((s: JobseekerSkillDTO) => ({
      skill_id: s.skills.skill_id,
      skill_name: s.skills.skill_name,
      skill_info_url: s.skills.skill_info_url,
    }));

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
