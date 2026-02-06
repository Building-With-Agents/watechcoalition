import { NextResponse } from "next/server";
import getPrismaClient from "@/app/lib/prismaClient.mjs";
import { PrismaClient } from "@prisma/client";
import { getResumeUrl } from "@/app/lib/services/azureBlobService";
import { auth } from "@/auth";
import { Role } from "@/data/dtos/UserInfoDTO";

const prisma: PrismaClient = getPrismaClient();

export async function GET(
  request: Request,
  props: { params: Promise<{ userId: string }> },
) {
  const params = await props.params;
  const userId = params.userId;
  try {
    const session = await auth();

    // Check if the session exists
    if (!session?.user) {
      return NextResponse.json({ error: "Page not found" }, { status: 404 });
    }

    const { roles, employeeIsApproved } = session.user;

    // Allow access if:
    // 1. The user is an EMPLOYER and is approved, OR ADMIN, OR CASEMANAGER
    // 2. The user is a JOBSEEKER and their session.user.id matches the requested userId
    const isApprovedRole =
      (roles.includes(Role.EMPLOYER) && employeeIsApproved) ||
      roles.includes(Role.ADMIN) ||
      roles.includes(Role.CASE_MANAGER);
    const isJobseekerViewingOwnData =
      roles.includes(Role.JOBSEEKER) && session.user.id === userId;

    if (!isApprovedRole && !isJobseekerViewingOwnData) {
      return NextResponse.json({ error: "Page not found" }, { status: 404 });
    }

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

    return NextResponse.json(url);
  } catch (e: any) {
    console.error("Error retrieving resume from Blob storage:", e.message);
    return NextResponse.json(
      { error: `Failed to retrieve resume for user.\n${e.message}` },
      { status: 500 },
    );
  } finally {
    await prisma.$disconnect();
  }
}
