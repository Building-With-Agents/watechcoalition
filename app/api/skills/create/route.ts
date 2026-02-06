import { adminCreateSkills } from "@/app/lib/admin/skill";
import { SkillDTO } from "@/data/dtos/SkillDTO";
import { NextResponse } from "next/server";

export async function POST(req: Request) {
  const body: SkillDTO[] = await req.json();
  console.log(body);
  const result = await adminCreateSkills(body);
  return NextResponse.json(result);
}
