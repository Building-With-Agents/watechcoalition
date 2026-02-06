import { JobseekerSkillDTO } from "@/data/dtos/JobseekerSkillDTO";

type UserDTO = {
  user_id: string;
  first_name: string;
  last_name: string;
  photo_url: string;
  email: string;
  phone: string;
};

type WorkExperienceDTO = {
  company: string;
  job_title: string;
  is_internship: number;
  is_current_job: number;
  responsibilities: string;
};

type EducationInstitutionDTO = {
  name: string;
};

type ProjectExperienceDTO = {
  project_title: string;
  start_date: string;
  completion_date: string;
  team_size: number;
  repo_url: string;
  demo_url: string;
  problem_solved_description: string;
};

export type JobSeekerEmployerViewDTO = {
  current_job_title: string;
  current_enrolled_ed_program: string;
  current_grade_level: string;
  years_work_exp: number;
  employment_type_sought: string;
  targeted_pathway: string;
  portfolio_url: string;
  users: UserDTO;
  work_experiences: WorkExperienceDTO[];
  edu_institutions: EducationInstitutionDTO;
  project_experiences: ProjectExperienceDTO[];
  jobseeker_has_skills: JobseekerSkillDTO[];
} | null;

export default JobSeekerEmployerViewDTO;
