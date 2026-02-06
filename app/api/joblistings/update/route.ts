import { updateJobListing } from "@/app/lib/joblistings";
import { JobPostCreationDTO } from "@/data/dtos/JobListingDTO";
import { NextResponse } from "next/server";

export async function POST(req: Request) {
  const body: JobPostCreationDTO = await req.json();
  const result = await updateJobListing(body);
  if (result) {
    return NextResponse.json(result);
  } else {
    return NextResponse.json({}, { status: 500 });
  }
}
