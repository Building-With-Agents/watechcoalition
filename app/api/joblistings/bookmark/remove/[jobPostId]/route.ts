import { NextResponse } from "next/server";
import { unbookmarkJobPosting } from "@/app/lib/joblistings";

export async function POST(
  request: Request,
  props: { params: Promise<{ jobPostId: string }> },
) {
  const params = await props.params;
  const jobPostId = params.jobPostId;
  if (!jobPostId) {
    return NextResponse.json(
      { error: "jobPostId is required." },
      { status: 400 },
    );
  }
  return NextResponse.json(await unbookmarkJobPosting(jobPostId));
}
