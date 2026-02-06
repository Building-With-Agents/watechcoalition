import { NextResponse } from "next/server";
import {
  CareerPrepStatus,
  updateCareerPrepStatusCardView,
} from "@/app/lib/admin/careerPrep";
import { auth } from "@/auth";
import { Role } from "@/data/dtos/UserInfoDTO";

export async function PATCH(request: Request) {
  const session = await auth();
  if (
    !session?.user.roles.includes(Role.CASE_MANAGER) &&
    !session?.user.roles.includes(Role.ADMIN)
  ) {
    return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
  }
  const body: {
    jobseekerId: string;
    status?: CareerPrepStatus;
    expectedEndDate?: Date;
  } = await request.json();
  if (!body.jobseekerId) {
    return NextResponse.json(
      { error: "jobseekerId is required." },
      { status: 400 },
    );
  }
  const data = await updateCareerPrepStatusCardView(
    body.jobseekerId,
    body.status,
  );
  return NextResponse.json(data);
}
