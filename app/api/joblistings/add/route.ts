import { createJobListingWithSkills } from "@/app/lib/joblistings";
import { JobPostCreationDTO } from "@/data/dtos/JobListingDTO";
import { NextResponse } from "next/server";

export async function POST(req: Request) {
  const body: JobPostCreationDTO = await req.json();
  console.log("Request body:", body);
  const result = await createJobListingWithSkills(body);
  return NextResponse.json(result);
}
