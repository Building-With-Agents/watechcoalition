import { TakeEmployerFeedBack } from "@/app/lib/ict";
import { NextRequest, NextResponse } from "next/server";

export async function POST(req: NextRequest) {
  try {
    const { jobRoleId, skillRatings } = await req.json();

    if (!jobRoleId || !skillRatings) {
      return NextResponse.json({ message: "Invalid data" }, { status: 400 });
    }

    const result = await TakeEmployerFeedBack(jobRoleId, skillRatings);

    if (result.success) {
      return NextResponse.json(
        { message: "Data processed successfully" },
        { status: 200 },
      );
    } else {
      return NextResponse.json(
        { message: "Failed to process data" },
        { status: 500 },
      );
    }
  } catch (error) {
    console.error("Error processing request:", error);
    return NextResponse.json(
      { success: false, error: "Internal Server Error" },
      { status: 500 },
    );
  }
}
