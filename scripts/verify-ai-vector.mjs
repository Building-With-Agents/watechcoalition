import dotenv from "dotenv";
import { AzureOpenAI } from "openai";
import getPrismaClient from "../app/lib/prismaClient.mjs";

// Load local config (gitignored). Do not print secrets.
dotenv.config({ path: ".env" });
dotenv.config({ path: ".env.local", override: true });

function requireEnv(name) {
  const v = process.env[name];
  if (!v) throw new Error(`Missing env var: ${name}`);
  return v;
}

async function main() {
  const prisma = getPrismaClient();

  const endpoint = requireEnv("AZURE_OPENAI_EMBEDDING_ENDPOINT");
  const apiKey = requireEnv("AZURE_OPENAI_EMBEDDING_API_KEY");
  const apiVersion = requireEnv("AZURE_OPENAI_EMBEDDING_API_VERSION");
  const deployment = requireEnv("AZURE_OPENAI_EMBEDDING_DEPLOYMENT_NAME");

  const client = new AzureOpenAI({
    endpoint,
    apiKey,
    apiVersion,
    deployment,
  });

  // Pick a skill row to update
  const skill =
    (await prisma.skills.findFirst({
      where: { skill_name: { equals: "Python" } },
      select: { skill_id: true, skill_name: true },
    })) ??
    (await prisma.skills.findFirst({
      select: { skill_id: true, skill_name: true },
    }));

  if (!skill) {
    throw new Error("No skills found in DB (skills table is empty).");
  }

  // Generate and store an embedding for this one skill (small, safe test)
  const embResp = await client.embeddings.create({
    model: deployment,
    input: skill.skill_name,
    dimensions: 1536,
  });
  const embedding = embResp.data?.[0]?.embedding;
  if (!Array.isArray(embedding) || embedding.length !== 1536) {
    throw new Error("Embeddings response did not return a 1536-dim vector.");
  }

  const embeddingString = JSON.stringify(embedding);
  await prisma.$executeRaw`
    UPDATE skills
    SET embedding = CAST(${embeddingString} AS VECTOR(1536))
    WHERE skill_id = ${skill.skill_id}
  `;

  // Now run a vector-distance query (mirrors app/lib/prisma.ts logic)
  const queryResp = await client.embeddings.create({
    model: deployment,
    input: skill.skill_name,
    dimensions: 1536,
  });
  const queryVector = queryResp.data?.[0]?.embedding;
  const queryVectorJsonString = JSON.stringify(queryVector);

  const results = await prisma.$queryRaw`
    SELECT TOP (5)
      skill_id,
      skill_name,
      VECTOR_DISTANCE('COSINE', embedding, CAST(${queryVectorJsonString} AS VECTOR(1536))) as distance
    FROM skills
    WHERE embedding IS NOT NULL
    ORDER BY distance ASC;
  `;

  console.log("vector_query_ok", {
    updatedSkill: { id: skill.skill_id, name: skill.skill_name },
    topResults: results,
  });
}

await main();

