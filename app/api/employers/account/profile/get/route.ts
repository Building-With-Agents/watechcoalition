import { getEmployerWithSession } from "@/app/lib/employer";
import { NextResponse } from "next/server";

export async function GET() {
  const result = await getEmployerWithSession();
  return NextResponse.json(result);
}
