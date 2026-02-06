import { NextResponse } from "next/server";
import { CreateUserDTO } from "@/data/dtos/UserInfoDTO";
import { createUser } from "@/app/lib/user";

export async function POST(request: Request) {
  try {
    const body: CreateUserDTO = await request.json();
    const result = await createUser(body);

    if (!result) {
      return NextResponse.json(
        { success: false, error: `User not found.` },
        { status: 404 },
      );
    }

    return NextResponse.json({ success: true, result }, { status: 200 });
  } catch (e: any) {
    return NextResponse.json(
      { error: `Failed to create user record. ${e.message}` },
      { status: 500 },
    );
  }
}
