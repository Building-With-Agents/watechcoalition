import { NextResponse } from "next/server";
import { createJobseeker } from "@/app/lib/jobseeker";
import { auth } from "@/auth";

export async function POST(req: Request) {
  const checkboxes = await req.json();
  try {
    const session = await auth();
    const userId: string = session?.user.id!;
    const result = await createJobseeker(userId, checkboxes);
    return NextResponse.json(
      {
        success: true,
        message: "Jobseeker created successfully.",
        result,
      },
      { status: 200 },
    );
  } catch {
    return NextResponse.json(
      { error: "Failed to create jobseeker." },
      { status: 500 },
    );
  }
}
