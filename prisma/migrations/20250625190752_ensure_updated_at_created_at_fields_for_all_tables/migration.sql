/*
  Warnings:
  - Made the column `createdAt` on table `companies` required. This step will fail if there are existing NULL values in that column.
  - Made the column `createdAt` on table `employers` required. This step will fail if there are existing NULL values in that column.
  - Made the column `updatedAt` on table `events` required. This step will fail if there are existing NULL values in that column.
  - Made the column `updated_at` on table `users` required. This step will fail if there are existing NULL values in that column.

*/
BEGIN TRY

BEGIN TRAN;

-- AlterTable
ALTER TABLE [dbo].[bookmarked_jobseekers] ADD [created_at] DATETIME NOT NULL CONSTRAINT [bookmarked_jobseekers_created_at_df] DEFAULT CURRENT_TIMESTAMP,
[updated_at] DATETIME NOT NULL CONSTRAINT [bookmarked_jobseekers_updated_at_df] DEFAULT CURRENT_TIMESTAMP;

-- AlterTable
ALTER TABLE [dbo].[BrandingRating] ADD CONSTRAINT [BrandingRating_updatedAt_df] DEFAULT CURRENT_TIMESTAMP FOR [updatedAt];
ALTER TABLE [dbo].[BrandingRating] ADD [createdAt] DATETIME NOT NULL CONSTRAINT [BrandingRating_createdAt_df] DEFAULT CURRENT_TIMESTAMP;

-- AlterTable
ALTER TABLE [dbo].[CareerPrepAssessment] ADD CONSTRAINT [CareerPrepAssessment_updatedAt_df] DEFAULT CURRENT_TIMESTAMP FOR [updatedAt];
ALTER TABLE [dbo].[CareerPrepAssessment] ADD [createdAt] DATETIME NOT NULL CONSTRAINT [CareerPrepAssessment_createdAt_df] DEFAULT CURRENT_TIMESTAMP;

-- AlterTable
ALTER TABLE [dbo].[CaseMgmt] ADD CONSTRAINT [CaseMgmt_updatedAt_df] DEFAULT CURRENT_TIMESTAMP FOR [updatedAt];

-- AlterTable
ALTER TABLE [dbo].[CaseMgmtNotes] ADD CONSTRAINT [CaseMgmtNotes_updatedAt_df] DEFAULT CURRENT_TIMESTAMP FOR [updatedAt];

-- AlterTable
ALTER TABLE [dbo].[certificates] ADD [created_at] DATETIME NOT NULL CONSTRAINT [certificates_created_at_df] DEFAULT CURRENT_TIMESTAMP,
[updated_at] DATETIME NOT NULL CONSTRAINT [certificates_updated_at_df] DEFAULT CURRENT_TIMESTAMP;

-- AlterTable
ALTER TABLE [dbo].[companies] ALTER COLUMN [createdAt] DATETIME NOT NULL;
ALTER TABLE [dbo].[companies] ADD [updatedAt] DATETIME NOT NULL CONSTRAINT [companies_updatedAt_df] DEFAULT CURRENT_TIMESTAMP;

-- AlterTable
ALTER TABLE [dbo].[company_addresses] ADD [created_at] DATETIME NOT NULL CONSTRAINT [company_addresses_created_at_df] DEFAULT CURRENT_TIMESTAMP,
[updated_at] DATETIME NOT NULL CONSTRAINT [company_addresses_updated_at_df] DEFAULT CURRENT_TIMESTAMP;

-- AlterTable
ALTER TABLE [dbo].[CybersecurityRating] ADD CONSTRAINT [CybersecurityRating_updatedAt_df] DEFAULT CURRENT_TIMESTAMP FOR [updatedAt];
ALTER TABLE [dbo].[CybersecurityRating] ADD [createdAt] DATETIME NOT NULL CONSTRAINT [CybersecurityRating_createdAt_df] DEFAULT CURRENT_TIMESTAMP;

-- AlterTable
ALTER TABLE [dbo].[DataAnalyticsRating] ADD CONSTRAINT [DataAnalyticsRating_updatedAt_df] DEFAULT CURRENT_TIMESTAMP FOR [updatedAt];
ALTER TABLE [dbo].[DataAnalyticsRating] ADD [createdAt] DATETIME NOT NULL CONSTRAINT [DataAnalyticsRating_createdAt_df] DEFAULT CURRENT_TIMESTAMP;

