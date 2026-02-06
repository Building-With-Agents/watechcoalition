import { NextResponse } from "next/server";
import { setEmployerConnect } from "@/app/lib/joblistings";

export async function PUT(request: Request) {
  const { jobPostingId, applicationId, status } = await request.json();
  if (!jobPostingId || !applicationId || !status) {
    return NextResponse.json({ error: "Missing a field." }, { status: 400 });
  }
  const result = await setEmployerConnect(jobPostingId, applicationId, status);
  return NextResponse.json(result);
}
