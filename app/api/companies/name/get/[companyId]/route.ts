import { NextResponse } from "next/server";
import getPrismaClient from "@/app/lib/prismaClient.mjs";
import { PrismaClient } from "@prisma/client";

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
        { success: false, error: `A uuidv4 companyId  is required.` },
        { status: 400 },
      );
    }
    const result = await prisma.companies.findUnique({
      where: {
        company_id: companyId,
      },
      select: {
        company_name: true,
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
