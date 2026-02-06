import NextAuth, { DefaultSession, DefaultUser } from "next-auth";
import { JWT as DefaultJWT } from "next-auth/jwt";
import { Role } from "data/dtos/UserInfoDTO";

declare module "next-auth" {
  interface User extends DefaultUser {
    id: string;
    firstName: string | null;
    lastName: string | null;
    email: string;
    roles: Role[];
    createdAt: Date;
    updatedAt: Date;
    jobseekerId?: string | null;
    employerId?: string | null;
    companyId?: string | null;
    companyIsApproved: boolean;
    employeeIsApproved: boolean;
    image?: string;
  }

  interface Session {
    user: User;
  }
}

declare module "next-auth/jwt" {
  interface JWT extends DefaultJWT {
    id: string;
    firstName: string | null;
    lastName: string | null;
    email: string;
    roles: Role[];
    jobseekerId?: string | null;
    employerId?: string | null;
    companyId?: string | null;
    companyIsApproved: boolean;
    employeeIsApproved: boolean;
    image?: string;
  }
}
