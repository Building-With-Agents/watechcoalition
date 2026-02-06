// src/app/services/userService.ts
import { Prisma, PrismaClient } from "@prisma/client";
import { CreateUserDTO, ReadUserInfoDTO, Role } from "@/data/dtos/UserInfoDTO";
import { v4 as uuidv4 } from "uuid";
import getPrismaClient from "@/app/lib/prismaClient.mjs";
import { auth } from "@/auth";
import { NextResponse } from "next/server";
import { setPoolWithSession } from "@/app/lib/jobseeker";

const prisma: PrismaClient = getPrismaClient();

export async function createUser(
  userData: CreateUserDTO,
): Promise<ReadUserInfoDTO | null> {
  try {
    const { email, firstName, lastName, roles, image } = userData;

    const data = await prisma.user.create({
      data: {
        id: uuidv4(),
        first_name: firstName,
        last_name: lastName,
        email: email,
        photo_url: image,
        role: roles.map((role) => role.toUpperCase().trim()).join(", "), // concatenate roles with a comma,
        createdAt: new Date(),
        is_marked_deletion: new Date(
          new Date().setDate(new Date().getDate() + 30),
        ), // marked for deletion 30 days from now
      },
      select: {
        id: true,
        role: true,
        first_name: true,
        last_name: true,
        email: true,
        photo_url: true,
        is_marked_deletion: true,
        jobseekers: {
          select: {
            jobseeker_id: true,
          },
        },
        employers: {
          select: {
            employer_id: true,
            company_id: true,
            is_verified_employee: true,
            companies: {
              select: {
                is_approved: true,
              },
            },
          },
        },
      },
    });

    if (!data?.id) {
      return null;
    }

    const responseRoles: Role[] = [];
    responseRoles.push(data.role.toUpperCase() as Role);

    const result: ReadUserInfoDTO = {
      userId: data.id,
      roles: responseRoles,
      firstName: data.first_name,
      lastName: data.last_name,
      email: email,
      image: data.photo_url || undefined,
      jobseekerId: data.jobseekers?.[0]?.jobseeker_id || null,
      employerId: data.employers?.[0]?.employer_id || null,
      companyId: data.employers?.[0]?.company_id || null,
      companyIsApproved: data.employers?.[0]?.companies?.is_approved || false,
      employeeIsApproved: data.employers?.[0]?.is_verified_employee || false,
      isMarkedDeletion: data.is_marked_deletion,
    };

    return result;
  } catch (e: any) {
    throw new Error(`Failed to create user record. ${e.message}`);
  }
}

export async function getUserByEmail(
  email: string,
): Promise<ReadUserInfoDTO | null> {
  try {
    const data = await prisma.user.findUnique({
      where: {
        email: email,
      },
      select: {
        id: true,
        first_name: true,
        last_name: true,
        role: true,
        photo_url: true,
        is_marked_deletion: true,
        jobseekers: {
          select: {
            jobseeker_id: true,
          },
        },
        employers: {
          select: {
            employer_id: true,
            company_id: true,
            is_verified_employee: true,
            companies: {
              select: {
                is_approved: true,
              },
            },
          },
        },
      },
    });

    if (!data?.id) {
      return null;
    }

    // Split the concatenated role string by comma, map to format each role correctly, and add to roles array
    const roles: Role[] = [];
    roles.push(
      ...data.role
        .split(",")
        .map((role: string) => role.toUpperCase().trim() as Role),
    );

    const result: ReadUserInfoDTO = {
      userId: data.id,
      roles: roles,
      firstName: data.first_name,
      lastName: data.last_name,
      email: email,
      image: data?.photo_url || undefined,
      jobseekerId: data.jobseekers?.[0]?.jobseeker_id || null,
      employerId: data.employers?.[0]?.employer_id || null,
      companyId: data.employers?.[0]?.company_id || null,
      companyIsApproved: data.employers?.[0]?.companies?.is_approved || false,
      employeeIsApproved: data.employers?.[0]?.is_verified_employee || false,
      isMarkedDeletion: data.is_marked_deletion,
    };

    return result;
  } catch (e: any) {
    throw new Error(`Failed to read jobseeker skills: ${e.message}`);
  }
}

export type userDataTable = {
  id: string;
  role: string;
  first_name: string | null;
  last_name: string | null;
  email: string;
  phone: string | null;
  zip: string | null;
  is_marked_deletion: Date | null;
};

export async function getAllUsers() {
  try {
    const res = await prisma.user.findMany({
      select: {
        id: true,
        is_marked_deletion: true,
        first_name: true,
        last_name: true,
        email: true,
        phone: true,
        zip: true,
        role: true,
      },
    });
    return res;
  } catch (error) {
    console.error(error);
    return [];
  }
}

export async function unflagDeletion() {
  const session = await auth();
  if (!session?.user?.id) {
    return NextResponse.json(
      { error: "Unable to retrieve user id from session" },
      { status: 409 },
    );
  }
  try {
    await prisma.user.update({
      where: {
        id: session.user.id!,
      },
      data: {
        is_marked_deletion: null,
      },
    });
    return NextResponse.json(`Successfully validated jobseeker profile.`, {
      status: 200,
    });
  } catch (e: any) {
    if (e instanceof Prisma.PrismaClientKnownRequestError) {
      if (e.code === "P2025") {
        // Record not found
        console.error("Record not found:", e);
        return NextResponse.json(
          { error: "The user was not found." },
          { status: 404 },
        );
      }
      // Add specific Prisma errors as needed
      console.error("Unexpected error:", e);
      return NextResponse.json(
        { error: `Failed to validate jobseeker profile.\n${e.message} ` },
        { status: 500 },
      );
    }
  }
}

export async function validateUserProfile() {
  const session = await auth();
  if (session?.user.roles.includes(Role.JOBSEEKER)) {
    await setPoolWithSession();
    return Response.json(
      { success: true },
      {
        status: 200,
      },
    );
  } else {
    return await unflagDeletion();
  }
}
