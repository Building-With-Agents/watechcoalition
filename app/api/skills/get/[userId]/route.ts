import getPrismaClient from "@/app/lib/prismaClient.mjs";
import { PrismaClient } from "@prisma/client";
import { NextResponse } from "next/server";
import { SkillDTO } from "@/data/dtos/SkillDTO";

const prisma: PrismaClient = getPrismaClient();

export async function GET(
  request: Request,
  props: { params: Promise<{ userId: string }> },
) {
  const params = await props.params;
  try {
    const userId = params.userId;

    const data = await prisma.jobseekers.findUnique({
      where: {
        user_id: userId,
      },
      select: {
        project_experiences: {
          select: {
            project_has_skills: {
              select: {
                skills: {
                  select: {
                    skill_id: true,
                    skill_name: true,
                    skill_info_url: true,
                  },
                },
              },
            },
          },
        },
        jobseeker_has_skills: {
          select: {
            skills: {
              select: {
                skill_id: true,
                skill_name: true,
                skill_info_url: true,
              },
            },
          },
        },
      },
    });

    // Map skills to SKillDTO[]
    const jobseekerSkills: SkillDTO[] =
      data?.jobseeker_has_skills?.map((skill) => skill.skills) || [];
    const projectSkills: SkillDTO[] =
      data?.project_experiences?.flatMap(
        (exp) => exp.project_has_skills?.map((skill) => skill.skills) || [],
      ) || [];

    // Create a Set of jobseeker skill IDs
    const jobseekerSkillIds = new Set(
      jobseekerSkills.map((skill) => skill.skill_id),
    );

    // Filter project skills to remove any that are already in jobseeker skills
    const uniqueProjectSkills: SkillDTO[] = projectSkills.filter(
      (skill) => !jobseekerSkillIds.has(skill.skill_id),
    );

    const result: { topSkills: SkillDTO[]; otherSkills: SkillDTO[] } = {
      topSkills: jobseekerSkills,
      otherSkills: uniqueProjectSkills,
    };
    return NextResponse.json({ success: true, result }, { status: 200 });
  } catch (e: any) {
    return NextResponse.json(
      { error: `Failed to read jobseeker skills: ${e.message}` },
      { status: 500 },
    );
  } finally {
    await prisma.$disconnect();
  }
}
