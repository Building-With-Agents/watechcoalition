import { getAllJobPosts } from "@/app/lib/joblistings";
import { NextResponse } from "next/server";

export async function GET() {
  return NextResponse.json(await getAllJobPosts());
}
