/**
 * error - copy of /home/megrim/frontend-cfa/types/next-auth.d.ts
 *
 * import NextAuth, { DefaultSession, DefaultUser } from 'next-auth';
import { JWT as DefaultJWT } from 'next-auth/jwt';
import { Role } from 'data/dtos/UserInfoDTO';
import { User as NextAuthUser } from 'next-auth';

declare module 'next-auth' {

  interface User extends NextAuthUser {
    id: string;
    roles: Role[];
    createdAt: Date;
    updatedAt: Date;
    jobseekerId?: string | null,
    employerId?: string | null,
    companyId?: string | null,
    companyIsApproved: boolean,
    employeeIsApproved: boolean,
  }

  interface Session {
    user?: User;
  }

  interface JWT extends DefaultJWT {
    user?: User;
  }
}**/
