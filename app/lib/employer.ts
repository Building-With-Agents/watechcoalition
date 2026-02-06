import { Prisma, PrismaClient } from "@prisma/client";
import getPrismaClient from "@/app/lib/prismaClient.mjs";
import { Role } from "@/data/dtos/UserInfoDTO";
import { auth } from "@/auth";
import { v4 as uuidv4 } from "uuid";
import { CompanyEmployerCreationDTO } from "@/data/dtos/CompanyEmployerCreateionDTO";

const prisma: PrismaClient = getPrismaClient();

/**
 * Create an employer (for an existing user) and associated data from the database.
 *
 * @param {string} userId - The ID of the user to become a jobseeker.
 * @returns {Promise<employers>}
 * @throws {Error} If user creation fails
 */
export async function createEmployer(
  userId: string,
): Promise<Prisma.employersGetPayload<object>> {
  try {
    // Use a transaction to ensure both operations succeed or fail together
    const result = await prisma.$transaction(async (prisma) => {
      await prisma.user.update({
        where: { id: userId },
        data: {
          role: Role.EMPLOYER,
          has_agreed_terms: true,
          updatedAt: new Date(),
        },
      });

      const employer = await prisma.employers.create({
        data: {
          employer_id: uuidv4(),
          user_id: userId,
        },
      });

      return employer;
    });

    return result;
  } catch (error) {
    if (error instanceof Prisma.PrismaClientKnownRequestError) {
      // Handle known Prisma errors (e.g., unique constraint violations)
      if (error.code === "P2002") {
        throw new Error("The Employer data/role already exists for this user");
      }
    }
    throw error;
  }
}

/**
 * Deletes an employer from the database based on the provided user ID.
 * This function starts a transaction to ensure data consistency and integrity.
 * It first deletes the employer record directly using the user ID.
 * Then it retrieves the user's roles, removes the EMPLOYER role if present,
 * and updates the user's roles accordingly. If the user has no roles left after removing EMPLOYER,
 * the user record is deleted as well.
 * If an error occurs during the process, it is logged and rethrown.
 * Finally, it disconnects from the Prisma client.
 * @param {string} userId - The unique identifier of the user whose employer record should be deleted.
 * @returns {Promise<void>} - A Promise that resolves when the employer is successfully deleted.
 */
export const deleteEmployer = async (userId: string) => {
  try {
    // Start a transaction
    await prisma.$transaction(async (prisma) => {
      // Delete the employer record directly using user_id
      await prisma.employers.delete({ where: { user_id: userId } });

      // Fetch the user's roles
      const user = await prisma.user.findUnique({
        where: { id: userId },
        select: {
          role: true, // Returns string -> comma-separated list of roles
        },
      });

      if (!user) {
        throw new Error("User not found");
      }

      // Split the roles into an array
      const userRolesArray: Role[] = user.role
        .split(",")
        .map((role) => role.trim() as Role);

      // Remove the EMPLOYER role
      const filteredRolesArray = userRolesArray.filter(
        (role) => role !== Role.EMPLOYER,
      );

      if (filteredRolesArray.length === 0) {
        // Delete the user if no roles are left
        await prisma.user.delete({ where: { id: userId } });
      } else {
        // Update the user's roles
        await prisma.user.update({
          where: { id: userId },
          data: { role: filteredRolesArray.join(",") },
        });
      }
    });
    return true;
  } catch (error: any) {
    console.error("Error deleting employer:", error);
    return false;
  } finally {
    await prisma.$disconnect();
  }
};

/**
 * Deletes the employer associated with the current user session.
 *
 * This function first authenticates the user session to obtain the user ID.
 * If the user ID is not found in the session, an error is logged and an exception is thrown.
 * Then it attempts to delete the employer with the obtained user ID.
 * If an error occurs during the deletion process, the error is logged and rethrown.
 *
 * @returns {Promise<void>} A promise that resolves when the employer is successfully deleted.
 */
