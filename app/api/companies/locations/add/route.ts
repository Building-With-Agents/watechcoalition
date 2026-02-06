import { NextResponse } from "next/server";
import getPrismaClient from "@/app/lib/prismaClient.mjs";
import { PrismaClient } from "@prisma/client";
import {
  PostAddressDTO,
  ReadAddressDTO,
} from "@/data/dtos/EmployerProfileCreationDTOs";
import { v4 as uuidv4 } from "uuid";
import { auth } from "@/auth";

const prisma: PrismaClient = getPrismaClient();

export async function POST(request: Request) {
  try {
    // Get essentials from session, not the request
    const session = await auth();
    const companyId: string | null | undefined = session?.user.companyId;

    const body: PostAddressDTO & { companyId: string } = await request.json();
    const { zip } = body;

    if (!companyId || !zip) {
      return NextResponse.json(
        {
          success: false,
          error: `A uuidv4 companyId and zip code is required.`,
        },
        { status: 400 },
      );
    }
    if (!session?.user.employeeIsApproved) {
      return NextResponse.json(
        {
          success: false,
          error: `Employee needs to be approved to edit this company.`,
        },
        { status: 401 },
      );
    }

    const newLocation = await prisma.company_addresses.upsert({
      where: {
        company_id_zip: {
          // compound unique field for company_id and zip
          company_id: companyId,
          zip: zip,
        },
      },
      update: {
        // do nothing just offering a smoother UX
      },
      create: {
        company_address_id: uuidv4(),
        company_id: companyId,
        zip: zip,
      },
      select: {
        company_address_id: true,
        locationData: {
          select: {
            zip: true,
            city: true,
            state: true,
            stateCode: true,
            county: true,
          },
        },
      },
    });

    const result: ReadAddressDTO = {
      addressId: newLocation.company_address_id,
      city: newLocation.locationData.city,
      state: newLocation.locationData.state,
      stateCode: newLocation.locationData.stateCode,
      zip: newLocation.locationData.zip,
      county: newLocation.locationData.county,
    };

    return NextResponse.json({ success: true, result }, { status: 200 });
  } catch (e: any) {
    console.error("Error creating company location:", e.message);
    return NextResponse.json(
      { error: `Failed to create company location.\n${e.message}` },
      { status: 500 },
    );
  }
}
