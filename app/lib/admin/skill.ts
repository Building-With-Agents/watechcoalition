import { auth } from "@/auth";
import { Role } from "@/data/dtos/UserInfoDTO";
import {
  PrismaClient,
  PrismaPromise,
  skill_subcategories,
} from "@prisma/client";
import getPrismaClient from "../prismaClient.mjs";
import { v4 as uuidv4 } from "uuid";
import { SkillDTO } from "@/data/dtos/SkillDTO";
import { getEmbeddingsClient } from "../openAiClients";
const prisma: PrismaClient = getPrismaClient();

async function generateAndStoreEmbeddings(
  skillsToEmbed: Pick<SkillDTO, "skill_id" | "skill_name">[],
) {
  if (!skillsToEmbed || skillsToEmbed.length === 0) {
    return { updated: 0 };
  }
  const client = getEmbeddingsClient();

  try {
    const skillMap = new Map(
      skillsToEmbed.map((s) => [s.skill_name, s.skill_id]),
    );
    const skillNames = skillsToEmbed.map((skill) => skill.skill_name);

    const BATCH_SIZE = 50;
    const updateOps: PrismaPromise<any>[] = [];

    for (let start = 0; start < skillNames.length; start += BATCH_SIZE) {
      const batchNames = skillNames.slice(start, start + BATCH_SIZE);
      const resp = await client.embeddings.create({
        model: process.env.AZURE_OPENAI_EMBEDDING_DEPLOYMENT_NAME!,
        input: batchNames,
        dimensions: 1536,
      });

      for (const item of resp.data) {
        const idxInBatch = item.index;
        const skillName = batchNames[idxInBatch];
        const skillId = skillMap.get(skillName);
        const embedding = item.embedding;

        if (!skillId) {
          console.warn(
            `Could not find skill_id for skill name "${skillName}" in the provided map. Skipping embedding update.`,
          );
          continue;
        }
        if (!Array.isArray(embedding)) {
          console.warn(
            `No embedding generated for skill: ${skillName} (ID: ${skillId}). Skipping.`,
          );
          continue;
        }

        const embeddingString = JSON.stringify(embedding);
        updateOps.push(
          prisma.$executeRaw`UPDATE skills SET embedding = CAST(${embeddingString} AS VECTOR(1536)) WHERE skill_id = ${skillId}`,
        );
      }
    }

    if (updateOps.length > 0) {
      await prisma.$transaction(updateOps);
    }

    return { updated: updateOps.length };
  } catch (error) {
    console.error("Error generating or storing skill embeddings:", error);
    return {
      updated: 0,
      error: `Embedding generation failed: ${error instanceof Error ? error.message : String(error)}`,
    };
  }
}

export async function adminCreateSkills(skillDataArray: SkillDTO[]) {
  const Session = await auth();
  if (!Session?.user.roles.includes(Role.ADMIN)) {
    throw new Error("Must Be Admin to complete this task");
  }
  if (!Session?.user.id) {
    throw new Error("Must Be a user to complete this task");
  }
  let newlyCreatedSkillsForEmbedding: Pick<
    SkillDTO,
    "skill_id" | "skill_name"
  >[] = [];
  try {
    // First, get all existing skill names (case insensitive)
    const existingSkills = await prisma.skills.findMany({
      where: {
        skill_name: {
          in: skillDataArray.map((skill) => skill.skill_name),
        },
      },
      select: {
        skill_name: true,
      },
    });

    const existingSkillNames = new Set(
      existingSkills.map((skill) => skill.skill_name.toLowerCase()),
    );

    // Filter out skills that already exist
    const newSkills = skillDataArray.filter(
      (skill) => !existingSkillNames.has(skill.skill_name.toLowerCase()),
    );

    if (newSkills.length === 0) {
      return {
        count: 0,
        skipped: skillDataArray.length,
        message: "All skills already exist",
      };
    }

    // Create only the new skills
    const skillsToCreate = newSkills.map((skillData) => ({
      skill_id: uuidv4(),
      skill_name: skillData.skill_name,
      skill_subcategory_id: skillData.skill_subcategory_id || "",
      skill_info_url: skillData.skill_info_url || "",
    }));
    const creationResult = await prisma.skills.createMany({
      data: skillsToCreate,
    });

    if (creationResult.count > 0) {
      newlyCreatedSkillsForEmbedding = skillsToCreate
        .filter((created) =>
          newSkills.some(
            (newData) => newData.skill_name === created.skill_name,
          ),
        )
        .map((s) => ({ skill_id: s.skill_id, skill_name: s.skill_name }));
      await generateAndStoreEmbeddings(newlyCreatedSkillsForEmbedding);
    }

    return creationResult;
  } catch (e) {
    console.error("Error creating skills:", e);
    throw e;
  }
}

