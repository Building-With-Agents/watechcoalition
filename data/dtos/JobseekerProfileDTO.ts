import { JobseekerSkillDTO } from "@/data/dtos/JobseekerSkillDTO";
import { SkillDTO } from "./SkillDTO";

export type JobseekerProfileDTO = {
  jobseeker_id: string;
  intro_headline: string;
  video_url: string;
  current_job_title: string;
  current_enrolled_ed_program: string;
  current_grade_level: string;
  years_work_exp: number;
  employment_type_sought: string;
  targeted_pathway: string;
  portfolio_url: string;
  linkedin_url: string;
  users: UserDTO;
  work_experiences: WorkExperienceDTO[];
  jobseeker_education: EducationDTO[];
  project_experiences: ProjectExperienceDTO[];
  jobseeker_has_skills: JobseekerSkillDTO[];
  pathways: Pathways;
};

type Pathways = {
  pathway_title: string;
};

type UserDTO = {
  id: string;
  first_name: string;
  last_name: string;
  photo_url: string;
  email: string;
  phone: string;
};

type WorkExperienceDTO = {
  workId: string;
  company: string;
  jobTitle: string;
  is_internship: number;
  is_current_job: number;
  responsibilities: string;
  startDate: string;
  endDate: string;
};

type EducationProviderDTO = {
  id: string;
  name: string;
};

type EduProviderProgramDTO = {
  id: string;
  title: string;
};

type EducationDTO = {
  name: string;
  eduProviders: EducationProviderDTO;
  id: string;
  edLevel: string;
  isEnrolled: boolean;
  startDate: string;
  gradDate: string;
  degreeType: string;
  program: EduProviderProgramDTO;
};

type ProjectExperienceDTO = {
  projectId: string;
  projTitle: string;
  startDate: string;
  completionDate: string;
  teamSize: number;
  repoUrl: string;
  demoUrl: string;
  problemSolvedDescription: string;
  project_has_skills: JobseekerSkillDTO[];
};

export default JobseekerProfileDTO;
