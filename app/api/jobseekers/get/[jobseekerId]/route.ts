import { NextResponse } from "next/server";
import { getJobSeekerEmployerView } from "@/app/lib/prisma";
import { auth } from "@/auth";

export async function GET(
  request: Request,
  props: { params: Promise<{ jobseekerId: string }> },
) {
  const params = await props.params;
  try {
    const session = await auth();

    // Check if the session exists
    if (!session?.user) {
      return NextResponse.json({ error: "Page not found" }, { status: 404 });
    }

    const jobseekerId = params.jobseekerId;

    // if (!isEmployerApproved && !isJobseekerViewingOwnData) {
    //   return NextResponse.json({ error: 'Page not found' }, { status: 404 });
    // }

    const jobseekerEmployerView = await getJobSeekerEmployerView(jobseekerId);

    if (!jobseekerEmployerView) {
      return NextResponse.json(
        { error: "Jobseeker not found" },
        { status: 404 },
      );
    }

    return NextResponse.json(jobseekerEmployerView);
  } catch (e: any) {
    console.error("Error retrieving jobseeker employer view:", e.message);
    return NextResponse.json(
      { error: `Failed to retrieve jobseeker employer view.\n${e.message}` },
      { status: 500 },
    );
  }
}
