import { NextResponse } from "next/server";
import { PrismaClient } from "@prisma/client";
import getPrismaClient from "@/app/lib/prismaClient.mjs";
import { JsShowcaseDTO } from "@/data/dtos/JobSeekerProfileCreationDTOs";
import { SkillDTO } from "@/data/dtos/SkillDTO";
import { JobseekerSkillDTO } from "@/data/dtos/JobseekerSkillDTO";
import { v4 as uuidv4 } from "uuid";
import { auth } from "@/auth";

const prisma: PrismaClient = getPrismaClient();

export async function POST(request: Request) {
  try {
    // Get essentials from session, not the request
    const session = await auth();
    const userId: string = session?.user.id!;

    const body: JsShowcaseDTO = await request.json();
    const {
      introduction,
      skills,
      portfolioUrl,
      portfolioPassword,
      video_url,
      linkedin_url,
    } = body;
    const existingJobseeker = await prisma.jobseekers.findUnique({
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

    const updatedRecords = [];
    if (existingJobseeker) {
      const updatedJobseeker = await prisma.jobseekers.update({
        where: {
          user_id: userId,
        },
        data: {
          intro_headline: introduction,
          portfolio_url: portfolioUrl,
          portfolio_password: portfolioPassword,
          video_url: video_url,
          linkedin_url: linkedin_url,
          updatedAt: new Date(),
          jobseeker_has_skills: {
            deleteMany: {},
            create: skills?.map((skill: SkillDTO) => ({
              skills: {
                connect: { skill_id: skill.skill_id },
              },
            })),
          },
        },
        select: {
          user_id: true,
          intro_headline: true,
          jobseeker_has_skills: {
            select: {
              jobseeker_id: true,
              skills: {
                select: {
                  skill_id: true,
                  skill_name: true,
                  skill_info_url: true,
                },
              },
            },
          },
          portfolio_url: true,
          portfolio_password: true,
          video_url: true,
          linkedin_url: true,
        },
      });
      updatedRecords.push(updatedJobseeker);
    } else {
      const createdRecord = await prisma.jobseekers.create({
        data: {
          jobseeker_id: uuidv4(),
          user_id: userId,
          intro_headline: introduction,
          portfolio_url: portfolioUrl,
          portfolio_password: portfolioPassword,
          video_url: video_url,
          linkedin_url: linkedin_url,
          targeted_pathway: undefined, // Provide a default or get from input
          is_enrolled_ed_program: false, // Provide a default or get from input
          jobseeker_has_skills: {
            create: skills?.map((skill: SkillDTO) => ({
              skills: {
                connect: { skill_id: skill.skill_id },
              },
            })),
          },
        },
        select: {
          user_id: true,
          intro_headline: true,
          jobseeker_has_skills: {
            select: {
              jobseeker_id: true,
              skills: {
                select: {
                  skill_id: true,
                  skill_name: true,
                  skill_info_url: true,
                },
              },
            },
          },
          portfolio_url: true,
          portfolio_password: true,
          video_url: true,
          linkedin_url: true,
        },
      });
      updatedRecords.push(createdRecord);
    }
    const showcase = updatedRecords[0];
    const mappedSkills: SkillDTO[] = showcase.jobseeker_has_skills?.map(
      (jsSkill: JobseekerSkillDTO) => ({
        skill_id: jsSkill.skills.skill_id,
        skill_name: jsSkill.skills.skill_name,
        skill_info_url: jsSkill.skills.skill_info_url,
      }),
    );
    const result: JsShowcaseDTO = {
      userId: userId,
      introduction: showcase.intro_headline,
      portfolioUrl: showcase.portfolio_url,
      portfolioPassword: showcase.portfolio_password,
      video_url: showcase.video_url,
      linkedin_url: showcase.linkedin_url,
      skills: mappedSkills,
    };
    return NextResponse.json({ success: true, result }, { status: 200 });
  } catch (e: any) {
    console.log(e.message);
    return NextResponse.json(
      { error: `Failed to create jobseeker education.\n${e.message} ` },
      { status: 500 },
    );
  } finally {
    await prisma.$disconnect();
  }
}
