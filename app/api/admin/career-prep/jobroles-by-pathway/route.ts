import { NextResponse } from "next/server";
import { auth } from "@/auth";
import { Role } from "@/data/dtos/UserInfoDTO";
import { getJobRolesPerPathway } from "@/app/lib/ict";

export async function GET() {
  const session = await auth();
  if (
    !session?.user.roles.includes(Role.CASE_MANAGER) &&
    !session?.user.roles.includes(Role.ADMIN)
  ) {
    return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
  }

  try {
    const result = await getJobRolesPerPathway();
    return NextResponse.json(result);
  } catch (error) {
    console.error("Error fetching job roles by pathway:", error);
    return NextResponse.json(
      { error: "Failed to fetch job roles by pathway" },
      { status: 500 },
    );
  }
}
