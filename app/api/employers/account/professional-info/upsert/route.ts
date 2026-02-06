import { NextResponse } from "next/server";
import getPrismaClient from "@/app/lib/prismaClient.mjs";
import { PrismaClient } from "@prisma/client";
import {
  CompanyInfoSummaryDTO,
  PostEmployerWorkDTO,
  ReadAddressDTO,
  ReadEmployerWorkDTO,
} from "@/data/dtos/EmployerProfileCreationDTOs";
import { devLog } from "@/app/lib/utils";
import { auth } from "@/auth";

const prisma: PrismaClient = getPrismaClient();

export async function POST(request: Request) {
  try {
    // Get essentials from session, not the request
    const session = await auth();
    const userId: string = session?.user.id!;
    const employerId: string = session?.user.employerId!;

    const body: PostEmployerWorkDTO = await request.json();
    const { currentJobTitle, linkedInUrl, workAddressId } = body;
    const addressId = !workAddressId ? undefined : workAddressId;
    const upsertedEmployer = await prisma.employers.upsert({
      where: {
        user_id: userId,
      },
      update: {
        job_title: currentJobTitle,
        linkedin_url: linkedInUrl,
        work_address_id: addressId,
      },
      create: {
        employer_id: employerId,
        user_id: userId,
        job_title: currentJobTitle,
        work_address_id: addressId,
        linkedin_url: linkedInUrl,
        is_verified_employee: false,
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
                    stateCode: true,
                    county: true,
                    zip: true,
                  },
                },
              },
            },
          },
        },
      },
    });
    devLog(upsertedEmployer);
    const companyAddressExists =
      !!upsertedEmployer?.companies?.company_addresses?.[0];
    const result: ReadEmployerWorkDTO & CompanyInfoSummaryDTO = {
      userId: upsertedEmployer.user_id,
      employerId: upsertedEmployer.employer_id,
      currentJobTitle: upsertedEmployer.job_title,
      linkedInUrl: upsertedEmployer.linkedin_url,
      companyId: upsertedEmployer?.companies?.company_id,
      companyName: upsertedEmployer?.companies?.company_name,
      isVerifiedCompany: upsertedEmployer.companies?.is_approved ?? false,
      isVerifiedEmployee: upsertedEmployer.is_verified_employee,
      companyAddress: companyAddressExists
        ? ({
            addressId:
              upsertedEmployer?.companies?.company_addresses[0]
                .company_address_id,
            city: upsertedEmployer?.companies?.company_addresses[0].locationData
              .city,
            state:
              upsertedEmployer?.companies?.company_addresses[0].locationData
                .state,
            stateCode:
              upsertedEmployer.companies?.company_addresses[0].locationData
                .stateCode,
            zip: upsertedEmployer?.companies?.company_addresses[0].locationData
              .zip,
            county:
              upsertedEmployer.companies?.company_addresses[0].locationData
                .county,
          } as ReadAddressDTO)
        : undefined,
    };
    return NextResponse.json({ success: true, result }, { status: 200 });
  } catch (e: any) {
    console.error("Error upserting job seeker intro:", e.message);
    return NextResponse.json(
      {
        error: `Failed to upsert employer profession information.\n${e.message}`,
      },
      { status: 500 },
    );
  }
}
