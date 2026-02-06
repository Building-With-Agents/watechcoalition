import { auth } from "@/auth";
import { NextRequest, NextResponse } from "next/server";

export async function POST(req: NextRequest) {
  try {
    const session = await auth();
    if (!session) {
      return NextResponse.json({ reply: "Unauthorized" }, { status: 401 });
    }
    if (!session.user.jobseekerId) {
      return NextResponse.json({ reply: "Unauthorized" }, { status: 401 });
    }
    if (!process.env.N8N_JOBSEEKER_CHAT_BOT) {
      return NextResponse.json({ reply: "Missing N8N key" }, { status: 401 });
    }

    const { message } = await req.json();
    const res = await fetch(
      "https://computing-for-all-trial.app.n8n.cloud/webhook/34b55a1c-0b0a-4f57-a744-745e369c1f0d",
      {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          CFA: process.env.N8N_JOBSEEKER_CHAT_BOT,
        },
        body: JSON.stringify({
          chatInput: message,
          sessionId: session.user.id.toUpperCase(),
          userId: session.user.id,
        }),
      },
    );
    const responseMessage = await res.json();

    return NextResponse.json({
      reply: responseMessage[0].output || "I didn't get that",
    });
  } catch (error) {
    console.error("chatbot error:", error);
    return NextResponse.json(
      { reply: "Sorry, I'm having trouble right now" },
      { status: 500 },
    );
  }
}
