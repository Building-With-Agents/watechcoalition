import { getJobseekerBookmarkByCompany } from "@/app/lib/prisma";
import { NextResponse } from "next/server";

export async function GET() {
  return NextResponse.json(await getJobseekerBookmarkByCompany());
}
