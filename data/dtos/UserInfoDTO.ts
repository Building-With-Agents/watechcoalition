export type ReadUserInfoDTO = {
  userId: string;
  roles: Role[];
  firstName: string | null;
  lastName: string | null;
  email: string;
  image?: string;
  jobseekerId?: string | null;
  employerId?: string | null;
  companyId?: string | null;
  companyIsApproved: boolean;
  employeeIsApproved: boolean;
  isMarkedDeletion: Date | null;
};

export type CreateUserDTO = {
  email: string;
  firstName: string;
  lastName: string;
  image?: string | null;
  roles: Role[];
};

export enum Role {
  ADMIN = "ADMIN",
  EDUCATOR = "EDUCATOR",
  EMPLOYER = "EMPLOYER",
  JOBSEEKER = "JOBSEEKER",
  GUEST = "GUEST", // logged in with oauth but no role selected yet
  VOLUNTEER = "VOLUNTEER",
  CASE_MANAGER = "CASE_MANAGER",
}
