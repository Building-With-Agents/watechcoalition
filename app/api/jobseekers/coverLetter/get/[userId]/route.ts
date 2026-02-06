import { NextResponse } from "next/server";
import { getCoverLetterUrl } from "@/app/lib/services/azureBlobService";

// const prisma: PrismaClient = getPrismaClient();

export async function GET(
  request: Request,
  props: { params: Promise<{ userId: string }> },
) {
  const params = await props.params;
  try {
    const userId = params.userId;
    const url = await getCoverLetterUrl(userId);

    if (!url) {
      return NextResponse.json(
        { error: "Cover Letter not found" },
        { status: 404 },
      );
    }

    return NextResponse.json(url);
  } catch (e: any) {
    console.error(
      "Error retrieving cover letter from Blob storage:",
      e.message,
    );
    return NextResponse.json(
      { error: `Failed to retrieve cover letter for user.\n${e.message}` },
      { status: 500 },
    );
  }
}