-- AlterTable
ALTER TABLE [dbo].[DurableSkillsRating] ADD CONSTRAINT [DurableSkillsRating_updatedAt_df] DEFAULT CURRENT_TIMESTAMP FOR [updatedAt];
ALTER TABLE [dbo].[DurableSkillsRating] ADD [createdAt] DATETIME NOT NULL CONSTRAINT [DurableSkillsRating_createdAt_df] DEFAULT CURRENT_TIMESTAMP;

-- AlterTable
ALTER TABLE [dbo].[edu_addresses] ADD [created_at] DATETIME NOT NULL CONSTRAINT [edu_addresses_created_at_df] DEFAULT CURRENT_TIMESTAMP,
[updated_at] DATETIME NOT NULL CONSTRAINT [edu_addresses_updated_at_df] DEFAULT CURRENT_TIMESTAMP;

-- AlterTable
ALTER TABLE [dbo].[edu_providers] ADD [created_at] DATETIME NOT NULL CONSTRAINT [edu_providers_created_at_df] DEFAULT CURRENT_TIMESTAMP,
[updated_at] DATETIME NOT NULL CONSTRAINT [edu_providers_updated_at_df] DEFAULT CURRENT_TIMESTAMP;

-- AlterTable
ALTER TABLE [dbo].[educators] ADD [created_at] DATETIME NOT NULL CONSTRAINT [educators_created_at_df] DEFAULT CURRENT_TIMESTAMP,
[updated_at] DATETIME NOT NULL CONSTRAINT [educators_updated_at_df] DEFAULT CURRENT_TIMESTAMP;

-- AlterTable
ALTER TABLE [dbo].[EmployerJobRoleFeedBack] ADD [createdAt] DATETIME NOT NULL CONSTRAINT [EmployerJobRoleFeedBack_createdAt_df] DEFAULT CURRENT_TIMESTAMP,
[updatedAt] DATETIME NOT NULL CONSTRAINT [EmployerJobRoleFeedBack_updatedAt_df] DEFAULT CURRENT_TIMESTAMP;

-- AlterTable
ALTER TABLE [dbo].[employers] ALTER COLUMN [createdAt] DATETIME NOT NULL;
ALTER TABLE [dbo].[employers] ADD [updatedAt] DATETIME NOT NULL CONSTRAINT [employers_updatedAt_df] DEFAULT CURRENT_TIMESTAMP;

-- AlterTable
ALTER TABLE [dbo].[events] ALTER COLUMN [updatedAt] DATETIME NOT NULL;
ALTER TABLE [dbo].[events] ADD CONSTRAINT [events_updatedAt_df] DEFAULT CURRENT_TIMESTAMP FOR [updatedAt];

-- AlterTable
ALTER TABLE [dbo].[events_on_users] ADD [created_at] DATETIME NOT NULL CONSTRAINT [events_on_users_created_at_df] DEFAULT CURRENT_TIMESTAMP,
[updated_at] DATETIME NOT NULL CONSTRAINT [events_on_users_updated_at_df] DEFAULT CURRENT_TIMESTAMP;

-- AlterTable
ALTER TABLE [dbo].[industry_sectors] ADD [createdAt] DATETIME NOT NULL CONSTRAINT [industry_sectors_createdAt_df] DEFAULT CURRENT_TIMESTAMP,
[updatedAt] DATETIME NOT NULL CONSTRAINT [industry_sectors_updatedAt_df] DEFAULT CURRENT_TIMESTAMP;

-- AlterTable
ALTER TABLE [dbo].[ITCloudRating] ADD CONSTRAINT [ITCloudRating_updatedAt_df] DEFAULT CURRENT_TIMESTAMP FOR [updatedAt];
ALTER TABLE [dbo].[ITCloudRating] ADD [createdAt] DATETIME NOT NULL CONSTRAINT [ITCloudRating_createdAt_df] DEFAULT CURRENT_TIMESTAMP;

