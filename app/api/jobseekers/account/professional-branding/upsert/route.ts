import { NextResponse } from "next/server";
import { Prisma, PrismaClient } from "@prisma/client";
import getPrismaClient from "@/app/lib/prismaClient.mjs";
import { JsCareerPrepProfessionalBrandingDTO } from "@/data/dtos/JobSeekerProfileCreationDTOs";
import { auth } from "@/auth";

const prisma: PrismaClient = getPrismaClient();

export async function POST(request: Request) {
  try {
    const session = await auth();
    const userId: string = session?.user.id!;

    const body: JsCareerPrepProfessionalBrandingDTO = await request.json();
    const { CareerPrepAssessment } = body;

    const result: JsCareerPrepProfessionalBrandingDTO =
      await prisma.$transaction(async (prisma) => {
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
            BrandingRating:
              CareerPrepAssessment.professionalBrandingAndJobMarketReadiness
                ? {
                    create: {
                      personalBrand:
                        CareerPrepAssessment
                          .professionalBrandingAndJobMarketReadiness
                          ?.personalBrand,
                      onlinePresence:
                        CareerPrepAssessment
                          .professionalBrandingAndJobMarketReadiness
                          ?.onlinePresence,
                      elevatorPitch:
                        CareerPrepAssessment
                          .professionalBrandingAndJobMarketReadiness
                          ?.elevatorPitch,
                      resumeEffectiveness:
                        CareerPrepAssessment
                          .professionalBrandingAndJobMarketReadiness
                          ?.resumeEffectiveness,
                      coverLetterEffectiveness:
                        CareerPrepAssessment
                          .professionalBrandingAndJobMarketReadiness
                          ?.coverLetterEffectiveness,
                      interviewExperience:
                        CareerPrepAssessment
                          .professionalBrandingAndJobMarketReadiness
                          ?.interviewExperience,
                      responseTechnique:
                        CareerPrepAssessment
                          .professionalBrandingAndJobMarketReadiness
                          ?.responseTechnique,
                      followUpImportance:
                        CareerPrepAssessment
                          .professionalBrandingAndJobMarketReadiness
                          ?.followUpImportance,
                      onlineNetworking:
                        CareerPrepAssessment
                          .professionalBrandingAndJobMarketReadiness
                          ?.onlineNetworking,
                      eventNetworking:
                        CareerPrepAssessment
                          .professionalBrandingAndJobMarketReadiness
                          ?.eventNetworking,
                      relationshipManagement:
                        CareerPrepAssessment
                          .professionalBrandingAndJobMarketReadiness
                          ?.relationshipManagement,
                      jobSearchStrategy:
                        CareerPrepAssessment
                          .professionalBrandingAndJobMarketReadiness
                          ?.jobSearchStrategy,
                      materialDistribution:
                        CareerPrepAssessment
                          .professionalBrandingAndJobMarketReadiness
                          ?.materialDistribution,
                      networkingTechniques:
                        CareerPrepAssessment
                          .professionalBrandingAndJobMarketReadiness
                          ?.networkingTechniques,
                      onboardingBestPractices:
                        CareerPrepAssessment
                          .professionalBrandingAndJobMarketReadiness
                          ?.onboardingBestPractices,
                      developmentPlan:
                        CareerPrepAssessment
                          .professionalBrandingAndJobMarketReadiness
                          ?.developmentPlan,
                      mentorship:
                        CareerPrepAssessment
                          .professionalBrandingAndJobMarketReadiness
                          ?.mentorship,
                    },
                  }
                : undefined,
          },
          update: {
            BrandingRating:
              CareerPrepAssessment.professionalBrandingAndJobMarketReadiness
                ? {
                    upsert: {
                      where: { jobseekerId: updatedJobseeker.jobseeker_id },
                      update: {
                        personalBrand:
                          CareerPrepAssessment
                            .professionalBrandingAndJobMarketReadiness
                            ?.personalBrand,
                        onlinePresence:
                          CareerPrepAssessment
                            .professionalBrandingAndJobMarketReadiness
                            ?.onlinePresence,
                        elevatorPitch:
                          CareerPrepAssessment
                            .professionalBrandingAndJobMarketReadiness
                            ?.elevatorPitch,
                        resumeEffectiveness:
                          CareerPrepAssessment
                            .professionalBrandingAndJobMarketReadiness
                            ?.resumeEffectiveness,
                        coverLetterEffectiveness:
                          CareerPrepAssessment
                            .professionalBrandingAndJobMarketReadiness
                            ?.coverLetterEffectiveness,
                        interviewExperience:
                          CareerPrepAssessment
                            .professionalBrandingAndJobMarketReadiness
                            ?.interviewExperience,
                        responseTechnique:
                          CareerPrepAssessment
                            .professionalBrandingAndJobMarketReadiness
                            ?.responseTechnique,
                        followUpImportance:
                          CareerPrepAssessment
                            .professionalBrandingAndJobMarketReadiness
                            ?.followUpImportance,
                        onlineNetworking:
                          CareerPrepAssessment
                            .professionalBrandingAndJobMarketReadiness
                            ?.onlineNetworking,
                        eventNetworking:
                          CareerPrepAssessment
                            .professionalBrandingAndJobMarketReadiness
                            ?.eventNetworking,
                        relationshipManagement:
                          CareerPrepAssessment
                            .professionalBrandingAndJobMarketReadiness
                            ?.relationshipManagement,
                        jobSearchStrategy:
                          CareerPrepAssessment
                            .professionalBrandingAndJobMarketReadiness
                            ?.jobSearchStrategy,
                        materialDistribution:
                          CareerPrepAssessment
                            .professionalBrandingAndJobMarketReadiness
                            ?.materialDistribution,
                        networkingTechniques:
                          CareerPrepAssessment
                            .professionalBrandingAndJobMarketReadiness
                            ?.networkingTechniques,
                        onboardingBestPractices:
                          CareerPrepAssessment
                            .professionalBrandingAndJobMarketReadiness
                            ?.onboardingBestPractices,
                        developmentPlan:
                          CareerPrepAssessment
                            .professionalBrandingAndJobMarketReadiness
                            ?.developmentPlan,
                        mentorship:
                          CareerPrepAssessment
                            .professionalBrandingAndJobMarketReadiness
                            ?.mentorship,
                      },
                      create: {
                        personalBrand:
                          CareerPrepAssessment
                            .professionalBrandingAndJobMarketReadiness
                            ?.personalBrand,
                        onlinePresence:
                          CareerPrepAssessment
                            .professionalBrandingAndJobMarketReadiness
                            ?.onlinePresence,
                        elevatorPitch:
                          CareerPrepAssessment
                            .professionalBrandingAndJobMarketReadiness
                            ?.elevatorPitch,
                        resumeEffectiveness:
                          CareerPrepAssessment
                            .professionalBrandingAndJobMarketReadiness
                            ?.resumeEffectiveness,
                        coverLetterEffectiveness:
                          CareerPrepAssessment
                            .professionalBrandingAndJobMarketReadiness
                            ?.coverLetterEffectiveness,
                        interviewExperience:
                          CareerPrepAssessment
                            .professionalBrandingAndJobMarketReadiness
                            ?.interviewExperience,
                        responseTechnique:
                          CareerPrepAssessment
                            .professionalBrandingAndJobMarketReadiness
                            ?.responseTechnique,
                        followUpImportance:
                          CareerPrepAssessment
                            .professionalBrandingAndJobMarketReadiness
                            ?.followUpImportance,
                        onlineNetworking:
                          CareerPrepAssessment
                            .professionalBrandingAndJobMarketReadiness
                            ?.onlineNetworking,
                        eventNetworking:
                          CareerPrepAssessment
                            .professionalBrandingAndJobMarketReadiness
                            ?.eventNetworking,
                        relationshipManagement:
                          CareerPrepAssessment
                            .professionalBrandingAndJobMarketReadiness
                            ?.relationshipManagement,
                        jobSearchStrategy:
                          CareerPrepAssessment
                            .professionalBrandingAndJobMarketReadiness
                            ?.jobSearchStrategy,
                        materialDistribution:
                          CareerPrepAssessment
                            .professionalBrandingAndJobMarketReadiness
                            ?.materialDistribution,
                        networkingTechniques:
                          CareerPrepAssessment
                            .professionalBrandingAndJobMarketReadiness
                            ?.networkingTechniques,
                        onboardingBestPractices:
                          CareerPrepAssessment
                            .professionalBrandingAndJobMarketReadiness
                            ?.onboardingBestPractices,
                        developmentPlan:
                          CareerPrepAssessment
                            .professionalBrandingAndJobMarketReadiness
                            ?.developmentPlan,
                        mentorship:
                          CareerPrepAssessment
                            .professionalBrandingAndJobMarketReadiness
                            ?.mentorship,
                      },
                    },
                  }
                : undefined,
          },
          select: {
            BrandingRating: true,
          },
        });

        return {
          userId: updatedJobseeker.user_id,
          CareerPrepAssessment: {
            professionalBrandingAndJobMarketReadiness:
              careerPrep.BrandingRating.length > 0
                ? careerPrep.BrandingRating[0]
                : null,
          },
        };
      });

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
