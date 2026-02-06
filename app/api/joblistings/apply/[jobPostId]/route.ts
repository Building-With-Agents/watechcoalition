import { NextResponse } from "next/server";
import { ApplyToJob } from "@/app/lib/joblistings";
import { sendJobApplicantEmailNotificationEmail } from "@/lib/smtp/sendJobApplicantEmailNotificationEmail";

export async function POST(
  request: Request,
  props: { params: Promise<{ jobPostId: string }> },
) {
  const params = await props.params;
  const jobPostId = params.jobPostId;
  if (!jobPostId) {
    return NextResponse.json(
      { error: "jobPostId is required." },
      { status: 400 },
    );
  }
  const result = await ApplyToJob(jobPostId);
  sendJobApplicantEmailNotificationEmail({
    applicantName: `${result.Jobseekers.users.first_name} ${result.Jobseekers.users.last_name}`,
    jobId: result.jobPostId,
    navigatorName: "",
    jobTitle: result.job_posting.job_title,
    Company: result.job_posting.companies.company_name,
  });
  return NextResponse.json(result);
}
