import { NextResponse } from "next/server";
import getPrismaClient from "@/app/lib/prismaClient.mjs";
import { PrismaClient } from "@prisma/client";
import {
  CompanyInfoSummaryDTO,
  ReadEmployerWorkDTO,
} from "@/data/dtos/EmployerProfileCreationDTOs";

const prisma: PrismaClient = getPrismaClient();

export async function GET(
  request: Request,
  props: { params: Promise<{ userId: string }> },
) {
  const params = await props.params;
  try {
    const userId = params.userId;

    if (!userId) {
      return NextResponse.json(
        { success: false, error: `A uuidv4 userId is required.` },
        { status: 400 },
      );
    }
    const empWorkInfo = await prisma.employers.findUnique({
      where: {
        user_id: userId,
      },
      select: {
        user_id: true,
        employer_id: true,
        job_title: true,
        linkedin_url: true,
        is_verified_employee: true,
        work_address_id: true,
        companies: {
          select: {
            company_id: true,
            company_name: true,
            company_logo_url: true,
            is_approved: true,
            company_addresses: {
              select: {
                company_address_id: true,
                locationData: {
                  select: {
                    city: true,
                    state: true,
                    zip: true,
                  },
                },
              },
            },
          },
        },
      },
    });

    if (!empWorkInfo) {
      return NextResponse.json({
        success: true,
        error: `No entry exists for userId: ${userId}`,
      });
    }
    let employerAddress = undefined;
    if (empWorkInfo?.work_address_id) {
      employerAddress = await prisma.company_addresses.findUnique({
        where: {
          company_address_id: empWorkInfo.work_address_id,
        },
        include: {
          locationData: true,
        },
      });
    }

    console.log(JSON.stringify(empWorkInfo, null, 2));
    const result: ReadEmployerWorkDTO & CompanyInfoSummaryDTO = {
      userId: empWorkInfo.user_id,
      employerId: empWorkInfo.employer_id,
      currentJobTitle: empWorkInfo.job_title,
      linkedInUrl: empWorkInfo.linkedin_url,
      companyId: empWorkInfo?.companies?.company_id,
      companyName: empWorkInfo?.companies?.company_name,
      isVerifiedCompany: empWorkInfo?.companies?.is_approved ?? false,
      isVerifiedEmployee: empWorkInfo.is_verified_employee,
      companyAddress: employerAddress
        ? {
            addressId: employerAddress.company_address_id,
            city: employerAddress.locationData.city,
            state: employerAddress.locationData.state,
            stateCode: employerAddress.locationData.stateCode,
            county: employerAddress.locationData.county,
            zip: employerAddress.locationData.zip,
          }
        : undefined,
    };
    return NextResponse.json({ success: true, result }, { status: 200 });
  } catch (e: any) {
    console.error("Error upserting job seeker introduction:", e.message);
    return NextResponse.json(
      {
        error: `Failed to upsert employer personal information.\n${e.message}`,
      },
      { status: 500 },
    );
  } finally {
    await prisma.$disconnect();
  }
}
