import { NextResponse } from "next/server";
import { createEmployer } from "@/app/lib/employer";
import { auth } from "@/auth";
import { sendEmployerOrCompanyNeedsApprovalEmailToGary } from "@/lib/smtp/send-employer-needs-verification-email";

export async function POST() {
  try {
    const session = await auth();
    const userId: string = session?.user.id!;
    const employerData = await createEmployer(userId);
    sendEmployerOrCompanyNeedsApprovalEmailToGary({
      recipient: "gary.larson@computingforall.org",
      name: "Gary Larson",
    });
    return NextResponse.json(
      {
        success: true,
        message: "Employer created successfully.",
        employerData,
      },
      { status: 200 },
    );
  } catch {
    return NextResponse.json(
      { error: "Failed to create Employer." },
      { status: 500 },
    );
  }
}
