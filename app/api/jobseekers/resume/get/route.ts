import { NextResponse } from "next/server";
import { getResumeUrl } from "@/app/lib/services/azureBlobService";
import { auth } from "@/auth";

export async function GET() {
  try {
    const session = await auth();
    const userId = session?.user.id;

    if (!userId) {
      return NextResponse.json(
        { success: false, url: null, error: "No user ID in session storage." },
        { status: 400 },
      );
    }

    const url = await getResumeUrl(userId);

    if (!url) {
      return NextResponse.json(
        { success: false, url: null, error: "No saved resume." },
        { status: 404 },
      );
    }

    return NextResponse.json(url, { status: 200 });
  } catch (e: any) {
    console.error("Error retrieving resume from Blob storage:", e.message);
    return NextResponse.json(
      { error: `Failed to retrieve resume for user.\n${e.message}` },
      { status: 500 },
    );
  }
}
