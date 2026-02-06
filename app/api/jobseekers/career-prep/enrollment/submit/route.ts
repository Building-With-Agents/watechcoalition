import { NextResponse } from "next/server";
import {
  CareerPrepEnrollmentDTO,
  submitCareerPrepEnrollment,
} from "@/app/lib/admin/careerPrep";

export async function POST(request: Request) {
  const body: CareerPrepEnrollmentDTO = await request.json();

  const result = await submitCareerPrepEnrollment(body);
  return NextResponse.json(result);
}
