import { getSkillSubcategories } from "@/app/lib/admin/skill";
import { NextResponse } from "next/server";

export async function GET() {
  try {
    const result = await getSkillSubcategories();
    return NextResponse.json(result);
  } catch (e) {
    console.error("Error fetching skill subcategories:", e);
    return NextResponse.json(
      { error: "Failed to fetch skill subcategories" },
      { status: 500 },
    );
  }
}
