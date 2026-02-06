import { getCompanyJobListings } from "@/app/lib/joblistings";
import { NextResponse } from "next/server";

export async function GET() {
  const results = await getCompanyJobListings();
  return NextResponse.json(results);
}
