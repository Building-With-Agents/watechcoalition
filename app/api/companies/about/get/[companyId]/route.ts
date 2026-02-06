import { NextResponse } from "next/server";
import getPrismaClient from "@/app/lib/prismaClient.mjs";
import { PrismaClient } from "@prisma/client";
import { ReadEmployerAboutDTO } from "@/data/dtos/EmployerProfileCreationDTOs";
const prisma: PrismaClient = getPrismaClient();

export async function GET(
  request: Request,
  props: { params: Promise<{ companyId: string }> },
) {
  const params = await props.params;
  try {
    const companyId = params.companyId;

    if (!companyId) {
      return NextResponse.json(
        { success: false, error: `A uuidv4 companyId is required.` },
        { status: 400 },
      );
    }
    const companyInfo = await prisma.companies.findUnique({
      where: {
        company_id: companyId,
      },
      select: {
        company_id: true,
        about_us: true,
      },
    });

    if (!companyInfo) {
      return NextResponse.json({
        success: true,
        error: `No entry exists for companyId: ${companyId}`,
      });
    }

    // const updatedAddresses = await prisma.company_addresses.findMany( {
    //     where: {
    //         company_id: companyId
    //     },
    //     select: {
    //         company_address_id: true,
    //         locationData: {
    //             select: {
    //                 state: true,
    //                 stateCode: true,
    //                 county: true,
    //                 city: true,
    //                 zip: true,
    //             }
    //         }
    //     }
    // })

    const result: ReadEmployerAboutDTO = {
      companyId: companyInfo.company_id,
      aboutUs: companyInfo.about_us,
      // isApproved: companyInfo.is_approved,
      // companyAddresses: updatedAddresses.map(address => ({
      //     addressId: address.company_address_id,
      //     state: address.locationData.state,
      //     city: address.locationData.city,
      //     zipCode: address.locationData.zip,
      //     county: address.locationData.county
      // }))
    };
    return NextResponse.json({ success: true, result }, { status: 200 });
  } catch (e: any) {
    console.error("Error retrieving company record.", e.message);
    return NextResponse.json(
      { error: `Error retrieving company record.\n${e.message}` },
      { status: 500 },
    );
  } finally {
    await prisma.$disconnect();
  }
}
