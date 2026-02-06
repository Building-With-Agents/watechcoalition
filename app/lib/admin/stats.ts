/**
 * This file is used for stats reporting that may be needed for grants, site metrics, etc
 */

import getPrismaClient from "@/app/lib/prismaClient.mjs";
import { PrismaClient } from "@prisma/client";
const prisma: PrismaClient = getPrismaClient();
export async function getNumOfJobseekers() {
  return await prisma.jobseekers.count();
}
export async function getNumOfIndividualEmployers() {
  return await prisma.employers.count();
}

type GenderBreakdown = {
  [gender: string]: number;
};

export async function getGenderBreakDownOfJobseekers(): Promise<GenderBreakdown> {
  const genderBreakdown = await prisma.jobseekers_private_data.groupBy({
    by: ["gender"],
    _count: {
      gender: true,
    },
  });

  const formattedBreakdown = genderBreakdown.reduce<GenderBreakdown>(
    (acc, item) => {
      acc[item.gender] = item._count.gender;
      return acc;
    },
    {},
  );

  return formattedBreakdown;
}

export const getUsersCreatedByQuarter = async () => {
  try {
    // Fetch all users with their creation date
    const users = await prisma.user.findMany({
      select: {
        createdAt: true,
      },
    });

    // Group users by year and quarter
    const groupedByQuarter = users.reduce(
      (acc, user) => {
        const year = user.createdAt.getFullYear();
        const quarter = Math.floor(user.createdAt.getMonth() / 3) + 1; // Calculate quarter (1-4)

        const key = `${year}-Q${quarter}`;
        if (!acc[key]) {
          acc[key] = 0;
        }
        acc[key] += 1;

        return acc;
      },
      {} as Record<string, number>,
    );

    // Convert the grouped data to an array for easier handling
    const result = Object.entries(groupedByQuarter).map(([key, count]) => {
      const [year, quarter] = key.split("-Q");
      return {
        year: parseInt(year, 10),
        quarter: parseInt(quarter, 10),
        userCount: count,
      };
    });

    // Sort the result by year and quarter
    result.sort((a, b) => a.year - b.year || a.quarter - b.quarter);

    return result;
  } catch (error) {
    console.error("Error fetching user creation data by quarter:", error);
    throw error;
  }
};
