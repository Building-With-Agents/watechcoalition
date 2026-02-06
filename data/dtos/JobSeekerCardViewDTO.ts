import { JobseekerSkillDTO } from "@/data/dtos/JobseekerSkillDTO";
import { ProgramEnrollmentStatus } from "./JobSeekerProfileCreationDTOs";

export type JobSeekerCardViewDTO = {
  jobseeker_id: string;
  user_id: string;
  BookmarkedJobseeker:
    | {
        // bookmarked by current user's company?
        jobseekerId: string;
        companyId: string;
        employerId: string | null;
      }[]
    | null;
  intro_headline: string | null;
  years_work_exp: number | null;
  highest_level_of_study_completed: string | null;
  pathways: {
    pathway_title: string;
  } | null;
  work_experiences:
    | {
        industrySector: {
          industry_sector_id: string;
          sector_title: string;
        } | null;
      }[]
    | null;
  users: {
    role: string;
    first_name: string | null;
    last_name: string | null;
    photo_url: string | null;
    locationData: {
      // Added user addresses returns an array but will be only one item.
      zip: string;
      state: string | null;
      city: string | null;
    } | null;
  } | null;
  jobseeker_education:
    | {
        eduProviders: {
          name: string | null;
        } | null;
        edLevel: string | null;
        enrollmentStatus?: ProgramEnrollmentStatus | string;
        startDate: string | null | Date;
        gradDate: string | null | Date;
        degreeType: string | null;
        program: {
          id: string;
          title: string;
        } | null;
      }[]
    | null; // Corrected to an array as per the select statement
  jobseeker_has_skills: JobseekerSkillDTO[];
};
