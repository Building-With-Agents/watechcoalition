import { NextResponse } from "next/server";
import { Prisma, PrismaClient } from "@prisma/client";
import getPrismaClient from "@/app/lib/prismaClient.mjs";
import { JsCareerPrepPathwaySkillsDTO } from "@/data/dtos/JobSeekerProfileCreationDTOs";
import { auth } from "@/auth";
import { CareerPrepPathways } from "@/app/lib/admin/careerPrep";

const prisma: PrismaClient = getPrismaClient();

export async function POST(request: Request) {
  try {
    const session = await auth();
    const userId: string = session?.user.id!;

    const body: JsCareerPrepPathwaySkillsDTO = await request.json();
    const { CareerPrepAssessment, targetedPathway } = body;

    const result: JsCareerPrepPathwaySkillsDTO = await prisma.$transaction(
      async (prisma) => {
        let pw = null;
        if (targetedPathway) {
          pw = await prisma.pathways.findUnique({
            where: {
              pathway_title: targetedPathway,
            },
          });

          if (!pw) {
            throw new Error(
              `No record exists for pathway: ${targetedPathway}.`,
            );
          }
        }

        const updatedJobseeker = await prisma.jobseekers.update({
          where: { user_id: userId },
          data: {
            updatedAt: new Date(),
            targeted_pathway: pw?.pathway_id,
          },
        });

        const careerPrep = await prisma.careerPrepAssessment.upsert({
          where: { jobseekerId: updatedJobseeker.jobseeker_id },
          create: {
            jobseekerId: updatedJobseeker.jobseeker_id,
            interestPathway: targetedPathway,
            pronouns: "",
            expectedEduCompletion: "",
            experienceWithApplying: false,
            experienceWithInterview: false,
            prevWorkExperience: false,
            CybersecurityRating: CareerPrepAssessment.cybersecurity
              ? {
                  create: {
                    networking: CareerPrepAssessment.cybersecurity.networking,
                    projectManagement:
                      CareerPrepAssessment.cybersecurity.projectManagement,
                    securityTools:
                      CareerPrepAssessment.cybersecurity.securityTools,
                    operatingSystems:
                      CareerPrepAssessment.cybersecurity.operatingSystems,
                    programming: CareerPrepAssessment.cybersecurity.programming,
                    cryptography:
                      CareerPrepAssessment.cybersecurity.cryptography,
                    cloudSecurity:
                      CareerPrepAssessment.cybersecurity.cloudSecurity,
                    incidentResponse:
                      CareerPrepAssessment.cybersecurity.incidentResponse,
                    dataSecurity:
                      CareerPrepAssessment.cybersecurity.dataSecurity,
                    technicalSupport:
                      CareerPrepAssessment.cybersecurity.technicalSupport,
                    computationalThinking:
                      CareerPrepAssessment.cybersecurity.computationalThinking,
                    apiUsage: CareerPrepAssessment.cybersecurity.apiUsage,
                  },
                }
              : undefined,
            DataAnalyticsRating: CareerPrepAssessment.dataAnalytics
              ? {
                  create: {
                    dataAnalysis:
                      CareerPrepAssessment.dataAnalytics.dataAnalysis,
                    sqlProgramming:
                      CareerPrepAssessment.dataAnalytics.sqlProgramming,
                    pythonPackages:
                      CareerPrepAssessment.dataAnalytics.pythonPackages,
                    dataScience: CareerPrepAssessment.dataAnalytics.dataScience,
                    dataEngineering:
                      CareerPrepAssessment.dataAnalytics.dataEngineering,
                    tableau: CareerPrepAssessment.dataAnalytics.tableau,
                    machineLearning:
                      CareerPrepAssessment.dataAnalytics.machineLearning,
                    rProgramming:
                      CareerPrepAssessment.dataAnalytics.rProgramming,
                    projectManagement:
                      CareerPrepAssessment.dataAnalytics.projectManagement,
                    dataVisualization:
                      CareerPrepAssessment.dataAnalytics.dataVisualization,
                    dataStructures:
                      CareerPrepAssessment.dataAnalytics.dataStructures,
                    bigOComplexity:
                      CareerPrepAssessment.dataAnalytics.bigOComplexity,
                    sortingAlgorithms:
                      CareerPrepAssessment.dataAnalytics.sortingAlgorithms,
                    databases: CareerPrepAssessment.dataAnalytics.databases,
                    computationalThinking:
                      CareerPrepAssessment.dataAnalytics.computationalThinking,
                  },
                }
              : undefined,
            ITCloudRating: CareerPrepAssessment.itAndCloudComputing
              ? {
                  create: {
                    techSupport:
                      CareerPrepAssessment.itAndCloudComputing.techSupport,
                    activeDirectory:
                      CareerPrepAssessment.itAndCloudComputing.activeDirectory,
                    projectManagement:
                      CareerPrepAssessment.itAndCloudComputing
                        .projectManagement,
                    helpDeskSupport:
                      CareerPrepAssessment.itAndCloudComputing.helpDeskSupport,
                    windowsServers:
                      CareerPrepAssessment.itAndCloudComputing.windowsServers,
                    sqlProgramming:
                      CareerPrepAssessment.itAndCloudComputing.sqlProgramming,
                    computerHardware:
                      CareerPrepAssessment.itAndCloudComputing.computerHardware,
                    operatingSystems:
                      CareerPrepAssessment.itAndCloudComputing.operatingSystems,
                    systemAdmin:
                      CareerPrepAssessment.itAndCloudComputing.systemAdmin,
                    networkAdmin:
                      CareerPrepAssessment.itAndCloudComputing.networkAdmin,
                    virtualization:
                      CareerPrepAssessment.itAndCloudComputing.virtualization,
                    coreCloudServices:
                      CareerPrepAssessment.itAndCloudComputing
                        .coreCloudServices,
                    apiUsage: CareerPrepAssessment.itAndCloudComputing.apiUsage,
                    httpResponseCodes:
                      CareerPrepAssessment.itAndCloudComputing
                        .httpResponseCodes,
                    computationalThinking:
                      CareerPrepAssessment.itAndCloudComputing
                        .computationalThinking,
                  },
                }
              : undefined,
            SoftwareDevRating: CareerPrepAssessment.softwareDevelopment
              ? {
                  create: {
                    softwareEngineering:
                      CareerPrepAssessment.softwareDevelopment
                        .softwareEngineering,
                    softwareDevelopmentLifecycle:
                      CareerPrepAssessment.softwareDevelopment
                        .softwareDevelopmentLifecycle,
                    programmingLanguages:
                      CareerPrepAssessment.softwareDevelopment
                        .programmingLanguages,
                    dataStructuresAndAlgorithms:
                      CareerPrepAssessment.softwareDevelopment
                        .dataStructuresAndAlgorithms,
                    softwareArchitecture:
                      CareerPrepAssessment.softwareDevelopment
                        .softwareArchitecture,
                    versionControl:
                      CareerPrepAssessment.softwareDevelopment.versionControl,
                    databaseManagement:
                      CareerPrepAssessment.softwareDevelopment
                        .databaseManagement,
                    devOps: CareerPrepAssessment.softwareDevelopment.devOps,
                    cloudComputing:
                      CareerPrepAssessment.softwareDevelopment.cloudComputing,
                    conceptualSystemsThinking:
                      CareerPrepAssessment.softwareDevelopment
                        .conceptualSystemsThinking,
                    problemSolving:
                      CareerPrepAssessment.softwareDevelopment.problemSolving,
                    fundamentalCodingConcepts:
                      CareerPrepAssessment.softwareDevelopment
                        .fundamentalCodingConcepts,
                    debugging:
                      CareerPrepAssessment.softwareDevelopment.debugging,
                    computationalThinking:
                      CareerPrepAssessment.softwareDevelopment
                        .computationalThinking,
                    softwareOptimization:
                      CareerPrepAssessment.softwareDevelopment
                        .softwareOptimization,
                  },
                }
              : undefined,
          },
          update: {
            interestPathway: targetedPathway,
            CybersecurityRating: CareerPrepAssessment.cybersecurity
              ? {
                  upsert: {
                    where: { jobseekerId: updatedJobseeker.jobseeker_id },
                    update: {
                      networking: CareerPrepAssessment.cybersecurity.networking,
                      projectManagement:
                        CareerPrepAssessment.cybersecurity.projectManagement,
                      securityTools:
                        CareerPrepAssessment.cybersecurity.securityTools,
                      operatingSystems:
                        CareerPrepAssessment.cybersecurity.operatingSystems,
                      programming:
                        CareerPrepAssessment.cybersecurity.programming,
                      cryptography:
                        CareerPrepAssessment.cybersecurity.cryptography,
                      cloudSecurity:
                        CareerPrepAssessment.cybersecurity.cloudSecurity,
                      incidentResponse:
                        CareerPrepAssessment.cybersecurity.incidentResponse,
                      dataSecurity:
                        CareerPrepAssessment.cybersecurity.dataSecurity,
                      technicalSupport:
                        CareerPrepAssessment.cybersecurity.technicalSupport,
                      computationalThinking:
                        CareerPrepAssessment.cybersecurity
                          .computationalThinking,
                      apiUsage: CareerPrepAssessment.cybersecurity.apiUsage,
                    },
                    create: {
                      networking: CareerPrepAssessment.cybersecurity.networking,
                      projectManagement:
                        CareerPrepAssessment.cybersecurity.projectManagement,
                      securityTools:
                        CareerPrepAssessment.cybersecurity.securityTools,
                      operatingSystems:
                        CareerPrepAssessment.cybersecurity.operatingSystems,
                      programming:
                        CareerPrepAssessment.cybersecurity.programming,
                      cryptography:
                        CareerPrepAssessment.cybersecurity.cryptography,
                      cloudSecurity:
                        CareerPrepAssessment.cybersecurity.cloudSecurity,
                      incidentResponse:
                        CareerPrepAssessment.cybersecurity.incidentResponse,
                      dataSecurity:
                        CareerPrepAssessment.cybersecurity.dataSecurity,
                      technicalSupport:
                        CareerPrepAssessment.cybersecurity.technicalSupport,
                      computationalThinking:
                        CareerPrepAssessment.cybersecurity
                          .computationalThinking,
                      apiUsage: CareerPrepAssessment.cybersecurity.apiUsage,
                    },
                  },
                }
              : undefined,
            DataAnalyticsRating: CareerPrepAssessment.dataAnalytics
              ? {
                  upsert: {
                    where: { jobseekerId: updatedJobseeker.jobseeker_id },
                    update: {
                      dataAnalysis:
                        CareerPrepAssessment.dataAnalytics.dataAnalysis,
                      sqlProgramming:
                        CareerPrepAssessment.dataAnalytics.sqlProgramming,
                      pythonPackages:
                        CareerPrepAssessment.dataAnalytics.pythonPackages,
                      dataScience:
                        CareerPrepAssessment.dataAnalytics.dataScience,
                      dataEngineering:
                        CareerPrepAssessment.dataAnalytics.dataEngineering,
                      tableau: CareerPrepAssessment.dataAnalytics.tableau,
                      machineLearning:
                        CareerPrepAssessment.dataAnalytics.machineLearning,
                      rProgramming:
                        CareerPrepAssessment.dataAnalytics.rProgramming,
                      projectManagement:
                        CareerPrepAssessment.dataAnalytics.projectManagement,
                      dataVisualization:
                        CareerPrepAssessment.dataAnalytics.dataVisualization,
                      dataStructures:
                        CareerPrepAssessment.dataAnalytics.dataStructures,
                      bigOComplexity:
                        CareerPrepAssessment.dataAnalytics.bigOComplexity,
                      sortingAlgorithms:
                        CareerPrepAssessment.dataAnalytics.sortingAlgorithms,
                      databases: CareerPrepAssessment.dataAnalytics.databases,
                      computationalThinking:
                        CareerPrepAssessment.dataAnalytics
                          .computationalThinking,
                    },
                    create: {
                      dataAnalysis:
                        CareerPrepAssessment.dataAnalytics.dataAnalysis,
                      sqlProgramming:
                        CareerPrepAssessment.dataAnalytics.sqlProgramming,
                      pythonPackages:
                        CareerPrepAssessment.dataAnalytics.pythonPackages,
                      dataScience:
                        CareerPrepAssessment.dataAnalytics.dataScience,
                      dataEngineering:
                        CareerPrepAssessment.dataAnalytics.dataEngineering,
                      tableau: CareerPrepAssessment.dataAnalytics.tableau,
                      machineLearning:
                        CareerPrepAssessment.dataAnalytics.machineLearning,
                      rProgramming:
                        CareerPrepAssessment.dataAnalytics.rProgramming,
                      projectManagement:
                        CareerPrepAssessment.dataAnalytics.projectManagement,
                      dataVisualization:
                        CareerPrepAssessment.dataAnalytics.dataVisualization,
                      dataStructures:
                        CareerPrepAssessment.dataAnalytics.dataStructures,
                      bigOComplexity:
                        CareerPrepAssessment.dataAnalytics.bigOComplexity,
                      sortingAlgorithms:
                        CareerPrepAssessment.dataAnalytics.sortingAlgorithms,
                      databases: CareerPrepAssessment.dataAnalytics.databases,
                      computationalThinking:
                        CareerPrepAssessment.dataAnalytics
                          .computationalThinking,
                    },
                  },
                }
              : undefined,
            ITCloudRating: CareerPrepAssessment.itAndCloudComputing
              ? {
                  upsert: {
                    where: { jobseekerId: updatedJobseeker.jobseeker_id },
                    update: {
                      techSupport:
                        CareerPrepAssessment.itAndCloudComputing.techSupport,
                      activeDirectory:
                        CareerPrepAssessment.itAndCloudComputing
                          .activeDirectory,
                      projectManagement:
                        CareerPrepAssessment.itAndCloudComputing
                          .projectManagement,
                      helpDeskSupport:
                        CareerPrepAssessment.itAndCloudComputing
                          .helpDeskSupport,
                      windowsServers:
                        CareerPrepAssessment.itAndCloudComputing.windowsServers,
                      sqlProgramming:
                        CareerPrepAssessment.itAndCloudComputing.sqlProgramming,
                      computerHardware:
                        CareerPrepAssessment.itAndCloudComputing
                          .computerHardware,
                      operatingSystems:
                        CareerPrepAssessment.itAndCloudComputing
                          .operatingSystems,
                      systemAdmin:
                        CareerPrepAssessment.itAndCloudComputing.systemAdmin,
                      networkAdmin:
                        CareerPrepAssessment.itAndCloudComputing.networkAdmin,
                      virtualization:
                        CareerPrepAssessment.itAndCloudComputing.virtualization,
                      coreCloudServices:
                        CareerPrepAssessment.itAndCloudComputing
                          .coreCloudServices,
                      apiUsage:
                        CareerPrepAssessment.itAndCloudComputing.apiUsage,
                      httpResponseCodes:
                        CareerPrepAssessment.itAndCloudComputing
                          .httpResponseCodes,
                      computationalThinking:
                        CareerPrepAssessment.itAndCloudComputing
                          .computationalThinking,
                    },
                    create: {
                      techSupport:
                        CareerPrepAssessment.itAndCloudComputing.techSupport,
                      activeDirectory:
                        CareerPrepAssessment.itAndCloudComputing
                          .activeDirectory,
                      projectManagement:
                        CareerPrepAssessment.itAndCloudComputing
                          .projectManagement,
                      helpDeskSupport:
                        CareerPrepAssessment.itAndCloudComputing
                          .helpDeskSupport,
                      windowsServers:
                        CareerPrepAssessment.itAndCloudComputing.windowsServers,
                      sqlProgramming:
                        CareerPrepAssessment.itAndCloudComputing.sqlProgramming,
                      computerHardware:
                        CareerPrepAssessment.itAndCloudComputing
                          .computerHardware,
                      operatingSystems:
                        CareerPrepAssessment.itAndCloudComputing
                          .operatingSystems,
                      systemAdmin:
                        CareerPrepAssessment.itAndCloudComputing.systemAdmin,
                      networkAdmin:
                        CareerPrepAssessment.itAndCloudComputing.networkAdmin,
                      virtualization:
                        CareerPrepAssessment.itAndCloudComputing.virtualization,
                      coreCloudServices:
                        CareerPrepAssessment.itAndCloudComputing
                          .coreCloudServices,
                      apiUsage:
                        CareerPrepAssessment.itAndCloudComputing.apiUsage,
                      httpResponseCodes:
                        CareerPrepAssessment.itAndCloudComputing
                          .httpResponseCodes,
                      computationalThinking:
                        CareerPrepAssessment.itAndCloudComputing
                          .computationalThinking,
                    },
                  },
                }
              : undefined,
            SoftwareDevRating: CareerPrepAssessment.softwareDevelopment
              ? {
                  upsert: {
                    where: { jobseekerId: updatedJobseeker.jobseeker_id },
                    update: {
                      softwareEngineering:
                        CareerPrepAssessment.softwareDevelopment
                          .softwareEngineering,
                      softwareDevelopmentLifecycle:
                        CareerPrepAssessment.softwareDevelopment
                          .softwareDevelopmentLifecycle,
                      programmingLanguages:
                        CareerPrepAssessment.softwareDevelopment
                          .programmingLanguages,
                      dataStructuresAndAlgorithms:
                        CareerPrepAssessment.softwareDevelopment
                          .dataStructuresAndAlgorithms,
                      softwareArchitecture:
                        CareerPrepAssessment.softwareDevelopment
                          .softwareArchitecture,
                      versionControl:
                        CareerPrepAssessment.softwareDevelopment.versionControl,
                      databaseManagement:
                        CareerPrepAssessment.softwareDevelopment
                          .databaseManagement,
                      devOps: CareerPrepAssessment.softwareDevelopment.devOps,
                      cloudComputing:
                        CareerPrepAssessment.softwareDevelopment.cloudComputing,
                      conceptualSystemsThinking:
                        CareerPrepAssessment.softwareDevelopment
                          .conceptualSystemsThinking,
                      problemSolving:
                        CareerPrepAssessment.softwareDevelopment.problemSolving,
                      fundamentalCodingConcepts:
                        CareerPrepAssessment.softwareDevelopment
                          .fundamentalCodingConcepts,
                      debugging:
                        CareerPrepAssessment.softwareDevelopment.debugging,
                      computationalThinking:
                        CareerPrepAssessment.softwareDevelopment
                          .computationalThinking,
                      softwareOptimization:
                        CareerPrepAssessment.softwareDevelopment
                          .softwareOptimization,
                    },
                    create: {
                      softwareEngineering:
                        CareerPrepAssessment.softwareDevelopment
                          .softwareEngineering,
                      softwareDevelopmentLifecycle:
                        CareerPrepAssessment.softwareDevelopment
                          .softwareDevelopmentLifecycle,
                      programmingLanguages:
                        CareerPrepAssessment.softwareDevelopment
                          .programmingLanguages,
                      dataStructuresAndAlgorithms:
                        CareerPrepAssessment.softwareDevelopment
                          .dataStructuresAndAlgorithms,
                      softwareArchitecture:
                        CareerPrepAssessment.softwareDevelopment
                          .softwareArchitecture,
                      versionControl:
                        CareerPrepAssessment.softwareDevelopment.versionControl,
                      databaseManagement:
                        CareerPrepAssessment.softwareDevelopment
                          .databaseManagement,
                      devOps: CareerPrepAssessment.softwareDevelopment.devOps,
                      cloudComputing:
                        CareerPrepAssessment.softwareDevelopment.cloudComputing,
                      conceptualSystemsThinking:
                        CareerPrepAssessment.softwareDevelopment
                          .conceptualSystemsThinking,
                      problemSolving:
                        CareerPrepAssessment.softwareDevelopment.problemSolving,
                      fundamentalCodingConcepts:
                        CareerPrepAssessment.softwareDevelopment
                          .fundamentalCodingConcepts,
                      debugging:
                        CareerPrepAssessment.softwareDevelopment.debugging,
                      computationalThinking:
                        CareerPrepAssessment.softwareDevelopment
                          .computationalThinking,
                      softwareOptimization:
                        CareerPrepAssessment.softwareDevelopment
                          .softwareOptimization,
                    },
                  },
                }
              : undefined,
          },
          select: {
            CybersecurityRating: true,
            ITCloudRating: true,
            DataAnalyticsRating: true,
            SoftwareDevRating: true,
          },
        });

        const mapOverall = <T extends { overallAverage?: unknown }>(r: T) =>
          r
            ? {
                ...r,
                overallAverage:
                  r.overallAverage != null ? Number(r.overallAverage) : null,
              }
            : null;
        return {
          userId: updatedJobseeker.user_id,
          targetedPathway: targetedPathway
            ? (targetedPathway as CareerPrepPathways)
            : null,
          CareerPrepAssessment: {
            cybersecurity: mapOverall(
              careerPrep.CybersecurityRating[0] ?? null,
            ),
            dataAnalytics: mapOverall(
              careerPrep.DataAnalyticsRating[0] ?? null,
            ),
            itAndCloudComputing: mapOverall(
              careerPrep.ITCloudRating[0] ?? null,
            ),
            softwareDevelopment: mapOverall(
              careerPrep.SoftwareDevRating[0] ?? null,
            ),
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
