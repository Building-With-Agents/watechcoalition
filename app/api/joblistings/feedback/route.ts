import { feedbackToCandidate } from "@/app/lib/joblistings";
import { NextResponse } from "next/server";

export async function POST(request: Request) {
  const body = await request.json();
  if (!body.jobseekerJobPostingId || !body.rating || !body.comment) {
    return NextResponse.json(
      { error: "Missing a needed field." },
      { status: 400 },
    );
  }
  const result = await feedbackToCandidate(
    body.jobseekerJobPostingId,
    body.rating,
    body.comment,
  );
  return NextResponse.json(result);
}
