import { NextResponse } from "next/server";
import { getCareerPrepAssessment } from "@/app/lib/admin/careerPrep";
import { auth } from "@/auth";
import { Role } from "@/data/dtos/UserInfoDTO";

export async function GET(
  request: Request,
  props: { params: Promise<{ jobseekerId: string }> },
) {
  const session = await auth();
  if (
    !session?.user.roles.includes(Role.CASE_MANAGER) &&
    !session?.user.roles.includes(Role.ADMIN)
  ) {
    return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
  }
  const params = await props.params;
  const jobseekerId = params.jobseekerId;
  if (!jobseekerId) {
    return NextResponse.json(
      { error: "jobseekerId is required." },
      { status: 400 },
    );
  }

  const data = await getCareerPrepAssessment(jobseekerId);
  return NextResponse.json(data);
}
