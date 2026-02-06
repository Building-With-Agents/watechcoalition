import { NextResponse } from "next/server";
import getPrismaClient from "@/app/lib/prismaClient.mjs";
import { PrismaClient } from "@prisma/client";
import { ReadEmployerPersonalDTO } from "@/data/dtos/EmployerProfileCreationDTOs";

const prisma: PrismaClient = getPrismaClient();

export async function GET(
  request: Request,
  props: { params: Promise<{ userId: string }> },
) {
  const params = await props.params;
  try {
    const userId = params.userId;

    if (!userId) {
      return NextResponse.json(
        { success: false, error: `A uuidv4 userId is required.` },
        { status: 400 },
      );
    }
    const empPersonalInfo = await prisma.user.findUnique({
      where: {
        id: userId,
      },
    });

    if (!empPersonalInfo) {
      return NextResponse.json({
        success: true,
        error: `No entry exists for userId: ${userId}`,
      });
    }

    const result: ReadEmployerPersonalDTO = {
      userId: empPersonalInfo.id,
      firstName: empPersonalInfo?.first_name,
      lastName: empPersonalInfo?.last_name,
      birthDate: empPersonalInfo?.birthdate?.toISOString(),
      email: empPersonalInfo?.email,
      phoneCountryCode: empPersonalInfo.phoneCountryCode,
      phone: empPersonalInfo?.phone,
      photoUrl: empPersonalInfo?.photo_url,
    };
    return NextResponse.json({ success: true, result }, { status: 200 });
  } catch (e: any) {
    console.error(
      "Failed to retrieve employer personal information.",
      e.message,
    );
    return NextResponse.json(
      {
        error: `Failed to retrieve employer personal information.\n${e.message}`,
      },
      { status: 500 },
    );
  } finally {
    await prisma.$disconnect();
  }
}
