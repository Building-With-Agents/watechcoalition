import { NextResponse } from "next/server";
import {
  CareerPrepJobseekerCardViewDTO,
  getAllCareerPrepStudentsCardView,
} from "@/app/lib/admin/careerPrep";
import { auth } from "@/auth";
import { Role } from "@/data/dtos/UserInfoDTO";

export async function GET() {
  const session = await auth();
  if (
    !session?.user.roles.includes(Role.CASE_MANAGER) &&
    !session?.user.roles.includes(Role.ADMIN)
  ) {
    return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
  }
  const data: CareerPrepJobseekerCardViewDTO[] | null =
    await getAllCareerPrepStudentsCardView();

  if (data === null) {
    // Return a 500 error response if data is null due to an error
    return NextResponse.json(
      { error: "Failed to Career Prep Jobseeker Card view data" },
      { status: 500 },
    );
  }

  return NextResponse.json(data);
}
