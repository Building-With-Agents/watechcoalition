import getPrismaClient from "@/app/lib/prismaClient.mjs";
import { auth } from "@/auth";
import { PrismaClient } from "@prisma/client";
import { NextResponse } from "next/server";

const prisma: PrismaClient = getPrismaClient();

export async function PATCH() {
  try {
    // Get essentials from session, not the request
    const session = await auth();
    const userId: string = session?.user.id!;

    if (!userId) {
      return NextResponse.json(
        { success: false, error: `Must provide a valid uuidv4 userId` },
        { status: 400 },
      );
    }
    // TODO: logic & route to mark blob storage video for deletion
    const js = await prisma.jobseekers.update({
      where: {
        user_id: userId,
      },
      data: {
        video_url: null,
      },
      select: {
        jobseeker_id: true,
        video_url: true,
      },
    });
    const result: { jobseekerId: string; videoUrl?: string | null } = {
      jobseekerId: js.jobseeker_id,
      videoUrl: js.video_url,
    };
    return NextResponse.json({ success: true, result }, { status: 200 });
  } catch (e: any) {
    return NextResponse.json(
      { success: false, error: `Failed to delete video.\n${e.message} ` },
      { status: 400 },
    );
  } finally {
    await prisma.$disconnect();
  }
}
