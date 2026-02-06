import { NextResponse } from "next/server";
import { PrismaClient, WorkExperience } from "@prisma/client";
import getPrismaClient from "@/app/lib/prismaClient.mjs";
import { auth } from "@/auth";

const prisma: PrismaClient = getPrismaClient();

export async function DELETE(
  request: Request,
  props: { params: Promise<{ workId: string }> },
) {
  const params = await props.params;
  let jsWorkExpId = null;
  try {
    // Get essentials from session, not the request
    const session = await auth();
    const jobseekerId: string = session?.user.jobseekerId!;

    jsWorkExpId = params.workId;
    const deletedEntry: WorkExperience = await prisma.workExperience.delete({
      where: {
        workId: jsWorkExpId,
        jobseekerId: jobseekerId,
      },
    });

    if (deletedEntry) {
      // work experience was deleted
      return NextResponse.json({ success: true, result: deletedEntry });
    } else {
      // work experience doesn't exist or jobseekerId mismatch
      return NextResponse.json({
        error: `Failed to delete jobseeker work experience with id: ${jsWorkExpId}`,
      });
    }
  } catch (e: any) {
    console.log(e.message);
    const msg = jsWorkExpId
      ? `(No Jobseeker Work Experience record with id ${jsWorkExpId})`
      : `unknown id`;
    return NextResponse.json({
      error: `Failed to delete jobseeker work experience with id: ${msg}`,
    });
  } finally {
    await prisma.$disconnect();
  }
}
