import { NextResponse } from "next/server";
import {
  CareerPrepSkillsAssessmentDTO,
  submitCareerPrepAssessmentWithSession,
} from "@/app/lib/admin/careerPrep";
import { sendCareerPrepApplicantEmailNotificationEmail } from "@/lib/smtp/send-career-prep-applicant-email-notification";

export async function POST(request: Request) {
  const body: CareerPrepSkillsAssessmentDTO = await request.json();

  const result = await submitCareerPrepAssessmentWithSession(body);
  await sendCareerPrepApplicantEmailNotificationEmail(body.jobseekerId);
  return NextResponse.json(result);
}
