import { signUpForEvent } from "@/app/lib/events";
import { NextRequest, NextResponse } from "next/server"; // Import NextRequest and NextResponse
export async function POST(req: NextRequest) {
  const { eventId } = await req.json(); // the client sends the eventId in the body
  const result = await signUpForEvent(eventId);
  if (result.success) {
    return NextResponse.json(result);
  } else {
    return NextResponse.json(result, { status: 500 });
  }
}
