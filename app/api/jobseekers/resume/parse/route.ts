import { NextResponse } from "next/server";
import { uploadResume } from "@/app/lib/services/azureBlobService";
import { auth } from "@/auth";
import { PrismaClient } from "@prisma/client";
import { parseResumeText } from "@/app/lib/jobseeker";

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
    const session = await auth();
    const userId: string = session?.user.id!;

    const formData = await request.formData();
    const file = formData.get("file") as File;
    const extractedText = formData.get("extractedText") as string;

    if (!file || !userId) {
      return NextResponse.json(
        { success: false, error: "Missing file or extractedText in form data" },
        { status: 400 },
      );
    }

    const resumeText = await parseResumeText(extractedText);

    const fileBuffer = Buffer.from(await file.arrayBuffer());
    const resumeUrl = await uploadResume(fileBuffer, "resume.pdf", userId);
    await prisma.jobseekers.update({
      where: { user_id: userId },
      data: {
        hasResume: true,
        updatedAt: new Date(),
      },
    });

    return NextResponse.json(
      { success: true, resumeText: resumeText, resumeUrl: resumeUrl },
      { status: 200 },
    );
  } catch (e: any) {
    return NextResponse.json(
      { error: `Failed to upload or parse resume: ${e.message}` },
      { status: 500 },
    );
  }
}
