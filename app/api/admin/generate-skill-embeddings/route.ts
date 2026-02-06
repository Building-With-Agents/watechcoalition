import { generateAllSkillEmbeddings } from "@/app/lib/admin/skill";
import { auth } from "@/auth";
import { Role } from "@/data/dtos/UserInfoDTO";
import { NextResponse } from "next/server";

export async function POST() {
  const session = await auth();
  if (!session?.user.roles.includes(Role.ADMIN)) {
    return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
  }
  try {
    const result = await generateAllSkillEmbeddings();
    return NextResponse.json(result);
  } catch (error) {
    console.error("Error in POST handler:", error);
    return NextResponse.json(
      { error: "Internal server error" },
      { status: 500 },
    );
  }
}
