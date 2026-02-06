import { NextResponse } from "next/server";
import { getJobRole } from "@/app/lib/ict";

export async function GET(
  request: Request,
  props: { params: Promise<{ jobRoleId: string }> },
) {
  const params = await props.params;
  try {
    const jobRoleId = params.jobRoleId;

    // if (!isEmployerApproved && !isJobseekerViewingOwnData) {
    //   return NextResponse.json({ error: 'Page not found' }, { status: 404 });
    // }

    const jobRoleRes = await getJobRole(jobRoleId);

    if (!jobRoleRes) {
      return NextResponse.json({ error: "Jobrole not found" }, { status: 404 });
    }

    return NextResponse.json(jobRoleRes);
  } catch (e: any) {
    console.error("Error retrieving job role:", e.message);
    return NextResponse.json(
      { error: `Failed to retrieve jobrole.\n${e.message}` },
      { status: 500 },
    );
  }
}
