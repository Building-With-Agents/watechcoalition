import { getAllIndustrySectors } from "@/app/lib/employer";
import { NextResponse } from "next/server";

export async function GET() {
  return NextResponse.json(await getAllIndustrySectors());
}
