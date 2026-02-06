import { NextResponse } from "next/server";
import { auth } from "@/auth";
import { getRegisteredEvents } from "@/app/lib/events";

export async function GET() {
  try {
    const session = await auth();
    const sessionUserId: string = session?.user.id!;

    if (!sessionUserId) {
      return NextResponse.json(
        { success: false, error: "Unauthorized" },
        { status: 401 },
      );
    }

    const events = await getRegisteredEvents(false);

    return NextResponse.json({ events }, { status: 200 });
  } catch (e: any) {
    return NextResponse.json(
      { error: `Failed to retrieve registered events: ${e.message}` },
      { status: 500 },
    );
  }
}
