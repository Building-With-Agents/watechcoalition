import { updateJobStatus } from "@/app/lib/admin/careerPrep";
import { JobStatus } from "@/app/lib/jobseekerJobTracking";
import { auth } from "@/auth";
import { Role } from "@/data/dtos/UserInfoDTO";
import { NextResponse } from "next/server";
interface updateJobStatusData {
  newJobStatus: JobStatus;
  joinTableId: string;
}
export async function PATCH(req: Request) {
  const session = await auth();
  if (
    !session?.user.roles.includes(Role.CASE_MANAGER) &&
    !session?.user.roles.includes(Role.ADMIN)
  ) {
    return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
  }
  const body: updateJobStatusData = await req.json();
  const result = await updateJobStatus(body.newJobStatus, body.joinTableId);
  return NextResponse.json(result);
}
