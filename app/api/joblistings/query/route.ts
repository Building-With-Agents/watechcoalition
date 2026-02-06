import { NextResponse } from "next/server";
import { getJobListingsFiltered } from "@/app/lib/joblistings";

export async function POST(request: Request) {
  return NextResponse.json(await getJobListingsFiltered(request));
}
