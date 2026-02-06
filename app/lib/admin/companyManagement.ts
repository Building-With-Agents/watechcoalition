import { auth } from "@/auth";
import { CompanyAdminCreationDTO } from "@/data/dtos/CompanyAdminCreationDTO";
import { Role } from "@/data/dtos/UserInfoDTO";
import { PrismaClient } from "@prisma/client";
import getPrismaClient from "../prismaClient.mjs";
import { validate as isUuid } from "uuid";
const prisma: PrismaClient = getPrismaClient();

export async function adminCreateCompany(companyData: CompanyAdminCreationDTO) {
  const Session = await auth();
  if (
    !Session?.user.roles.includes(Role.ADMIN) &&
    !Session?.user.roles.includes(Role.CASE_MANAGER)
  ) {
    throw new Error("Must Be Admin to complete this task");
  }
  if (!Session?.user.id) {
    throw new Error("Must Be a user to complete this task");
  }
  try {
    const result = await prisma.companies.create({
      data: {
        company_id: companyData.companyId,
        company_name: companyData.companyName,
        company_email: companyData.companyEmail,
        about_us: companyData.aboutUs,
        size: companyData.size,
        year_founded: companyData.yearFounded,
        createdBy: Session.user.id,
        company_mission: companyData.companyMission,
        estimated_annual_hires: companyData.estimatedAnnualHires,
        industry_sector_id: companyData.industrySectorId,
        is_approved: true, //since this is created by an employer currently
        company_website_url: companyData.companyWebsiteUrl,
        company_phone: companyData.companyPhone,
        company_vision: companyData.companyVision,
        company_logo_url: companyData.logoUrl,
      },
    });
    return result;
  } catch (e) {
    console.error(e);
  }
}
export async function adminDeleteCompany(companyId: string) {
  const session = await auth();

  if (!session?.user) {
    throw new Error("User not authenticated.");
  }

  if (!session.user.roles.includes(Role.ADMIN)) {
    throw new Error("User does not have admin privileges.");
  }

  if (!companyId || !isUuid(companyId)) {
    throw new Error("Invalid company ID.");
  }

  try {
    console.debug("Deleting company with ID:", companyId);

    // Perform delete
    //Will currently fail everytime since cascading delete is not set up
    const result = await prisma.companies.delete({
      where: {
        company_id: companyId,
      },
    });

    return result;
  } catch (error: any) {
    console.error("Error in DELETE handler:", error);
    throw new Error("Failed to delete company. Please try again.");
  }
}

export async function adminUpdateCompanyApproval(
  companyId: string,
  isApproved: boolean,
) {
  try {
    const Session = await auth();
    if (!Session?.user.roles.includes(Role.ADMIN)) {
      throw new Error("Must Be Admin to complete this task");
    }
    const res = await prisma.companies.update({
      where: {
        company_id: companyId,
      },
      data: {
        is_approved: isApproved,
      },
    });
    return res;
  } catch (error) {
    console.error(error);
  }
}

export async function adminEmployerApproval(
  employerId: string,
  isVerifed: boolean,
) {
  try {
    const Session = await auth();
    if (!Session?.user.roles.includes(Role.ADMIN)) {
      throw new Error("Must Be Admin to complete this task");
    }
    const res = await prisma.employers.update({
      where: {
        employer_id: employerId,
      },
      data: {
        is_verified_employee: isVerifed,
      },
    });
    return res;
  } catch (error) {
    console.error(error);
  }
}

export async function getAllCompaniesWithAllEmployers() {
  try {
    const res = await prisma.companies.findMany({
      include: {
        employers: {
          include: {
            users: true,
          },
        },
      },
    });
    return res;
  } catch (error) {
    console.error(error);
    return [];
  }
}
