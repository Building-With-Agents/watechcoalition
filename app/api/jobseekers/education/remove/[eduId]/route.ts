import { NextResponse } from "next/server";
import { jobseekers_education, PrismaClient } from "@prisma/client";
import getPrismaClient from "@/app/lib/prismaClient.mjs";
import { auth } from "@/auth";

const prisma: PrismaClient = getPrismaClient();

export async function DELETE(
  request: Request,
  props: { params: Promise<{ eduId: string }> },
) {
  const params = await props.params;
  let eduId = null;
  try {
    // Get essentials from session, not the request
    const session = await auth();
    const jobseekerId: string = session?.user.jobseekerId!;

    eduId = params.eduId;
    const deletedEntry: jobseekers_education =
      await prisma.jobseekers_education.delete({
        where: {
          id: eduId,
          jobseekerId: jobseekerId,
        },
      });

    if (deletedEntry) {
      // education was deleted
      return NextResponse.json({ success: true, result: deletedEntry });
    } else {
      // education doesn't exist or jobseekerId mismatch
      return NextResponse.json({
        error: `Failed to delete jobseeker education with id: ${eduId}`,
      });
    }
  } catch (e: any) {
    console.log(e.message);
    const msg = eduId
      ? `(No Jobseeker Education record with id ${eduId})`
      : `unknown id`;
    return NextResponse.json({
      error: `Failed to delete jobseeker education with id: ${msg}`,
    });
  } finally {
    await prisma.$disconnect();
  }
}
