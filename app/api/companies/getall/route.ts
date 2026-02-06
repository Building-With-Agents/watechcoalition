import { getAllCompanies } from "@/app/lib/employer";
import { auth } from "@/auth";
import { Role } from "@/data/dtos/UserInfoDTO";
import { NextResponse } from "next/server";

export async function GET() {
  const session = await auth();
  if (
    !session?.user.roles.includes(Role.ADMIN) &&
    !session?.user.roles.includes(Role.CASE_MANAGER)
  ) {
    return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
  }
  return NextResponse.json(await getAllCompanies());
}
