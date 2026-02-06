import { NextResponse } from "next/server";
import { PrismaClient } from "@prisma/client";
import {
  CertDTO,
  HighestCompletedEducationLevel,
  EducationLevel,
  JsEducationInfoDTO,
  JsEducationPageDTO,
  ProjectExpDTO,
  CollegeDegreeType,
  HighSchoolDegreeType,
  PreAEduSystem,
  ProgramEnrollmentStatus,
} from "@/data/dtos/JobSeekerProfileCreationDTOs";
import { mapToEnum, mapToEnumOrThrow } from "@/app/lib/utils";
import getPrismaClient from "@/app/lib/prismaClient.mjs";
import { JobseekerSkillDTO } from "@/data/dtos/JobseekerSkillDTO";
import { TimeUntilCompletion } from "@/app/lib/admin/careerPrep";

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
        { error: "User ID is required" },
        { status: 400 },
      );
    }

    // Fetch the jobseeker data
    const jobseeker = await prisma.jobseekers.findUnique({
      where: { user_id: userId },
      select: {
        user_id: true,
        current_enrolled_ed_program: true,
        highest_level_of_study_completed: true,
        current_grade_level: true,
        is_enrolled_ed_program: true,
        jobseeker_education: {
          select: {
            id: true,
            eduProviderId: true,
            eduProviders: {
              select: {
                name: true,
              },
            },
            edLevel: true,
            preAppEdSystem: true,
            isEnrolled: true,
            enrollmentStatus: true,
            startDate: true,
            gradDate: true,
            degreeType: true,
            program: {
              select: {
                id: true,
                title: true,
              },
            },
            gpa: true,
            description: true,
          },
        },
        certificates: {
          select: {
            certId: true,
            name: true,
            logoUrl: true,
            issuingOrg: true,
            credentialId: true,
            credentialUrl: true,
            issueDate: true,
            expiryDate: true,
            description: true,
          },
        },
        project_experiences: {
          select: {
            projectId: true,
            projTitle: true,
            projectRole: true,
            startDate: true,
            completionDate: true,
            problemSolvedDescription: true,
            teamSize: true,
            demoUrl: true,
            repoUrl: true,
            project_has_skills: {
              select: {
                skills: {
                  select: {
                    skill_id: true,
                    skill_subcategory_id: true,
                    skill_name: true,
                    skill_info_url: true,
                  },
                },
              },
            },
          },
        },
        CareerPrepAssessment: {
          select: {
            expectedEduCompletion: true,
          },
        },
      },
    });
    console.log(JSON.stringify(jobseeker, null, 2));
    if (!jobseeker) {
      return NextResponse.json(
        { error: "Jobseeker not found" },
        { status: 404 },
      );
    }

    // Map the jobseeker data to DTOs
    const edHistory: JsEducationInfoDTO[] = jobseeker.jobseeker_education.map(
      (edu) => ({
        id: edu.id,
        edLevel: mapToEnumOrThrow(edu.edLevel, EducationLevel),
        edProviderId: edu.eduProviderId!, //these should always exist on an entry
        edProviderName: edu.eduProviders.name! ?? undefined, //these should always exist on an entry
        preAppEdSystem: mapToEnumOrThrow(edu?.preAppEdSystem, PreAEduSystem),
        isEnrolled: edu.isEnrolled,
        enrollmentStatus: mapToEnum(
          edu.enrollmentStatus,
          ProgramEnrollmentStatus,
        ),
        startDate: edu.startDate.toISOString(),
        gradDate: edu.gradDate.toISOString(),
        degreeType:
          mapToEnum(edu.degreeType, CollegeDegreeType) ||
          mapToEnumOrThrow(edu.degreeType, HighSchoolDegreeType),
        programId: edu?.program?.id!, //these should always exist on an entry
        programName: edu?.program?.title!, //these should always exist on an entry
        gpa: edu.gpa,
        description: edu.description,
      }),
    );

    const certs: CertDTO[] = jobseeker.certificates.map((cert) => ({
      certId: cert.certId,
      name: cert.name,
      logoUrl: cert.logoUrl,
      issuingOrg: cert.issuingOrg,
      credentialId: cert.credentialId,
      credentialUrl: cert.credentialUrl,
      issueDate: cert?.issueDate?.toISOString(),
      expiryDate: cert?.expiryDate?.toISOString(),
      description: cert.description,
    }));

    const projects: ProjectExpDTO[] = jobseeker.project_experiences.map(
      (proj) => ({
        projectId: proj.projectId,
        projTitle: proj.projTitle,
        projectRole: proj.projectRole,
        startDate: proj.startDate.toISOString(),
        completionDate: proj.completionDate.toISOString(),
        problemSolvedDescription: proj.problemSolvedDescription,
        teamSize: proj.teamSize.toString(),
        repoUrl: proj.repoUrl,
        demoUrl: proj.demoUrl,
        skills: proj.project_has_skills.map((s: JobseekerSkillDTO) => ({
          skill_id: s.skills.skill_id,
          skill_name: s.skills.skill_name,
          skill_info_url: s.skills.skill_info_url,
        })),
      }),
    );

    const result: JsEducationPageDTO = {
      userId: jobseeker.user_id,
      highestLevelOfStudy: mapToEnum(
        jobseeker.highest_level_of_study_completed,
        HighestCompletedEducationLevel,
      ),
      educations: edHistory,
      certifications: certs,
      projects: projects,
      CareerPrepAssessment: {
        expectedEduCompletion:
          jobseeker.CareerPrepAssessment.length > 0
            ? (jobseeker.CareerPrepAssessment[0]
                .expectedEduCompletion as TimeUntilCompletion)
            : TimeUntilCompletion.NA,
      },
    };

    return NextResponse.json(
      {
        success: true,
        result,
      },
      { status: 200 },
    );
  } catch (e: any) {
    console.log(e.message);
    return NextResponse.json(
      { error: `Failed to fetch jobseeker data.\n${e.message} ` },
      { status: 500 },
    );
  } finally {
    await prisma.$disconnect();
  }
}
