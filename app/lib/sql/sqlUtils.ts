import { readFile } from "fs/promises";
import { PrismaClient } from "@prisma/client";

const prisma = new PrismaClient();

export async function ExecuteSqlFile(path: string) {
  try {
    const sqlQuery = await readFile(path, "utf-8");
    const result = await prisma.$queryRawUnsafe(sqlQuery);
    return result;
  } catch (e) {
    console.error(e);
  }
}
