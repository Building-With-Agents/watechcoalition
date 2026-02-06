import { NextResponse } from "next/server";
import { getJobSeekerBookmarkedJobs } from "@/app/lib/joblistings";

export async function GET() {
  return NextResponse.json(await getJobSeekerBookmarkedJobs());
}
