import { NextResponse } from "next/server";
import { certificates, PrismaClient } from "@prisma/client";
import getPrismaClient from "@/app/lib/prismaClient.mjs";
import { auth } from "@/auth";

const prisma: PrismaClient = getPrismaClient();

export async function DELETE(
  request: Request,
  props: { params: Promise<{ certificateId: string }> },
) {
  const params = await props.params;
  let certificateId = null;
  try {
    // Get essentials from session, not the request
    const session = await auth();
    const jobseekerId: string = session?.user.jobseekerId!;

    certificateId = params.certificateId;

    const deletedEntry: certificates = await prisma.certificates.delete({
      where: {
        certId: certificateId,
        jobSeekerId: jobseekerId,
      },
    });

    if (deletedEntry) {
      // Certificate was deleted
      return NextResponse.json({ success: true, result: deletedEntry });
    } else {
      // cert doesn't exist or jobseekerId mismatch
      return NextResponse.json({
        error: `Failed to delete jobseeker certificate with id: ${certificateId}`,
      });
    }
  } catch (e: any) {
    console.log(e.message);
    const msg = certificateId
      ? `(No Jobseeker Certificate record with id ${certificateId})`
      : `unknown id`;
    return NextResponse.json({
      error: `Failed to delete jobseeker certificate with id: ${msg}`,
    });
  } finally {
    await prisma.$disconnect();
  }
}
