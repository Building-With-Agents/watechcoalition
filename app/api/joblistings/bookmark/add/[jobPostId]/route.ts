import { bookmarkJobPosting } from "@/app/lib/joblistings";
import { NextResponse } from "next/server";

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
  return NextResponse.json(await bookmarkJobPosting(jobPostId));
}