export const deleteEmployerWithSession = async (): Promise<void> => {
  const session = await auth();
  const userId = session?.user.id;

  if (!userId) {
    console.error("No user id found in session. Could not delete employer");
    throw Error("No userId found in session. Could not delete employer");
  }
  try {
    await deleteEmployer(userId);
  } catch (error: any) {
    console.error("Error deleting employer with session:", error);
    throw error;
  }
};

export async function createCompany(companyData: CompanyEmployerCreationDTO) {
  const session = await auth();
  if (!session?.user.roles.includes(Role.EMPLOYER)) {
    throw new Error("Must Be Employer to complete this task");
  }
  if (!session?.user.id) {
    throw new Error("Must Be a user");
  }
  try {
    const result = await prisma.companies.create({
      data: {
        company_name: companyData.companyName,
        company_email: session.user.email ?? "",
        company_id: uuidv4(),
        about_us: "",
        year_founded: companyData.yearFounded ?? 2024,
        createdBy: session.user.id,
        company_mission: "",
      },
    });
    return result;
  } catch (e) {
    console.error(e);
  }
}

export async function updateCompany(
  companyData: Partial<Prisma.companiesUncheckedCreateInput>,
) {
  try {
    if (!companyData.company_id) {
      throw new Error("company_id is required to update a company");
    }

    // Remove company_id from data to avoid updating the primary key
    const { company_id, ...data } = companyData;

    console.log("Prisma update input:", { where: { company_id }, data });

    const result = await prisma.companies.update({
      where: { company_id },
      data,
    });

    return result;
  } catch (error) {
    console.error("Error updating company:", error);
    throw new Error("Failed to update company");
  }
}

export async function getAllCompanies() {
  const res = await prisma.companies.findMany();
  return res;
}

export async function getAllEmployers() {
  return await prisma.employers.findMany({
    include: {
      users: true,
    },
  });
}

export async function getAllTechAreas() {
  const res = await prisma.technology_areas.findMany();
  return res;
}

export async function getAllIndustrySectors() {
  const res = await prisma.industry_sectors.findMany();
  return res;
}

export type ReadEmployerRecordDTO = {
  company_id: string | null;
  employer_id: string;
  user_id: string;
  work_address_id: string | null;
  job_title: string | null;
  linkedin_url: string | null;
  is_verified_employee: boolean;
} | null;

export async function getEmployer(
  userId: string,
): Promise<ReadEmployerRecordDTO> {
  const res: ReadEmployerRecordDTO = await prisma.employers.findUnique({
    where: {
      user_id: userId,
    },
  });
  return res;
}

export async function getEmployerWithSession() {
  const session = await auth();
  const userId = session?.user.id;
  if (!userId) {
    return;
  }
  const res: ReadEmployerRecordDTO = await getEmployer(userId);
  return res;
}

/**
 * Stages of a company’s journey through the Employer Engagement Pipeline.
 *
 * @remarks
 * - **LEAD**: Newly identified cold lead (e.g. from JSearch API); goal is to gather contact info and convert to ENGAGED.
 * - **ENGAGED**: Actively in communication with the Employer Engagement team.
 * - **OPPORTUNITY**: Company has agreed to host one or more activities (see {@link OpportunityType}).
 * - **HIRED**: Company has successfully hired talent from the Coalition pool.
 */
export enum EngagementType {
  LEAD = "Lead",
  ENGAGED = "Engaged",
  OPPORTUNITY = "Opportunity",
  HIRED = "Hired",
}

/**
 * Types of engagement activities a company can offer to jobseekers or students.
 *
 * @remarks
 * - **JOB_POSTS**: Posting jobs to our board.
 * - **MENTORING**: Hosting mock interviews or mentoring sessions.
 * - **INDUSTRY_COUNCIL**: Advising on curriculum modernization.
 * - **AMA_SPEAKER**: Presenting in an “Ask Me Anything” session.
 */
export enum OpportunityType {
  JOB_POSTS = "Job Posts",
  MENTORING = "Mentoring",
  INDUSTRY_COUNCIL = "Industry Council",
  AMA_SPEAKER = "AMA Speaker",
}
