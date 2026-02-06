import { NextRequest, NextResponse } from "next/server";
import { PrismaClient, Prisma } from "@prisma/client";
import { auth } from "@/auth";
import { Role } from "@/data/dtos/UserInfoDTO";

const prisma = new PrismaClient();
const TOP_RECOMMENDATIONS = 10;

export async function GET(
  request: NextRequest,
  { params }: { params: Promise<{ jobId: string }> },
) {
  const session = await auth();
  if (
    !session?.user.roles.includes(Role.CASE_MANAGER) &&
    !session?.user.roles.includes(Role.ADMIN)
  ) {
    return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
  }
  const jobId = (await params).jobId;

  if (!jobId) {
    return NextResponse.json({ error: "Job ID is required" }, { status: 400 });
  }

  try {
    const recommendationsQuery = Prisma.sql`
        WITH JobSkills AS (
            SELECT
                s.skill_id,
                s.embedding
            FROM skills s
            JOIN _JobPostingSkills jps ON s.skill_id = jps.B
            WHERE jps.A = ${jobId} AND s.embedding IS NOT NULL
        ),
        JobseekerSkills AS (
            SELECT
                jhs.jobseeker_id,
                s.skill_id,
                s.embedding
            FROM skills s
            JOIN jobseeker_has_skills jhs ON s.skill_id = jhs.skill_id
            WHERE s.embedding IS NOT NULL
        ),
        SimilarityScores AS (
            -- Calculate cosine similarity for every job skill vs every jobseeker skill
            -- Similarity = 1 - Cosine Distance
            SELECT
                js.jobseeker_id,
                jks.skill_id AS job_skill_id,
                (1.0 - VECTOR_DISTANCE('COSINE', jks.embedding, js.embedding)) AS similarity
            FROM JobSkills jks
            CROSS JOIN JobseekerSkills js
        ),
        MaxSimilarityPerJobSkill AS (
            -- Find the maximum similarity for each job skill for each jobseeker
            SELECT
                jobseeker_id,
                job_skill_id,
                MAX(similarity) AS max_similarity
            FROM SimilarityScores
            WHERE similarity >= 0.0 AND similarity <= 1.0 -- Filter based on SIMILARITY range [0, 1] is typical desired range
            GROUP BY jobseeker_id, job_skill_id
        ),
        TotalScorePerJobseeker AS (
            SELECT
                jobseeker_id,
                SUM(max_similarity) AS total_similarity_sum
            FROM MaxSimilarityPerJobSkill
            GROUP BY jobseeker_id
        ),
        JobSkillCount AS (
            SELECT CAST(COUNT(*) AS FLOAT) as count FROM JobSkills
        ),
        FinalScores AS (
            SELECT
                ts.jobseeker_id,
                j.user_id,
                u.first_name,
                u.last_name,
                u.email,
                CASE
                    WHEN (SELECT count FROM JobSkillCount) > 0
                    THEN ts.total_similarity_sum / (SELECT count FROM JobSkillCount)
                    ELSE 0.0
                END AS final_score
            FROM TotalScorePerJobseeker ts
            JOIN jobseekers j ON ts.jobseeker_id = j.jobseeker_id
            JOIN users u ON j.user_id = u.id
            CROSS JOIN JobSkillCount -- Make count available
            WHERE JobSkillCount.count > 0 -- Only include if job has skills
        )
        SELECT TOP (${TOP_RECOMMENDATIONS})
            jobseeker_id,
            user_id,
            first_name,
            last_name,
            email,
            final_score
        FROM FinalScores
        ORDER BY final_score DESC;
    `;

    type RecommendationResult = {
      jobseeker_id: string;
      user_id: string;
      first_name: string | null;
      last_name: string | null;
      email: string;
      final_score: number;
    };

    const results =
      await prisma.$queryRaw<RecommendationResult[]>(recommendationsQuery);

    if (results.length === 0) {
      return NextResponse.json(
        { message: "No matching candidates found." },
        { status: 200 },
      );
    }

    return NextResponse.json(results);
  } catch (error) {
    console.error("Error fetching recommendations:", error);
    return NextResponse.json(
      { error: "Failed to fetch recommendations" },
      { status: 500 },
    );
  }
}
