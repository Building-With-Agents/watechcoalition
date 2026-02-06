import { NextResponse } from "next/server";
import getPrismaClient from "@/app/lib/prismaClient.mjs";
import { PrismaClient } from "@prisma/client";
import {
  ReadAddressDTO,
  ReadCompanyInfoDTO,
} from "@/data/dtos/EmployerProfileCreationDTOs";
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
        industry_sector_id: true,
        industry_sectors: {
          select: {
            sector_title: true,
          },
        },
        company_name: true,
        company_logo_url: true,
        about_us: true,
        company_email: true,
        year_founded: true,
        company_website_url: true,
        company_video_url: true,
        company_phone: true,
        company_mission: true,
        company_vision: true,
        size: true,
        estimated_annual_hires: true,
        is_approved: true,
        createdBy: true,
        company_addresses: {
          select: {
            locationData: {
              select: {
                state: true,
                stateCode: true,
                city: true,
                zip: true,
                county: true,
              },
            },
          },
        },
      },
    });

    if (!companyInfo) {
      return NextResponse.json({
        success: true,
        error: `No entry exists for companyId: ${companyId}`,
      });
    }

    const updatedAddresses = await prisma.company_addresses.findMany({
      where: {
        company_id: companyId,
      },
      select: {
        company_address_id: true,
        locationData: {
          select: {
            state: true,
            stateCode: true,
            county: true,
            city: true,
            zip: true,
          },
        },
      },
    });

    const result: ReadCompanyInfoDTO = {
      companyId: companyInfo.company_id,
      industrySectorId: companyInfo.industry_sector_id,
      industrySectorTitle: companyInfo?.industry_sectors?.sector_title,
      companyName: companyInfo.company_name,
      logoUrl: companyInfo.company_logo_url,
      aboutUs: companyInfo.about_us,
      companyEmail: companyInfo.company_email,
      yearFounded: companyInfo?.year_founded?.toString(),
      websiteUrl: companyInfo.company_website_url,
      videoUrl: companyInfo.company_video_url,
      phoneCountryCode: null,
      companyPhone: companyInfo.company_phone,
      mission: companyInfo.company_mission,
      vision: companyInfo.company_vision,
      companySize: companyInfo.size,
      estimatedAnnualHires: companyInfo?.estimated_annual_hires?.toString(),
      isApproved: companyInfo.is_approved,
      createdBy: companyInfo.createdBy,
      companyAddresses:
        updatedAddresses?.map((address) => ({
          addressId: address.company_address_id,
          state: address.locationData.state,
          stateCode: address.locationData.stateCode,
          city: address.locationData.city,
          zip: address.locationData.zip,
          county: address.locationData.county,
        })) || ([] as ReadAddressDTO[]),
    };
    console.log("server-result", result);
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