-- AlterTable
ALTER TABLE [dbo].[job_postings] ADD [createdAt] DATETIME NOT NULL CONSTRAINT [job_postings_createdAt_df] DEFAULT CURRENT_TIMESTAMP,
[updatedAt] DATETIME NOT NULL CONSTRAINT [job_postings_updatedAt_df] DEFAULT CURRENT_TIMESTAMP;

-- AlterTable
ALTER TABLE [dbo].[JobPlacement] ADD [createdAt] DATETIME NOT NULL CONSTRAINT [JobPlacement_createdAt_df] DEFAULT CURRENT_TIMESTAMP,
[updatedAt] DATETIME NOT NULL CONSTRAINT [JobPlacement_updatedAt_df] DEFAULT CURRENT_TIMESTAMP;

-- AlterTable
ALTER TABLE [dbo].[JobRole] ADD [createdAt] DATETIME NOT NULL CONSTRAINT [JobRole_createdAt_df] DEFAULT CURRENT_TIMESTAMP,
[updatedAt] DATETIME NOT NULL CONSTRAINT [JobRole_updatedAt_df] DEFAULT CURRENT_TIMESTAMP;

-- AlterTable
ALTER TABLE [dbo].[JobRoleSkill] ADD [createdAt] DATETIME NOT NULL CONSTRAINT [JobRoleSkill_createdAt_df] DEFAULT CURRENT_TIMESTAMP,
[updatedAt] DATETIME NOT NULL CONSTRAINT [JobRoleSkill_updatedAt_df] DEFAULT CURRENT_TIMESTAMP;

-- AlterTable
ALTER TABLE [dbo].[JobRoleTraining] ADD [createdAt] DATETIME NOT NULL CONSTRAINT [JobRoleTraining_createdAt_df] DEFAULT CURRENT_TIMESTAMP,
[updatedAt] DATETIME NOT NULL CONSTRAINT [JobRoleTraining_updatedAt_df] DEFAULT CURRENT_TIMESTAMP;

-- AlterTable
ALTER TABLE [dbo].[jobseeker_has_skills] ADD [createdAt] DATETIME NOT NULL CONSTRAINT [jobseeker_has_skills_createdAt_df] DEFAULT CURRENT_TIMESTAMP,
[updatedAt] DATETIME NOT NULL CONSTRAINT [jobseeker_has_skills_updatedAt_df] DEFAULT CURRENT_TIMESTAMP;

-- AlterTable
ALTER TABLE [dbo].[JobseekerJobPosting] ADD [createdAt] DATETIME NOT NULL CONSTRAINT [JobseekerJobPosting_createdAt_df] DEFAULT CURRENT_TIMESTAMP,
[updatedAt] DATETIME NOT NULL CONSTRAINT [JobseekerJobPosting_updatedAt_df] DEFAULT CURRENT_TIMESTAMP;

-- AlterTable
ALTER TABLE [dbo].[jobseekers_education] ADD [createdAt] DATETIME NOT NULL CONSTRAINT [jobseekers_education_createdAt_df] DEFAULT CURRENT_TIMESTAMP,
[updatedAt] DATETIME NOT NULL CONSTRAINT [jobseekers_education_updatedAt_df] DEFAULT CURRENT_TIMESTAMP;

-- AlterTable
ALTER TABLE [dbo].[jobseekers_private_data] ADD [createdAt] DATETIME NOT NULL CONSTRAINT [jobseekers_private_data_createdAt_df] DEFAULT CURRENT_TIMESTAMP,
[updatedAt] DATETIME NOT NULL CONSTRAINT [jobseekers_private_data_updatedAt_df] DEFAULT CURRENT_TIMESTAMP;

-- AlterTable
ALTER TABLE [dbo].[Meeting] ADD CONSTRAINT [Meeting_updatedAt_df] DEFAULT CURRENT_TIMESTAMP FOR [updatedAt];
ALTER TABLE [dbo].[Meeting] ADD [createdAt] DATETIME NOT NULL CONSTRAINT [Meeting_createdAt_df] DEFAULT CURRENT_TIMESTAMP;

