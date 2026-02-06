import { NextResponse } from "next/server";
import { PrismaClient } from "@prisma/client";
import getPrismaClient from "@/app/lib/prismaClient.mjs";
import { JsShowcaseDTO } from "@/data/dtos/JobSeekerProfileCreationDTOs";
import { SkillDTO } from "@/data/dtos/SkillDTO";
import { JobseekerSkillDTO } from "@/data/dtos/JobseekerSkillDTO";

const prisma: PrismaClient = getPrismaClient();
export async function GET(
  request: Request,
  props: { params: Promise<{ userId: string }> },
) {
  const params = await props.params;
  try {
    const userId = params.userId;

    const showcase = await prisma.jobseekers.findUnique({
      where: {
        user_id: userId,
      },
      select: {
        user_id: true,
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
        intro_headline: true,
        portfolio_url: true,
        portfolio_password: true,
        video_url: true,
        linkedin_url: true,
      },
    });

    if (!showcase) {
      return NextResponse.json({
        success: false,
        error: `Record does not exist for id ${userId}`,
      });
    } else {
      const mappedSkills: SkillDTO[] = showcase.jobseeker_has_skills.map(
        (jsSkill: JobseekerSkillDTO) => ({
          skill_id: jsSkill.skills.skill_id,
          skill_name: jsSkill.skills.skill_name,
          skill_info_url: jsSkill.skills.skill_info_url,
        }),
      );
      const result: JsShowcaseDTO = {
        userId: showcase.user_id,
        introduction: showcase.intro_headline,
        portfolioUrl: showcase.portfolio_url,
        portfolioPassword: showcase.portfolio_password,
        video_url: showcase.video_url,
        linkedin_url: showcase.linkedin_url,
        skills: mappedSkills,
      };
      // console.log(JSON.stringify(showcase, null ,2))
      return NextResponse.json({ success: true, result }, { status: 200 });
    }
  } catch (error: any) {
    return NextResponse.json(
      { success: false, error: error.message },
      { status: 500 },
    );
  } finally {
    await prisma.$disconnect();
  }
}
