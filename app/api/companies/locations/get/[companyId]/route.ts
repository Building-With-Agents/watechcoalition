import { NextResponse } from "next/server";
import getPrismaClient from "@/app/lib/prismaClient.mjs";
import { PrismaClient } from "@prisma/client";
import { ReadAddressDTO } from "@/data/dtos/EmployerProfileCreationDTOs";

const prisma: PrismaClient = getPrismaClient();

export async function GET(
  request: Request,
  props: { params: Promise<{ companyId: string }> },
) {
  const params = await props.params;
  try {
    const companyId = params?.companyId;

    if (!companyId) {
      return NextResponse.json(
        { success: false, error: `A uuidv4 companyId is required.` },
        { status: 400 },
      );
    }

    const companyAddresses = await prisma.company_addresses.findMany({
      where: {
        company_id: companyId,
      },
      select: {
        company_address_id: true,
        locationData: {
          select: {
            zip: true,
            state: true,
            stateCode: true,
            county: true,
            city: true,
          },
        },
      },
    });
    if (!companyAddresses) {
      return NextResponse.json(
        {
          success: false,
          error: `There is no company with id ${companyId}`,
        },
        { status: 400 },
      );
    }

    const result: ReadAddressDTO[] = companyAddresses.map((address) => ({
      addressId: address.company_address_id,
      city: address.locationData.city,
      state: address.locationData.state,
      stateCode: address.locationData.stateCode,
      zip: address.locationData.zip,
      county: address.locationData.county,
    }));

    return NextResponse.json(result, { status: 200 });
  } catch (e: any) {
    console.error("Error reading company locations:", e.message);
    return NextResponse.json(
      { error: `Failed to read company locations.\n${e.message}` },
      { status: 500 },
    );
  } finally {
    await prisma.$disconnect();
  }
}