export async function adminUpdateSkill(skillData: SkillDTO) {
  const Session = await auth();
  if (!Session?.user.roles.includes(Role.ADMIN)) {
    throw new Error("Must Be Admin to complete this task");
  }
  if (!Session?.user.id) {
    throw new Error("Must Be a user to complete this task");
  }
  if (!skillData.skill_id) {
    throw new Error("Skill ID is required for update.");
  }

  try {
    const currentSkill = await prisma.skills.findUnique({
      where: { skill_id: skillData.skill_id },
      select: { skill_name: true },
    });
    if (!currentSkill) {
      throw new Error(`Skill with ID ${skillData.skill_id} not found.`);
    }

    const nameHasChanged = currentSkill.skill_name !== skillData.skill_name;
    const result = await prisma.skills.update({
      where: {
        skill_id: skillData.skill_id,
      },
      data: {
        skill_name: skillData.skill_name,
        skill_subcategory_id: skillData.skill_subcategory_id,
        skill_info_url: skillData.skill_info_url,
      },
    });
    if (nameHasChanged) {
      await generateAndStoreEmbeddings([
        {
          skill_id: result.skill_id,
          skill_name: result.skill_name,
        },
      ]);
    }

    return result;
  } catch (e) {
    console.error("Error updating skill:", e);
    throw e;
  }
}

export async function adminGetSkills() {
  const Session = await auth();
  if (!Session?.user.roles.includes(Role.ADMIN)) {
    throw new Error("Must Be Admin to complete this task");
  }
  if (!Session?.user.id) {
    throw new Error("Must Be a user to complete this task");
  }

  try {
    const result = await prisma.skills.findMany();
    return result;
  } catch (e) {
    console.error("Error getting skills:", e);
    throw e;
  }
}

export async function getSkillSubcategories() {
  try {
    const skillSubcategories = await prisma.skill_subcategories.findMany({
      include: {
        skills: true,
      },
    });
    return skillSubcategories;
  } catch (e) {
    console.error("Error fetching skill subcategories:", e);
    throw e;
  }
}

export async function adminCreateSkillSubcategory(
  subcategoryData: skill_subcategories,
) {
  const Session = await auth();
  if (!Session?.user.roles.includes(Role.ADMIN)) {
    throw new Error("Must Be Admin to complete this task");
  }
  if (!Session?.user.id) {
    throw new Error("Must Be a user to complete this task");
  }

  try {
    const result = await prisma.skill_subcategories.create({
      data: {
        skill_subcategory_id: uuidv4(),
        subcategory_name: subcategoryData.subcategory_name,
        subcategory_description: subcategoryData.subcategory_description,
      },
    });

    return result;
  } catch (e) {
    console.error("Error creating skill subcategory:", e);
    throw e;
  }
}

export async function generateAllSkillEmbeddings() {
  try {
    const skills = await prisma.skills.findMany({
      select: { skill_id: true, skill_name: true },
    });

    if (!skills || skills.length === 0) {
      return { updated: 0, total: 0 };
    }

    const result = await generateAndStoreEmbeddings(skills);

    return {
      processed: skills.length,
      updated: result.updated,
      error: result.error,
    };
  } catch (error) {
    console.error("Error during bulk embedding generation:", error);
    throw new Error(
      `Failed during bulk embedding: ${error instanceof Error ? error.message : String(error)}`,
    );
  }
}
