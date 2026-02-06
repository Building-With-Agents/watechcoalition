import { NextRequest, NextResponse } from "next/server";
import { auth } from "@/auth";
import { Role } from "@/data/dtos/UserInfoDTO";
import { getRecommendedJobSeekersByJobRole } from "@/app/lib/ict";

export async function GET(
  request: NextRequest,
  { params }: { params: Promise<{ roleId: string }> },
) {
  const [session, { roleId }] = await Promise.all([auth(), params]);

  if (
    !session?.user.roles.includes(Role.CASE_MANAGER) &&
    !session?.user.roles.includes(Role.ADMIN)
  ) {
    return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
  }
  if (!roleId) {
    return NextResponse.json({ error: "roleId is required" }, { status: 400 });
  }

  try {
    const results = await getRecommendedJobSeekersByJobRole(roleId);
    if (!results) {
      return NextResponse.json([]);
    }

    return NextResponse.json(results);
  } catch (error) {
    console.error("Error fetching recommendations for role:", roleId, error);
    return NextResponse.json(
      { error: "Failed to fetch recommendations" },
      { status: 500 },
    );
  }
}
