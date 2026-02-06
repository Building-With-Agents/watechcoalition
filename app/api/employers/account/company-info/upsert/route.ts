import { NextResponse } from "next/server";
import getPrismaClient from "@/app/lib/prismaClient.mjs";
import { PrismaClient } from "@prisma/client";
import { auth } from "@/auth";
import {
  PostAddressDTO,
  PostCompanyInfoDTO,
  ReadAddressDTO,
  ReadCompanyInfoDTO,
} from "@/data/dtos/EmployerProfileCreationDTOs";
import { v4 as uuidv4 } from "uuid";

const prisma: PrismaClient = getPrismaClient();

export async function POST(request: Request) {
  try {
    // Get essentials from session, not the request
    const session = await auth();
    const userId: string = session?.user.id!;
    const employerId: string = session?.user.employerId!;

    const body: PostCompanyInfoDTO = await request.json();
    const {
      companyId,
      industrySectorId,
      companyName,
      companyAddresses,
      logoUrl,
      aboutUs,
      companyEmail,
      yearFounded,
      websiteUrl,
      videoUrl,
      companyPhone,
      mission,
      vision,
      companySize,
      estimatedAnnualHires,
    } = body;

    await prisma.employers.upsert({
      where: {
        user_id: userId,
      },
      update: {
        users: {
          connect: {
            id: userId,
          },
        },
      },
      create: {
        employer_id: employerId,
        users: {
          connect: {
            id: userId,
          },
        },
      },
    });

    // const newCompanyId: string = session?.user.companyId!;
    if (!companyId) {
      console.error("Company Id needs created and passed to this route first.");
      return NextResponse.json(
        {
          success: false,
          error:
            "Company Id needs to be created and passed to this route first.",
        },
        { status: 400 }, // Bad Request
      );
    }

    const upsertedCompany = await prisma.companies.upsert({
      where: {
        company_id: companyId,
      },
      update: {
        company_name: companyName,
        company_logo_url: logoUrl,
        about_us: aboutUs || undefined,
        company_email: companyEmail,
        year_founded: yearFounded ? parseInt(yearFounded, 10) : undefined,
        company_website_url: websiteUrl,
        company_video_url: videoUrl,
        company_phone: companyPhone,
        company_mission: mission,
        company_vision: vision,
        size: companySize,
        estimated_annual_hires: parseInt(estimatedAnnualHires, 10),
        employers: {
          connect: {
            user_id: userId,
          },
        },
        // Only connect if industrySectorId exists
        ...(industrySectorId && {
          industry_sectors: {
            connect: {
              industry_sector_id: industrySectorId,
            },
          },
        }),
      },
      create: {
        createdByUser: {
          connect: {
            id: userId,
          },
        },
        company_id: companyId,
        company_name: companyName,
        company_logo_url: logoUrl,
        about_us: aboutUs || "",
        company_email: companyEmail,
        year_founded: parseInt(yearFounded, 10),
        company_website_url: websiteUrl,
        company_video_url: videoUrl,
        company_phone: companyPhone,
        company_mission: mission,
        company_vision: vision,
        size: companySize,
        estimated_annual_hires: parseInt(estimatedAnnualHires, 10),
        is_approved: false,
        employers: {
          connect: {
            user_id: userId,
          },
        },
        // Only connect if industrySectorId exists
        ...(industrySectorId && {
          industry_sectors: {
            connect: {
              industry_sector_id: industrySectorId,
            },
          },
        }),
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
      },
    });

    await prisma.employers.update({
      where: {
        employer_id: session?.user.employerId!,
      },
      data: {
        is_verified_employee: true,
      },
    });

    if (!upsertedCompany) {
      return NextResponse.json({
        success: false,
        error: `No company exists for companyId: ${companyId}`,
      });
    }

    const upsertPromises = companyAddresses?.map((address: PostAddressDTO) => {
      return prisma.company_addresses.upsert({
        where: {
          company_id_zip: {
            company_id: companyId,
            zip: address.zip,
          },
        },
        update: {
          zip: address.zip,
        },
        create: {
          company_address_id: uuidv4(),
          zip: address.zip,
          company_id: upsertedCompany.company_id,
        },
        select: {
          company_address_id: true,
          locationData: {
            select: {
              city: true,
              state: true,
              zip: true,
              county: true,
            },
          },
        },
      });
    });

    if (Array.isArray(upsertPromises) && upsertPromises.length > 0) {
      await Promise.all(upsertPromises);
    }

    const updatedAddresses = await prisma.company_addresses.findMany({
      where: {
        company_id: companyId,
      },
      select: {
        company_address_id: true,
        locationData: {
          select: {
            city: true,
            state: true,
            stateCode: true,
            zip: true,
            county: true,
          },
        },
      },
    });

    const result: ReadCompanyInfoDTO = {
      companyId: upsertedCompany.company_id,
      industrySectorId: upsertedCompany.industry_sector_id,
      industrySectorTitle: upsertedCompany?.industry_sectors?.sector_title,
      companyName: upsertedCompany.company_name,
      companyAddresses:
        updatedAddresses?.map((address) => ({
          addressId: address.company_address_id,
          state: address.locationData.state,
          stateCode: address.locationData.stateCode,
          city: address.locationData.city,
          zip: address.locationData.zip,
          county: address.locationData.county,
        })) || ([] as ReadAddressDTO[]),
      logoUrl: upsertedCompany.company_logo_url,
      aboutUs: upsertedCompany.about_us,
      companyEmail: upsertedCompany.company_email,
      yearFounded: upsertedCompany?.year_founded?.toString(),
      websiteUrl: upsertedCompany.company_website_url,
      videoUrl: upsertedCompany.company_video_url,
      phoneCountryCode: null,
      companyPhone: upsertedCompany.company_phone,
      mission: upsertedCompany.company_mission,
      vision: upsertedCompany.company_vision,
      companySize: upsertedCompany.size,
      estimatedAnnualHires: upsertedCompany?.estimated_annual_hires?.toString(),
      isApproved: upsertedCompany.is_approved,
      createdBy: upsertedCompany.createdBy,
    };

    // Fixme: Update session with new employerId and companyId. Session returning null.
    // const session = await auth(); // Get the session using the auth function
    // if (session) {
    //   // Update session properties
    //   session.user.employerId = employerId || newEmployerId;
    //   session.user.companyId = companyId || newCompanyId;
    // }

    return NextResponse.json({ success: true, result }, { status: 200 });
  } catch (e: any) {
    console.error("Error upserting company information:", e.message);
    return NextResponse.json(
      { error: `Failed to upsert company information.\n${e.message}` },
      { status: 500 },
    );
  }
}
