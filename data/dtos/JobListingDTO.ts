import { SkillDTO } from "./SkillDTO";
import { PostalGeoDataDTO } from "./PostalGeoDataDTO";

export type JobPostCreationDTO = {
  job_posting_id?: string;
  tech_area_id: string | null;
  techArea: { id: string; title: string } | null;
  sector_id: string | null;
  company_id: string | null;
  jobApplications: {
    id: string;
    jobseekerId: string;
    jobStatus: string;
    Jobseekers: {
      pathways: {
        pathway_title: string;
      } | null;
      users: {
        first_name: string | null;
        last_name: string | null;
        photo_url: string | null;
        zip: string | null;
        email: string | null;
      };
      intro_headline: string | null;
      jobseeker_has_skills?:
        | {
            skills: SkillDTO;
          }[]
        | null;
    };
    postalGeoData?: PostalGeoDataDTO;
  }[];
  postalGeoData?: PostalGeoDataDTO;
  job_title: string;
  job_description: string;
  is_internship?: boolean;
  is_apprenticeship: boolean;
  is_paid?: boolean;
  employment_type?: string;
  location: string;
  salary_range: string;
  relocation_services_available: boolean;
  offer_visa_sponsorship: boolean;
  zip: string;
  publish_date: Date | null;
  unpublish_date: Date | null;
  job_post_url: string | null;
  assessment_url: string | null;
  skills?: SkillDTO[];
  skillIds?: string[];
  earn_and_learn_type: string | null;
  occupation_code: string | null;
  employment_duration: string | null;
  start_date: Date | null;
  end_date: Date | null;
  career_services_offered: boolean | null;
  trainingRequirements: string | null;
  requiredCertifications: string | null;
  minimumEducationLevel: string | null;
};
