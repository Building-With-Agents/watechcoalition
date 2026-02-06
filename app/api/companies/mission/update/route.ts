import { NextResponse } from "next/server";
import getPrismaClient from "@/app/lib/prismaClient.mjs";
import { PrismaClient } from "@prisma/client";
import { auth } from "@/auth";

const prisma: PrismaClient = getPrismaClient();

export async function PATCH(request: Request) {
  try {
    // Get essentials from session, not the request
    const session = await auth();
    const companyId: string | null | undefined = session?.user.companyId;

    const body: { companyId: string; mission: string } = await request.json();
    const { mission } = body;

    // validate the companyId and verify the user is an approved employee
    if (!companyId) {
      return NextResponse.json(
        { success: false, error: `A uuidv4 companyId is required.` },
        { status: 400 },
      );
    }

    const companyInQuestion = await prisma.companies.findUnique({
      where: {
        company_id: session?.user.companyId!,
      },
    });

    // have to allow permission for the creator of the company to edit as they are making it.
    if (
      !session?.user.employeeIsApproved &&
      companyInQuestion?.createdBy !== session?.user.id
    ) {
      return NextResponse.json(
        {
          success: false,
          error: `Employee needs to be approved to edit this company.`,
        },
        { status: 401 },
      );
    }

    const result = await prisma.companies.update({
      where: {
        company_id: companyId,
      },
      data: {
        company_mission: mission,
      },
    });
    return NextResponse.json({ success: true, result }, { status: 200 });
  } catch (e: any) {
    console.error("Error updating company mission content.", e.message);
    return NextResponse.json(
      {
        error: `Failed to update company mission content..\n${e.message}`,
      },
      { status: 500 },
    );
  }
}