-- AlterTable
ALTER TABLE [dbo].[OtherPriorityPopulations] ADD [created_at] DATETIME NOT NULL CONSTRAINT [OtherPriorityPopulations_created_at_df] DEFAULT CURRENT_TIMESTAMP,
[updated_at] DATETIME NOT NULL CONSTRAINT [OtherPriorityPopulations_updated_at_df] DEFAULT CURRENT_TIMESTAMP;

-- AlterTable
ALTER TABLE [dbo].[pathway_has_skills] ADD [createdAt] DATETIME NOT NULL CONSTRAINT [pathway_has_skills_createdAt_df] DEFAULT CURRENT_TIMESTAMP,
[updatedAt] DATETIME NOT NULL CONSTRAINT [pathway_has_skills_updatedAt_df] DEFAULT CURRENT_TIMESTAMP;

-- AlterTable
ALTER TABLE [dbo].[pathway_subcategories] ADD [createdAt] DATETIME NOT NULL CONSTRAINT [pathway_subcategories_createdAt_df] DEFAULT CURRENT_TIMESTAMP,
[updatedAt] DATETIME NOT NULL CONSTRAINT [pathway_subcategories_updatedAt_df] DEFAULT CURRENT_TIMESTAMP;

-- AlterTable
ALTER TABLE [dbo].[pathways] ADD [createdAt] DATETIME NOT NULL CONSTRAINT [pathways_createdAt_df] DEFAULT CURRENT_TIMESTAMP,
[updatedAt] DATETIME NOT NULL CONSTRAINT [pathways_updatedAt_df] DEFAULT CURRENT_TIMESTAMP;

-- AlterTable
ALTER TABLE [dbo].[PathwayTraining] ADD [createdAt] DATETIME NOT NULL CONSTRAINT [PathwayTraining_createdAt_df] DEFAULT CURRENT_TIMESTAMP,
[updatedAt] DATETIME NOT NULL CONSTRAINT [PathwayTraining_updatedAt_df] DEFAULT CURRENT_TIMESTAMP;

-- AlterTable
ALTER TABLE [dbo].[programs] ADD [createdAt] DATETIME NOT NULL CONSTRAINT [programs_createdAt_df] DEFAULT CURRENT_TIMESTAMP,
[updatedAt] DATETIME NOT NULL CONSTRAINT [programs_updatedAt_df] DEFAULT CURRENT_TIMESTAMP;

-- AlterTable
ALTER TABLE [dbo].[project_experiences] ADD [createdAt] DATETIME NOT NULL CONSTRAINT [project_experiences_createdAt_df] DEFAULT CURRENT_TIMESTAMP,
[updatedAt] DATETIME NOT NULL CONSTRAINT [project_experiences_updatedAt_df] DEFAULT CURRENT_TIMESTAMP;

-- AlterTable
ALTER TABLE [dbo].[project_has_skills] ADD [createdAt] DATETIME NOT NULL CONSTRAINT [project_has_skills_createdAt_df] DEFAULT CURRENT_TIMESTAMP,
[updatedAt] DATETIME NOT NULL CONSTRAINT [project_has_skills_updatedAt_df] DEFAULT CURRENT_TIMESTAMP;

-- AlterTable
ALTER TABLE [dbo].[provider_program_has_skills] ADD [createdAt] DATETIME NOT NULL CONSTRAINT [provider_program_has_skills_createdAt_df] DEFAULT CURRENT_TIMESTAMP,
[updatedAt] DATETIME NOT NULL CONSTRAINT [provider_program_has_skills_updatedAt_df] DEFAULT CURRENT_TIMESTAMP;

-- AlterTable
ALTER TABLE [dbo].[provider_programs] ADD [createdAt] DATETIME NOT NULL CONSTRAINT [provider_programs_createdAt_df] DEFAULT CURRENT_TIMESTAMP,
[updatedAt] DATETIME NOT NULL CONSTRAINT [provider_programs_updatedAt_df] DEFAULT CURRENT_TIMESTAMP;

-- AlterTable
ALTER TABLE [dbo].[skill_subcategories] ADD [createdAt] DATETIME NOT NULL CONSTRAINT [skill_subcategories_createdAt_df] DEFAULT CURRENT_TIMESTAMP,
[updatedAt] DATETIME NOT NULL CONSTRAINT [skill_subcategories_updatedAt_df] DEFAULT CURRENT_TIMESTAMP;

