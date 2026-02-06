import { NextRequest, NextResponse } from "next/server";
import {
  submitAiWorkforceContact,
  AiWorkforceContactDTO,
} from "@/app/lib/aiWorkforce/contacts";

/**
 * API route for submitting AI Workforce contact forms.
 * Forwards the payload to the Logic Apps endpoint.
 */
export async function POST(request: NextRequest) {
  const body: AiWorkforceContactDTO = await request.json();
  const result = await submitAiWorkforceContact(body);
  return NextResponse.json(result);
}
