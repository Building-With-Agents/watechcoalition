import { adminUpdateSkill } from "@/app/lib/admin/skill";
import { SkillDTO } from "@/data/dtos/SkillDTO";
import { NextResponse } from "next/server";

export async function PUT(req: Request) {
  const body: SkillDTO = await req.json();
  console.log(body);
  const result = await adminUpdateSkill(body);
  return NextResponse.json(result);
}
