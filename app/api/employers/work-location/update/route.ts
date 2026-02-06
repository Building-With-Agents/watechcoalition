import { NextResponse } from "next/server";
import getPrismaClient from "@/app/lib/prismaClient.mjs";
import { PrismaClient } from "@prisma/client";
import {
  CompanyInfoSummaryDTO,
  ReadAddressDTO,
  ReadEmployerWorkDTO,
} from "@/data/dtos/EmployerProfileCreationDTOs";
import { auth } from "@/auth";

const prisma: PrismaClient = getPrismaClient();

export async function PATCH(request: Request) {
  try {
    // Get essentials from session, not the request
    const session = await auth();
    const userId: string = session?.user.id!;

    const body = await request.json();
    const { companyAddressId } = body;

    if (!userId) {
      return NextResponse.json(
        { success: false, error: `A uuidv4 userId is required.` },
        { status: 400 },
      );
    }
    const empWorkInfo = await prisma.employers.update({
      where: {
        user_id: userId,
      },
      data: {
        work_address_id: companyAddressId,
      },
      select: {
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
            company_addresses: {
              select: {
                company_address_id: true,
                locationData: {
                  select: {
                    city: true,
                    state: true,
                    stateCode: true,
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
      employerId: empWorkInfo.employer_id,
      currentJobTitle: empWorkInfo.job_title,
      linkedInUrl: empWorkInfo.linkedin_url,
      companyId: empWorkInfo?.companies?.company_id,
      companyName: empWorkInfo?.companies?.company_name,
      isVerifiedEmployee: empWorkInfo.is_verified_employee,
      companyAddress: employerAddress
        ? ({
            addressId: employerAddress?.company_address_id,
            city: employerAddress?.locationData.city,
            state: employerAddress?.locationData.state,
            stateCode: employerAddress?.locationData.stateCode,
            county: employerAddress?.locationData.county,
            zip: employerAddress?.locationData.zip,
          } as ReadAddressDTO)
        : undefined,
    };
    return NextResponse.json({ success: true, result }, { status: 200 });
  } catch (e: any) {
    console.error("Error updating employer's work location:", e.message);
    return NextResponse.json(
      { error: `Failed to update employer's work location.\n${e.message}` },
      { status: 500 },
    );
  }
}
