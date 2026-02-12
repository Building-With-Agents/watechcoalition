import { NextResponse } from "next/server";
import { Prisma, PrismaClient } from "@prisma/client";
import getPrismaClient from "@/app/lib/prismaClient.mjs";
import { JsCareerPrepDurableSkillsDTO } from "@/data/dtos/JobSeekerProfileCreationDTOs";
import { auth } from "@/auth";

const prisma: PrismaClient = getPrismaClient();

export async function POST(request: Request) {
  try {
    const session = await auth();
    const userId: string = session?.user.id!;

    const body: JsCareerPrepDurableSkillsDTO = await request.json();
    const { CareerPrepAssessment } = body;

    const result: JsCareerPrepDurableSkillsDTO = await prisma.$transaction(
      async (prisma) => {
        const updatedJobseeker = await prisma.jobseekers.update({
          where: { user_id: userId },
          data: { updatedAt: new Date() },
        });

        const careerPrep = await prisma.careerPrepAssessment.upsert({
          where: { jobseekerId: updatedJobseeker.jobseeker_id },
          create: {
            jobseekerId: updatedJobseeker.jobseeker_id,
            interestPathway: updatedJobseeker.targeted_pathway,
            pronouns: "",
            expectedEduCompletion: "",
            experienceWithApplying: false,
            experienceWithInterview: false,
            prevWorkExperience: false,
            DurableSkillsRating: CareerPrepAssessment.durableSkills
              ? {
                  create: {
                    emotionManagement:
                      CareerPrepAssessment.durableSkills?.emotionManagement,
                    empathy: CareerPrepAssessment.durableSkills?.empathy,
                    goalSetting:
                      CareerPrepAssessment.durableSkills?.goalSetting,
                    timeManagement:
                      CareerPrepAssessment.durableSkills?.timeManagement,
                    adaptability:
                      CareerPrepAssessment.durableSkills?.adaptability,
                    criticalThinking:
                      CareerPrepAssessment.durableSkills?.criticalThinking,
                    creativity: CareerPrepAssessment.durableSkills?.creativity,
                    resilience: CareerPrepAssessment.durableSkills?.resilience,
                    communication:
                      CareerPrepAssessment.durableSkills?.communication,
                    activeListening:
                      CareerPrepAssessment.durableSkills?.activeListening,
                    conflictResolution:
                      CareerPrepAssessment.durableSkills?.conflictResolution,
                    nonverbalCommunication:
                      CareerPrepAssessment.durableSkills
                        ?.nonverbalCommunication,
                    teamwork: CareerPrepAssessment.durableSkills?.teamwork,
                    trustBuilding:
                      CareerPrepAssessment.durableSkills?.trustBuilding,
                    leadership: CareerPrepAssessment.durableSkills?.leadership,
                    perspectiveTaking:
                      CareerPrepAssessment.durableSkills?.perspectiveTaking,
                    culturalAwareness:
                      CareerPrepAssessment.durableSkills?.culturalAwareness,
                    relationshipBuilding:
                      CareerPrepAssessment.durableSkills?.relationshipBuilding,
                    documentationSkills:
                      CareerPrepAssessment.durableSkills?.documentationSkills,
                  },
                }
              : undefined,
          },
          update: {
            DurableSkillsRating: CareerPrepAssessment.durableSkills
              ? {
                  upsert: {
                    where: { jobseekerId: updatedJobseeker.jobseeker_id },
                    update: {
                      emotionManagement:
                        CareerPrepAssessment.durableSkills?.emotionManagement,
                      empathy: CareerPrepAssessment.durableSkills?.empathy,
                      goalSetting:
                        CareerPrepAssessment.durableSkills?.goalSetting,
                      timeManagement:
                        CareerPrepAssessment.durableSkills?.timeManagement,
                      adaptability:
                        CareerPrepAssessment.durableSkills?.adaptability,
                      criticalThinking:
                        CareerPrepAssessment.durableSkills?.criticalThinking,
                      creativity:
                        CareerPrepAssessment.durableSkills?.creativity,
                      resilience:
                        CareerPrepAssessment.durableSkills?.resilience,
                      communication:
                        CareerPrepAssessment.durableSkills?.communication,
                      activeListening:
                        CareerPrepAssessment.durableSkills?.activeListening,
                      conflictResolution:
                        CareerPrepAssessment.durableSkills?.conflictResolution,
                      nonverbalCommunication:
                        CareerPrepAssessment.durableSkills
                          ?.nonverbalCommunication,
                      teamwork: CareerPrepAssessment.durableSkills?.teamwork,
                      trustBuilding:
                        CareerPrepAssessment.durableSkills?.trustBuilding,
                      leadership:
                        CareerPrepAssessment.durableSkills?.leadership,
                      perspectiveTaking:
                        CareerPrepAssessment.durableSkills?.perspectiveTaking,
                      culturalAwareness:
                        CareerPrepAssessment.durableSkills?.culturalAwareness,
                      relationshipBuilding:
                        CareerPrepAssessment.durableSkills
                          ?.relationshipBuilding,
                      documentationSkills:
                        CareerPrepAssessment.durableSkills?.documentationSkills,
                    },
                    create: {
                      emotionManagement:
                        CareerPrepAssessment.durableSkills?.emotionManagement,
                      empathy: CareerPrepAssessment.durableSkills?.empathy,
                      goalSetting:
                        CareerPrepAssessment.durableSkills?.goalSetting,
                      timeManagement:
                        CareerPrepAssessment.durableSkills?.timeManagement,
                      adaptability:
                        CareerPrepAssessment.durableSkills?.adaptability,
                      criticalThinking:
                        CareerPrepAssessment.durableSkills?.criticalThinking,
                      creativity:
                        CareerPrepAssessment.durableSkills?.creativity,
                      resilience:
                        CareerPrepAssessment.durableSkills?.resilience,
                      communication:
                        CareerPrepAssessment.durableSkills?.communication,
                      activeListening:
                        CareerPrepAssessment.durableSkills?.activeListening,
                      conflictResolution:
                        CareerPrepAssessment.durableSkills?.conflictResolution,
                      nonverbalCommunication:
                        CareerPrepAssessment.durableSkills
                          ?.nonverbalCommunication,
                      teamwork: CareerPrepAssessment.durableSkills?.teamwork,
                      trustBuilding:
                        CareerPrepAssessment.durableSkills?.trustBuilding,
                      leadership:
                        CareerPrepAssessment.durableSkills?.leadership,
                      perspectiveTaking:
                        CareerPrepAssessment.durableSkills?.perspectiveTaking,
                      culturalAwareness:
                        CareerPrepAssessment.durableSkills?.culturalAwareness,
                      relationshipBuilding:
                        CareerPrepAssessment.durableSkills
                          ?.relationshipBuilding,
                      documentationSkills:
                        CareerPrepAssessment.durableSkills?.documentationSkills,
                    },
                  },
                }
              : undefined,
          },
          select: {
            DurableSkillsRating: true,
          },
        });

        const rawDs =
          careerPrep.DurableSkillsRating.length > 0
            ? careerPrep.DurableSkillsRating[0]
            : null;
        return {
          userId: updatedJobseeker.user_id,
          CareerPrepAssessment: {
            durableSkills: rawDs
              ? {
                  ...rawDs,
                  overallAverage:
                    rawDs.overallAverage != null
                      ? Number(rawDs.overallAverage)
                      : null,
                }
              : null,
          },
        };
      },
    );

    return NextResponse.json({ success: true, result }, { status: 200 });
  } catch (e: any) {
    if (e instanceof Prisma.PrismaClientKnownRequestError) {
      if (e.code === "P2002") {
        console.error(e);
        return NextResponse.json(
          { error: "Unique constraint violation. This data already exists." },
          { status: 409 },
        );
      }
      if (e.code === "P2025") {
        return NextResponse.json(
          { error: "No record found that matches the provided foreign key." },
          { status: 404 },
        );
      }
    }
    console.error("Unexpected error:", e);
    return NextResponse.json(
      { error: `Failed to create work experiences.\n${e.message}` },
      { status: 500 },
    );
  }
}
