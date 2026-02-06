import { adminUpdateUserRole } from "@/app/lib/admin/adminOnlyFuncs";
import { Role } from "@/data/dtos/UserInfoDTO";
import { NextResponse } from "next/server";

export async function POST(req: Request) {
  const body: { userId: string; newRoles: Role[] } = await req.json();
  const res = await adminUpdateUserRole(body.userId, body.newRoles);
  if (res == undefined) {
    return NextResponse.json({}, { status: 500 });
  }
  return NextResponse.json(res);
}
