import { NextResponse } from "next/server";
import { PrismaClient } from "@prisma/client";
import getPrismaClient from "@/app/lib/prismaClient.mjs";
import { devLog, mapToEnumOrThrow } from "@/app/lib/utils";
import { Role } from "@/data/dtos/UserInfoDTO";
import { auth } from "@/auth";

const prisma: PrismaClient = getPrismaClient();

export async function PATCH(request: Request) {
  try {
    // Get essentials from session, not the request
    const session = await auth();
    const userId: string = session?.user.id!;

    const body: {
      role: Role;
      sendNewJobPosts?: boolean;
      sendCareerOpportunities?: boolean;
      agreedTerms: boolean;
    } = await request.json();

    // Destructure the DTO
    const { role, sendNewJobPosts, sendCareerOpportunities, agreedTerms } =
      body;

    const result = await prisma.$transaction(async (prisma) => {
      // Fetch the current user roles
      const user = await prisma.user.findUnique({
        where: { id: userId },
        select: { role: true }, // Only fetching the role field
      });

      if (!user) {
        throw new Error("User not found");
      }

      // Split the current roles
      let currentRoles: Role[] = user.role
        .split(",")
        .map((r) => r.trim().toUpperCase() as Role);
      // Ensure the role is valid using mapToEnumOrThrow
      const newRole = mapToEnumOrThrow(role, Role);
      // Remove Role.GUEST if the new role is not Role.GUEST
      if (newRole !== Role.GUEST) {
        currentRoles = currentRoles.filter((r: Role) => r !== Role.GUEST);
      }

      // Add the new role if it's not already in the roles array
      if (!currentRoles.includes(newRole)) {
        currentRoles.push(newRole);
      }

      // and rejoin them
      const updatedRoles = currentRoles.join(",");

      // Upsert user
      return prisma.user.update({
        where: { id: userId },
        data: {
          role: updatedRoles,
          ...(sendNewJobPosts && { sendNewJobPosts: sendNewJobPosts }),
          ...(sendCareerOpportunities && {
            sendCareerOpportunities: sendCareerOpportunities,
          }),
          has_agreed_terms: agreedTerms,
        },
      });
    });
    devLog("ss-result", result);
    return NextResponse.json({ success: true, result }, { status: 200 });
  } catch (error) {
    console.error("Error creating job seeker intro:", error);
    return NextResponse.json(
      { error: "Failed to create job seeker intro" },
      { status: 500 },
    );
  } finally {
    await prisma.$disconnect();
  }
}
