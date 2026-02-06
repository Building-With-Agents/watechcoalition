import { NextResponse } from "next/server";
import { PrismaClient, ProjectExperiences } from "@prisma/client";
import getPrismaClient from "@/app/lib/prismaClient.mjs";
import { auth } from "@/auth";

const prisma: PrismaClient = getPrismaClient();

export async function DELETE(
  request: Request,
  props: { params: Promise<{ projectId: string }> },
) {
  const params = await props.params;
  let projId = null;
  try {
    // Get essentials from session, not the request
    const session = await auth();
    const jobseekerId: string = session?.user.jobseekerId!;

    projId = params.projectId;

    const skillsCount = await prisma.project_has_skills.deleteMany({
      where: {
        project_experiences: {
          projectId: projId,
        },
      },
    });

    const deletedEntry: ProjectExperiences =
      await prisma.projectExperiences.delete({
        where: {
          projectId: projId,
          jobseekerId: jobseekerId,
        },
      });

    const result = {
      ...deletedEntry,
      skillsCount,
    };

    if (deletedEntry) {
      // project was deleted
      return NextResponse.json({ success: true, result });
    } else {
      // project doesn't exist or jobseekerId mismatch
      return NextResponse.json({
        error: `Failed to delete jobseeker project with id: ${projId}`,
      });
    }
  } catch (e: any) {
    console.log(e.message);
    const msg = projId
      ? `(No Jobseeker Project record with id ${projId})`
      : `unknown id`;
    return NextResponse.json({
      error: `Failed to delete jobseeker project with id: ${msg}`,
    });
  } finally {
    await prisma.$disconnect();
  }
}
