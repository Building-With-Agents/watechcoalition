import { Prisma, PrismaClient } from "@prisma/client";
import getPrismaClient from "./prismaClient.mjs";
import { auth } from "@/auth";

const prisma: PrismaClient = getPrismaClient();

export type RoleInfo = {
  role_id: string;
  title: string;
};

export type PathwayStructure = {
  pathway_id: string;
  pathway_title: string;
  roles: RoleInfo[];
};

export type ICTRecommendationResult = {
  id: string;
  jobseeker_id: string;
  first_name: string;
  last_name: string;
  email: string;
  hasResume: boolean;
  final_score: number;
};

type SkillRatings = {
  [key: string]: number;
};

interface FeedbackResult {
  success: boolean;
  message: string;
}

export async function getJobRolesPerPathway() {
  try {
    const pathwaysWithRoles = await prisma.pathways.findMany({
      orderBy: {
        pathway_title: "asc",
      },
      select: {
        pathway_id: true,
        pathway_title: true,
        jobRoles: {
          orderBy: {
            title: "asc",
          },
          select: {
            id: true,
            title: true,
          },
        },
      },
    });

    if (!pathwaysWithRoles || pathwaysWithRoles.length === 0) {
      return [];
    }

    const result: PathwayStructure[] = pathwaysWithRoles.map((pathway) => ({
      pathway_id: pathway.pathway_id,
      pathway_title: pathway.pathway_title,
      roles: pathway.jobRoles.map((role) => ({
        role_id: role.id,
        title: role.title,
      })),
    }));
    return result;
  } catch (error) {
    console.error(error);
  }
}

export async function getJobRole(id: string) {
  try {
    const jobRole = await prisma.jobRole.findUnique({
      where: {
        id: id,
      },
      include: {
        skills: {
          include: {
            skill: {
              select: {
                skill_name: true,
              },
            },
          },
        },
      },
    });
    return jobRole;
  } catch (error) {
    console.error(error);
  }
}

export async function getRecommendedJobSeekersByJobRole(jobRoleId: string) {
  const SIMILARITY_THRESHOLD = 0.4;
  try {
    const recommendationsQuery = Prisma.sql`
          WITH JobRoleSkills AS (
            SELECT
              jrs.jobRoleId   AS role_id,
              s.skill_id      AS role_skill_id,
              s.embedding     AS role_embedding
            FROM JobRoleSkill jrs
            JOIN skills s ON jrs.skillId = s.skill_id
            WHERE s.embedding IS NOT NULL
            AND jrs.jobRoleId = ${jobRoleId}
          ),

          JobseekerSkills AS (
            SELECT
              js.jobseeker_id AS jobseeker_id,
              s.skill_id      AS jobseeker_skill_id,
              s.embedding     AS jobseeker_embedding
            FROM jobseeker_has_skills js
            JOIN skills s ON js.skill_id = s.skill_id
            WHERE s.embedding IS NOT NULL
          ),

          BestMatchPerRoleSkill AS (
            SELECT
              jrs.role_id,
              jsk.jobseeker_id,
              jrs.role_skill_id,
              MAX(1.0 - VECTOR_DISTANCE('COSINE', jrs.role_embedding, jsk.jobseeker_embedding)) AS best_similarity_for_role_skill
            FROM JobRoleSkills jrs
            CROSS JOIN JobseekerSkills jsk
            GROUP BY
              jrs.role_id,
              jsk.jobseeker_id,
              jrs.role_skill_id
          ),

          FilteredBestMatch AS (
            SELECT
                role_id,
                jobseeker_id,
                role_skill_id,
                best_similarity_for_role_skill
            FROM BestMatchPerRoleSkill
            WHERE best_similarity_for_role_skill >= 0 AND best_similarity_for_role_skill <= 1.0
          ),

          TotalPerRole AS (
            SELECT
              jobseeker_id,
              role_id,
              SUM(best_similarity_for_role_skill) AS sum_similarity
            FROM FilteredBestMatch
            GROUP BY jobseeker_id, role_id
          ),

          RoleSkillCounts AS (
            SELECT
              role_id,
              COUNT(DISTINCT role_skill_id) AS total_role_skill_count
            FROM JobRoleSkills
            GROUP BY role_id
          ),

          FinalScores AS (
            SELECT
              tpr.jobseeker_id,
              j.hasResume,
              u.first_name,
              u.last_name,
              u.email,
              u.id,
              CASE
                WHEN rsc.total_role_skill_count > 0 THEN tpr.sum_similarity / CAST(rsc.total_role_skill_count AS float)
                ELSE 0
              END AS final_score
            FROM TotalPerRole tpr
            JOIN RoleSkillCounts rsc ON tpr.role_id = rsc.role_id
            JOIN jobseekers j        ON j.jobseeker_id = tpr.jobseeker_id
            JOIN users u             ON u.id = j.user_id
            WHERE tpr.role_id = ${jobRoleId}
          )

          SELECT
            fs.id,
            fs.jobseeker_id,
            fs.first_name,
            fs.last_name,
            fs.hasResume,
            fs.email,
            fs.final_score
          FROM FinalScores fs
          WHERE fs.final_score > ${SIMILARITY_THRESHOLD}
          ORDER BY fs.final_score DESC;
        `;

    const results =
      await prisma.$queryRaw<ICTRecommendationResult[]>(recommendationsQuery);

    if (results.length === 0) {
      return [];
    }

    return results;
  } catch (error) {
    console.error(error);
  }
}

export async function TakeEmployerFeedBack(
  jobRoleId: string,
  skillRatings: SkillRatings,
): Promise<FeedbackResult> {
  try {
    const session = await auth();
    if (!session?.user.id)
      return {
        success: false,
        message: "user id needed",
      };

    const submiterId = session.user.id;
    const validSkills = await prisma.skills.findMany({
      select: {
        skill_id: true,
      },
    });

    // Convert validSkills to a set for fast lookup
    const validSkillIds = new Set(validSkills.map((skill) => skill.skill_id));
    console.log(Object.entries(skillRatings));
    // Filter the skillRatings to only include valid skillIds
    const feedbacks = Object.entries(skillRatings)
      .filter(([skillId]) => validSkillIds.has(skillId))
      .map(([skillId, likertRating]) => ({
        jobRoleId,
        skillId,
        likertRating,
        submiterid: submiterId,
      }));
    await prisma.employerJobRoleFeedBack.createMany({ data: feedbacks });

    return {
      success: true,
      message: "Feedback processed successfully.",
    };
  } catch (error) {
    console.error("Error in processing feedback:", error);
    return {
      success: false,
      message: "An error occurred while processing feedback.",
    };
  }
}