-- AlterTable
ALTER TABLE [dbo].[skills] ADD [createdAt] DATETIME NOT NULL CONSTRAINT [skills_createdAt_df] DEFAULT CURRENT_TIMESTAMP,
[updatedAt] DATETIME NOT NULL CONSTRAINT [skills_updatedAt_df] DEFAULT CURRENT_TIMESTAMP;

-- AlterTable
ALTER TABLE [dbo].[social_media_platforms] ADD [createdAt] DATETIME NOT NULL CONSTRAINT [social_media_platforms_createdAt_df] DEFAULT CURRENT_TIMESTAMP,
[updatedAt] DATETIME NOT NULL CONSTRAINT [social_media_platforms_updatedAt_df] DEFAULT CURRENT_TIMESTAMP;

-- AlterTable
ALTER TABLE [dbo].[SoftwareDevRating] ADD CONSTRAINT [SoftwareDevRating_updatedAt_df] DEFAULT CURRENT_TIMESTAMP FOR [updatedAt];
ALTER TABLE [dbo].[SoftwareDevRating] ADD [createdAt] DATETIME NOT NULL CONSTRAINT [SoftwareDevRating_createdAt_df] DEFAULT CURRENT_TIMESTAMP;

-- AlterTable
ALTER TABLE [dbo].[technology_areas] ADD [createdAt] DATETIME NOT NULL CONSTRAINT [technology_areas_createdAt_df] DEFAULT CURRENT_TIMESTAMP,
[updatedAt] DATETIME NOT NULL CONSTRAINT [technology_areas_updatedAt_df] DEFAULT CURRENT_TIMESTAMP;

-- AlterTable
ALTER TABLE [dbo].[TraineeDetail] ADD [created_at] DATETIME NOT NULL CONSTRAINT [TraineeDetail_created_at_df] DEFAULT CURRENT_TIMESTAMP,
[updated_at] DATETIME NOT NULL CONSTRAINT [TraineeDetail_updated_at_df] DEFAULT CURRENT_TIMESTAMP;

-- AlterTable
ALTER TABLE [dbo].[Training] ADD [createdAt] DATETIME NOT NULL CONSTRAINT [Training_createdAt_df] DEFAULT CURRENT_TIMESTAMP,
[updatedAt] DATETIME NOT NULL CONSTRAINT [Training_updatedAt_df] DEFAULT CURRENT_TIMESTAMP;

-- AlterTable
ALTER TABLE [dbo].[users] ALTER COLUMN [updated_at] DATETIME NOT NULL;
ALTER TABLE [dbo].[users] ADD CONSTRAINT [users_updated_at_df] DEFAULT CURRENT_TIMESTAMP FOR [updated_at];

-- AlterTable
ALTER TABLE [dbo].[volunteer_has_skills] ADD [createdAt] DATETIME NOT NULL CONSTRAINT [volunteer_has_skills_createdAt_df] DEFAULT CURRENT_TIMESTAMP,
[updatedAt] DATETIME NOT NULL CONSTRAINT [volunteer_has_skills_updatedAt_df] DEFAULT CURRENT_TIMESTAMP;

-- AlterTable
ALTER TABLE [dbo].[volunteers] ADD [createdAt] DATETIME NOT NULL CONSTRAINT [volunteers_createdAt_df] DEFAULT CURRENT_TIMESTAMP,
[updatedAt] DATETIME NOT NULL CONSTRAINT [volunteers_updatedAt_df] DEFAULT CURRENT_TIMESTAMP;

-- AlterTable
ALTER TABLE [dbo].[work_experiences] ADD [createdAt] DATETIME NOT NULL CONSTRAINT [work_experiences_createdAt_df] DEFAULT CURRENT_TIMESTAMP,
[updatedAt] DATETIME NOT NULL CONSTRAINT [work_experiences_updatedAt_df] DEFAULT CURRENT_TIMESTAMP;

COMMIT TRAN;

END TRY
BEGIN CATCH

IF @@TRANCOUNT > 0
BEGIN
    ROLLBACK TRAN;
END;
THROW

END CATCH
