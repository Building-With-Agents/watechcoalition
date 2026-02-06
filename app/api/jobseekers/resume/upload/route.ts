import { NextResponse } from "next/server";
import { uploadResume } from "@/app/lib/services/azureBlobService";
import { auth } from "@/auth";
import { PrismaClient } from "@prisma/client";

const prisma = new PrismaClient();

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
    const resumeUrl = await uploadResume(fileBuffer, fileName, userId);
    await prisma.jobseekers.update({
      where: { user_id: userId },
      data: {
        hasResume: true,
        updatedAt: new Date(),
      },
    });

    return NextResponse.json(
      { success: true, imageUrl: resumeUrl },
      { status: 200 },
    );
  } catch (e: any) {
    return NextResponse.json(
      { error: `Failed to upload document: ${e.message}` },
      { status: 500 },
    );
  }
}
