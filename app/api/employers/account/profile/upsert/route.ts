import { NextResponse } from "next/server";
import getPrismaClient from "@/app/lib/prismaClient.mjs";
import { PrismaClient } from "@prisma/client";
import { auth } from "@/auth";
import { v4 as uuidv4 } from "uuid";
import { Role } from "@/data/dtos/UserInfoDTO";
import { PostEmployerProfileDTO } from "@/data/dtos/EmployerProfileCreationDTOs";

const prisma: PrismaClient = getPrismaClient();

export async function PATCH(request: Request) {
  try {
    const session = await auth();
    const body: PostEmployerProfileDTO = await request.json();
    const {
      userId,
      firstName,
      lastName,
      currentJobTitle,
      linkedInUrl,
      workAddressId,
      companyId,
      photoUrl,
      isApprovedEmployee,
    } = body;

    if (!userId) {
      return NextResponse.json(
        { success: false, error: `A uuidv4 userId is required.` },
        { status: 400 },
      );
    }
    if (!companyId) {
      return NextResponse.json(
        { success: false, error: `A uuidv4 companyId is required.` },
        { status: 400 },
      );
    }

    await prisma.$transaction(async (prisma) => {
      await prisma.user.upsert({
        where: {
          id: session?.user?.id!,
        },
        update: {
          first_name: firstName,
          last_name: lastName,
          photo_url: photoUrl,
        },
        create: {
          id: uuidv4(),
          role: Role.EMPLOYER,
          first_name: firstName,
          last_name: lastName,
          email: session?.user.email!,
          has_agreed_terms: false,
          createdAt: new Date(Date.now()),
        },
      });

      // fixme: need to fetch current companyId. If it is different need to set is_verified_employee to false.
      //  but if the employer is the creator of the company or just editing their profile need to keep is_verified_employee set to true.

      await prisma.employers.upsert({
        where: {
          user_id: session?.user?.id!,
        },
        update: {
          job_title: currentJobTitle,
          ...(linkedInUrl && { linkedin_url: linkedInUrl }),
          ...(isApprovedEmployee && {
            is_verified_employee: isApprovedEmployee,
          }),
          ...(workAddressId && {
            company_addresses: {
              connect: {
                company_address_id: workAddressId,
              },
            },
          }),
          ...(companyId && {
            companies: {
              connect: {
                company_id: companyId,
              },
            },
          }),
        },
        create: {
          employer_id: session?.user.employerId!,
          job_title: currentJobTitle,
          linkedin_url: linkedInUrl,
          is_verified_employee: false,
          users: {
            connect: {
              id: session?.user.id!,
            },
          },
          ...(isApprovedEmployee && {
            is_verified_employee: isApprovedEmployee,
          }),
          ...(workAddressId && {
            company_addresses: {
              connect: {
                company_address_id: workAddressId,
              },
            },
          }),
          ...(companyId && {
            companies: {
              connect: {
                company_id: companyId,
              },
            },
          }),
        },
      });
    }); // end transaction

    return NextResponse.json({ success: true }, { status: 200 });
  } catch (e: any) {
    console.error("Error creating employer profile:", e.message);
    return NextResponse.json(
      { error: `Failed to create employer profile.\n${e.message}` },
      { status: 500 },
    );
  }
}
