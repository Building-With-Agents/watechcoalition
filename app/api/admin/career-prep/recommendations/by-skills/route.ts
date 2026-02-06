import { NextRequest, NextResponse } from "next/server";
import { PrismaClient, Prisma } from "@prisma/client";

const prisma = new PrismaClient();
const TOP_RECOMMENDATIONS = 10;

interface RequestBody {
  skillIds: string[];
}

type MatchedSkillDetail = {
  job_skill_name: string;
  seeker_skill_name: string;
  score: number;
};

type RecommendationResult = {
  jobseeker_id: string;
  user_id: string;
  first_name: string | null;
  last_name: string | null;
  hasResume: boolean;
  email: string;
  final_score: number;
  matched_skills: MatchedSkillDetail[];
};

export async function POST(request: NextRequest) {
  let body: RequestBody;
  try {
    body = await request.json();
  } catch {
    return NextResponse.json({ error: "Invalid JSON body" }, { status: 400 });
  }

  const { skillIds } = body;
  if (!Array.isArray(skillIds) || skillIds.length === 0) {
    return NextResponse.json(
      { error: "skillIds must be a non-empty array of strings" },
      { status: 400 },
    );
  }
  if (!skillIds.every((id) => typeof id === "string")) {
    return NextResponse.json(
      { error: "All skillIds must be strings" },
      { status: 400 },
    );
  }

  try {
    const skillParams = Prisma.join(skillIds.map((id) => Prisma.sql`${id}`));

    const query = Prisma.sql`
      WITH JobSkills AS (
        SELECT skill_id, skill_name, embedding
        FROM skills
        WHERE skill_id IN (${skillParams}) AND embedding IS NOT NULL
      ),
      JobseekerSkills AS (
        SELECT jhs.jobseeker_id,
               s.skill_id        AS seeker_skill_id,
               s.skill_name      AS seeker_skill_name,
               s.embedding
        FROM jobseeker_has_skills jhs
        JOIN skills s ON jhs.skill_id = s.skill_id
        WHERE s.embedding IS NOT NULL
      ),
      SimilarityScores AS (
        SELECT
          js.jobseeker_id,
          jks.skill_name      AS job_skill_name,
          js.seeker_skill_name,
          1.0 - VECTOR_DISTANCE('COSINE', jks.embedding, js.embedding) AS similarity
        FROM JobSkills jks
        CROSS JOIN JobseekerSkills js
      ),
      RankedSimilarityScores AS (
        SELECT
          jobseeker_id,
          job_skill_name,
          seeker_skill_name,
          similarity,
          ROW_NUMBER() OVER (PARTITION BY jobseeker_id, job_skill_name ORDER BY similarity DESC) as rn
        FROM SimilarityScores
        WHERE similarity BETWEEN 0.0 AND 1.0
      ),
      BestMatches AS (
        SELECT
          jobseeker_id,
          job_skill_name,
          seeker_skill_name,
          similarity AS max_similarity
        FROM RankedSimilarityScores
        WHERE rn = 1
      ),
      AggregatedMatchedSkills AS (
        SELECT
          jobseeker_id,
          STRING_AGG(
            CONCAT(job_skill_name, ':', seeker_skill_name, ':', CAST(max_similarity AS VARCHAR(10))),
            ';'
          ) WITHIN GROUP (ORDER BY job_skill_name) AS matched_text
        FROM BestMatches
        GROUP BY jobseeker_id
      ),
      TotalScore AS (
        SELECT
          jobseeker_id,
          AVG(max_similarity) AS average_similarity
        FROM BestMatches
        GROUP BY jobseeker_id
      )
      SELECT TOP (${TOP_RECOMMENDATIONS})
        ts.jobseeker_id,
        j.user_id,
        j.hasResume,
        u.first_name,
        u.last_name,
        u.email,
        ts.average_similarity AS final_score,
        ams.matched_text
      FROM TotalScore ts
      JOIN jobseekers j ON ts.jobseeker_id = j.jobseeker_id
      JOIN users u ON j.user_id = u.id
      LEFT JOIN AggregatedMatchedSkills ams ON ts.jobseeker_id = ams.jobseeker_id
      ORDER BY final_score DESC
    `;

    const dbResults: Array<{
      jobseeker_id: string;
      user_id: string;
      first_name: string | null;
      last_name: string | null;
      hasResume: boolean;
      email: string;
      final_score: number;
      matched_text: string | null;
    }> = await prisma.$queryRaw(query);

    if (dbResults.length === 0) {
      return NextResponse.json(
        { message: "No matching candidates found for the provided skills." },
        { status: 200 },
      );
    }

    const results: RecommendationResult[] = dbResults.map((row) => {
      const matched_skills: MatchedSkillDetail[] = [];
      if (row.matched_text) {
        row.matched_text.split(";").forEach((segment) => {
          const [job_skill_name, seeker_skill_name, scoreStr] = segment.split(
            ":",
            3,
          );
          const score = parseFloat(scoreStr);
          if (job_skill_name && seeker_skill_name && !isNaN(score)) {
            matched_skills.push({
              job_skill_name,
              seeker_skill_name,
              score: parseFloat(score.toFixed(4)),
            });
          }
        });
      }
      return {
        jobseeker_id: row.jobseeker_id,
        user_id: row.user_id,
        first_name: row.first_name,
        last_name: row.last_name,
        hasResume: row.hasResume,
        email: row.email,
        final_score: row.final_score,
        matched_skills,
      };
    });

    return NextResponse.json(results);
  } catch (err) {
    console.error("Error in recommendations route:", err);
    return NextResponse.json(
      { error: "Failed to fetch recommendations by skills" },
      { status: 500 },
    );
  }
}
