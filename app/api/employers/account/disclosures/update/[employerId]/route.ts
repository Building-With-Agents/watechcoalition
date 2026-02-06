import { NextResponse } from "next/server";
import getPrismaClient from "@/app/lib/prismaClient.mjs";
import { PrismaClient } from "@prisma/client";
import { auth } from "@/auth";
import { PostEmployerWorkDTO } from "@/data/dtos/EmployerProfileCreationDTOs";

const prisma: PrismaClient = getPrismaClient();

export async function PATCH(request: Request) {
  try {
    // Get essentials from session, not the request
    const session = await auth();
    const employerId: string = session?.user.employerId!;

    if (!employerId) {
      return NextResponse.json(
        { success: false, error: `A uuidv4 employerId  is required.` },
        { status: 400 },
      );
    }
    const body: PostEmployerWorkDTO = await request.json();
    const { currentJobTitle, linkedInUrl, workAddressId } = body;
    const result = await prisma.employers.update({
      where: {
        employer_id: employerId,
      },
      data: {
        job_title: currentJobTitle,
        linkedin_url: linkedInUrl,
        work_address_id: workAddressId,
      },
      select: {
        job_title: true,
        linkedin_url: true,
        work_address_id: true,
      },
    });
    return NextResponse.json({ success: true, result }, { status: 200 });
  } catch (e: any) {
    console.error("Error retrieving company name.", e.message);
    return NextResponse.json(
      {
        error: `Failed to retrieve company name.\n${e.message}`,
      },
      { status: 500 },
    );
  } finally {
    await prisma.$disconnect();
  }
}
