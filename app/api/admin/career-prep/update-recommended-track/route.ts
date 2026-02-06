import { updateAssignedTrack } from "@/app/lib/admin/careerPrep";
import { CareerPrepTrack } from "@/app/lib/poolAssignment";
import { auth } from "@/auth";
import { Role } from "@/data/dtos/UserInfoDTO";
import { NextResponse } from "next/server";

export async function PATCH(request: Request) {
  const session = await auth();
  if (
    !session?.user.roles.includes(Role.CASE_MANAGER) &&
    !session?.user.roles.includes(Role.ADMIN)
  ) {
    return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
  }
  const body: { jobseekerId: string; track: CareerPrepTrack } =
    await request.json();
  if (!body.jobseekerId) {
    return NextResponse.json(
      { error: "jobseekerId is required." },
      { status: 400 },
    );
  }
  const data = await updateAssignedTrack(body.jobseekerId, body.track);
  return NextResponse.json(data);
}
