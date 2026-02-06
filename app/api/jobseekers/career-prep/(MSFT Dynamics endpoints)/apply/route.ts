import { NextResponse } from "next/server";
import {
  submitCareerPrepApplication,
  CareerPrepApplicationDTO,
} from "@/app/lib/admin/careerPrep";

/**
 * API route for submitting Career Prep applications.
 * Forwards the payload to the Microsoft List endpoint via Logic Apps.
 */
export async function POST(request: Request) {
  const body: CareerPrepApplicationDTO = await request.json();
  const result = await submitCareerPrepApplication(body);
  return NextResponse.json(result);
}
