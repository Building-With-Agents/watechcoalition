import { NextResponse } from "next/server";
import { uploadCoverLetter } from "@/app/lib/services/azureBlobService";
import { auth } from "@/auth";

export const config = {
  api: {
    bodyParser: {
      sizeLimit: "5mb",
    },
  },
};

export async function POST(request: Request) {
  try {
    // Get essentials from session, not the request
    const session = await auth();
    const userId: string = session?.user.id!;

    const body = await request.json();
    const { file, fileName } = body;

    if (!file || !userId) {
      return NextResponse.json(
        { success: false, error: "Missing file or userId" },
        { status: 400 },
      );
    }

    // Convert file back to Buffer
    const fileBuffer = Buffer.from(new Uint8Array(file));

    // Upload the image using the Azure Blob Storage service
    const coverLetterUrl = await uploadCoverLetter(
      fileBuffer,
      fileName,
      userId,
    );

    return NextResponse.json(
      { success: true, imageUrl: coverLetterUrl },
      { status: 200 },
    );
  } catch (e: any) {
    return NextResponse.json(
      { error: `Failed to upload document: ${e.message}` },
      { status: 500 },
    );
  }
}
