import { NextResponse } from "next/server";
import getPrismaClient from "@/app/lib/prismaClient.mjs";
import { PrismaClient } from "@prisma/client";
import { ReadEmployerMissionDTO } from "@/data/dtos/EmployerProfileCreationDTOs";
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
        company_mission: true,
      },
    });

    if (!companyInfo) {
      return NextResponse.json({
        success: true,
        error: `No entry exists for companyId: ${companyId}`,
      });
    }

    const result: ReadEmployerMissionDTO = {
      companyId: companyInfo.company_id,
      mission: companyInfo.company_mission,
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
