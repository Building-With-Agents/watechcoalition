import { NextResponse } from "next/server";
import getPrismaClient from "@/app/lib/prismaClient.mjs";
import { PrismaClient } from "@prisma/client";
import {
  PostEmployerPersonalDTO,
  ReadEmployerPersonalDTO,
} from "@/data/dtos/EmployerProfileCreationDTOs";
import { Role } from "@/data/dtos/UserInfoDTO";
import { auth } from "@/auth";

const prisma: PrismaClient = getPrismaClient();

export async function POST(request: Request) {
  try {
    // Get essentials from session, not the request
    const session = await auth();
    const userId: string = session?.user.id!;

    const body: PostEmployerPersonalDTO = await request.json();
    const { firstName, lastName, photoUrl } = body;

    // const formattedPhone = formatPhoneE164(phoneCountryCode, phone);
    const upsertedUser = await prisma.user.upsert({
      where: {
        id: userId,
      },
      update: {
        first_name: firstName,
        last_name: lastName,
        photo_url: photoUrl,
        updatedAt: new Date(),
      },
      create: {
        id: userId,
        role: Role.EMPLOYER,
        first_name: firstName,
        last_name: lastName,
        birthdate: undefined,
        email: session?.user.email!,
        phoneCountryCode: undefined,
        phone: undefined,
        photo_url: photoUrl,
        createdAt: new Date(),
      },
    });

    const result: ReadEmployerPersonalDTO = {
      userId: upsertedUser.id,
      firstName: upsertedUser.first_name,
      lastName: upsertedUser.last_name,
      // birthDate: upsertedUser?.birthdate?.toISOString(),
      email: upsertedUser.email,
      // phoneCountryCode: phoneCountryCode ?? null,
      // phone: phone ?? null,
      photoUrl: upsertedUser.photo_url,
    };
    return NextResponse.json({ success: true, result }, { status: 200 });
  } catch (e: any) {
    console.error("Error upserting employer:", e.message);
    return NextResponse.json(
      {
        error: `Failed to upsert employer personal information.\n${e.message}`,
      },
      { status: 500 },
    );
  }
}
