import { NextResponse } from "next/server";
import { PrismaClient } from "@prisma/client";
import { jobSeekerCardViewSelect } from "@/app/lib/prisma";
import { educationRank } from "@/data/dtos/JobSeekerProfileCreationDTOs";
import { HighestCompletedEducationLevel } from "@/data/dtos/JobSeekerProfileCreationDTOs";
import { devLog } from "@/app/lib/utils";

const prisma = new PrismaClient();

export async function POST(request: Request) {
  const {
    skills = [],
    industrySector = [],
    educationLevel = undefined,
    trainingProvider = undefined,
    yearsWorkExpMin = 0,
    yearsWorkExpMax = undefined,
    zipCode = undefined,
    sortBy = "yearsExp",
    hasIntroduction = false,
    hasAnySkills = false,
    hasResume = false,
    maxResults = 50,
    page = 1,
  } = await request.json();

  const normalizedSkills: string[] = skills.filter(
    (skill: string) => skill && skill.trim() !== "",
  );

  const andConditions: any[] = [];

  if (hasIntroduction) {
    andConditions.push({ intro_headline: { not: null } });
    andConditions.push({ NOT: { intro_headline: "" } });
  }
  if (hasAnySkills) {
    andConditions.push({
      jobseeker_has_skills: { some: {} },
    });
  }
  if (hasResume) {
    andConditions.push({
      hasResume: true,
    });
  }

  if (normalizedSkills.length > 0) {
    // Here we are checking if the skills are highlighted in projects or listed as their top five
    // Discuss with team how we want this to be implemented.
    // Q: Do we want to look in both places as project skills may not be that great?
    // Or should we allow the employer to choose 1) Top Skills 2) Any Skill 3) Or All?
    const orConditions = [
      {
        jobseeker_has_skills: {
          some: {
            skills: {
              skill_name: {
                in: normalizedSkills,
              },
            },
          },
        },
      },
      // {
      //   project_experiences: {
      //     some: {
      //       project_has_skills: {
      //         some: {
      //           skills: {
      //             skill_name: {
      //               in: normalizedSkills,
      //             },
      //           },
      //         },
      //       },
      //     },
      //   },
      // },
    ];
    // fixme: let's change this to an { OR: orConditions } when we have a healthy amount of jobseeker users.
    andConditions.push({ OR: orConditions });
  }

  // Years Work Experience Filtering with both lower and upper bounds
  if (yearsWorkExpMin !== undefined && yearsWorkExpMax !== undefined) {
    andConditions.push({
      years_work_exp: {
        gte: yearsWorkExpMin, // Greater than or equal to the minimum
        lte: yearsWorkExpMax, // Less than or equal to the maximum
      },
    });
  } else if (yearsWorkExpMin !== undefined) {
    // If only minimum is specified
    andConditions.push({
      years_work_exp: {
        gte: yearsWorkExpMin,
      },
    });
  } else if (yearsWorkExpMax !== undefined) {
    // If only maximum is specified
    andConditions.push({
      years_work_exp: {
        lte: yearsWorkExpMax,
      },
    });
  }

  // Industry Sector Filtering
  if (industrySector.length > 0) {
    andConditions.push({
      work_experiences: {
        some: {
          industrySector: {
            sector_title: { in: industrySector },
          },
        },
      },
    });
  }

  // Training Provider Filtering
  if (trainingProvider) {
    andConditions.push({
      jobseeker_education: {
        some: {
          eduProviders: {
            name: trainingProvider,
          },
        },
      },
    });
  }

  // Education Level Filtering
  if (educationLevel) {
    const minRank: number =
      educationRank[educationLevel as HighestCompletedEducationLevel];
    andConditions.push({
      highest_level_of_study_completed: {
        in: Object.keys(educationRank).filter(
          (level) =>
            educationRank[level as HighestCompletedEducationLevel] >= minRank,
        ),
      },
    });
  }

  // Zip Code Filtering
  if (zipCode) {
    andConditions.push({
      users: {
        some: {
          zip: {
            startsWith: zipCode,
          },
        },
      },
    });
  }

  // have to sort by eduLevel after we get the result because Prisma does not support custom comparators. see Line 140.
  const orderBy =
    sortBy === "newest"
      ? [{ createdAt: "desc" as const }]
      : sortBy === "yearsExp"
        ? [{ years_work_exp: "desc" as const }]
        : undefined;

  // Determine the number of results to skip based on the page number and maxResults
  const skip = (page - 1) * maxResults;

  const [filteredJobSeekers, totalCount] = await prisma.$transaction([
    prisma.jobseekers.findMany({
      where: andConditions.length > 0 ? { AND: andConditions } : undefined,
      select: jobSeekerCardViewSelect, // for testing queries in Postman use jobseekerQueryTestSelect //website use: jobSeekerCardViewSelect
      take: maxResults,
      skip: skip,
      orderBy: orderBy,
    }),
    prisma.jobseekers.count({
      where: andConditions.length > 0 ? { AND: andConditions } : undefined,
    }),
  ]);

  // Sort by education level if needed
  if (sortBy === "highestDegree") {
    filteredJobSeekers.sort(
      (a, b) =>
        educationRank[
          b.highest_level_of_study_completed as HighestCompletedEducationLevel
        ] -
        educationRank[
          a.highest_level_of_study_completed as HighestCompletedEducationLevel
        ],
    );
  }
  devLog(filteredJobSeekers[0]);

  return NextResponse.json({
    filteredJobSeekers,
    totalCount,
  });
}
