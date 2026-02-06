//TODO: write function that takes in a userID and sets their role to career Navigator
import { PrismaClient } from "@prisma/client";
import { Role } from "@/data/dtos/UserInfoDTO";
import getPrismaClient from "@/app/lib/prismaClient.mjs";
import { auth } from "@/auth";
import { deleteEmployer } from "../employer";
import { deleteJobseeker } from "../jobseeker";
const prisma: PrismaClient = getPrismaClient();
/**
 * fully replaces the users role with the role[] provided
 * @param userId user to be updated
 * @param newRoles
 */
export async function adminUpdateUserRole(userId: string, newRoles: Role[]) {
  //TODO when node mailer is set up send email to user letting them know their permissions have updated and they need to log out and back in
  try {
    const session = await auth();
    if (!session?.user.roles.includes(Role.ADMIN)) {
      throw new Error("ADMIN Role Needed for this function");
    }
    const result = await prisma.user.update({
      where: { id: userId },
      data: { role: newRoles.join() },
    });
    return result;
  } catch (error) {
    console.error(error);
  }
}

export async function adminDeleteUser(userId: string) {
  const session = await auth();
  let res: boolean = false;
  try {
    if (!session?.user.roles.includes(Role.ADMIN)) {
      throw new Error("ADMIN Role Needed for this function");
    }
    const user = await prisma.user.findUnique({
      where: {
        id: userId,
      },
    });
    if (user?.role.includes(Role.EMPLOYER)) {
      res = await deleteEmployer(userId);
    } else if (user?.role.includes(Role.JOBSEEKER)) {
      res = await deleteJobseeker(userId);
    } else {
      try {
        await prisma.user.delete({
          where: {
            id: userId,
          },
        });
        res = true;
      } catch {
        res = false;
      }
    }
    if (!res) {
      return { status: 500 };
    }
    return { status: 200 };
  } catch {}
}
