import { addMeeting, CreateMeetingDTO } from "@/app/lib/admin/careerPrep";
import { NextResponse } from "next/server";

export async function POST(request: Request) {
  const body: CreateMeetingDTO = await request.json();
  const result = await addMeeting(body);
  if (result) {
    return NextResponse.json(result);
  }
  return NextResponse.json(
    {
      message: `Meeting Creation failed js with id: ${body.jobseekerId} not found`,
    },
    { status: 404 },
  );
}
