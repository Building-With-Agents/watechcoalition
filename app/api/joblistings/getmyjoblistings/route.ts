import { getMyJobListings } from "@/app/lib/joblistings";
import { NextResponse } from "next/server";

export async function GET() {
  const results = await getMyJobListings();
  return NextResponse.json(results);
}
