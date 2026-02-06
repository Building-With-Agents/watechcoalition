import { adminGetSkills } from "@/app/lib/admin/skill";
import { NextResponse } from "next/server";

export async function GET() {
  const result = await adminGetSkills();
  return NextResponse.json(result);
}
