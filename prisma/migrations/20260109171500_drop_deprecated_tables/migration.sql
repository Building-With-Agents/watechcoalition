BEGIN TRY

BEGIN TRAN;

-- Drop foreign keys that touch tables we are removing
IF EXISTS (SELECT 1 FROM sys.foreign_keys WHERE name = '_OtherPriorityPopulations_A_fkey')
  ALTER TABLE [dbo].[_OtherPriorityPopulations] DROP CONSTRAINT [_OtherPriorityPopulations_A_fkey];

IF EXISTS (SELECT 1 FROM sys.foreign_keys WHERE name = '_OtherPriorityPopulations_B_fkey')
  ALTER TABLE [dbo].[_OtherPriorityPopulations] DROP CONSTRAINT [_OtherPriorityPopulations_B_fkey];

IF EXISTS (SELECT 1 FROM sys.foreign_keys WHERE name = 'fk_social_media_company_company1')
  ALTER TABLE [dbo].[company_social_links] DROP CONSTRAINT [fk_social_media_company_company1];

IF EXISTS (SELECT 1 FROM sys.foreign_keys WHERE name = 'fk_social_media_company_social_media_platform1')
  ALTER TABLE [dbo].[company_social_links] DROP CONSTRAINT [fk_social_media_company_social_media_platform1];

IF EXISTS (SELECT 1 FROM sys.foreign_keys WHERE name = 'fk_social_media_employer_employer1')
  ALTER TABLE [dbo].[company_social_links] DROP CONSTRAINT [fk_social_media_employer_employer1];

IF EXISTS (SELECT 1 FROM sys.foreign_keys WHERE name = 'fk_company_testimonals_employer1')
  ALTER TABLE [dbo].[company_testimonials] DROP CONSTRAINT [fk_company_testimonals_employer1];

IF EXISTS (SELECT 1 FROM sys.foreign_keys WHERE name = 'fk_company_testimonials_company1')
  ALTER TABLE [dbo].[company_testimonials] DROP CONSTRAINT [fk_company_testimonials_company1];

IF EXISTS (SELECT 1 FROM sys.foreign_keys WHERE name = 'fk_proj_based_tech_assessments_Pathways1')
  ALTER TABLE [dbo].[proj_based_tech_assessments] DROP CONSTRAINT [fk_proj_based_tech_assessments_Pathways1];

IF EXISTS (SELECT 1 FROM sys.foreign_keys WHERE name = 'ProviderTestimonials_eduProviderId_fkey')
  ALTER TABLE [dbo].[ProviderTestimonials] DROP CONSTRAINT [ProviderTestimonials_eduProviderId_fkey];

IF EXISTS (SELECT 1 FROM sys.foreign_keys WHERE name = 'fk_sa_possilbe_answer_sa_question1')
  ALTER TABLE [dbo].[sa_possible_answers] DROP CONSTRAINT [fk_sa_possilbe_answer_sa_question1];

IF EXISTS (SELECT 1 FROM sys.foreign_keys WHERE name = 'fk_sa_question_self_assessment')
  ALTER TABLE [dbo].[sa_questions] DROP CONSTRAINT [fk_sa_question_self_assessment];

IF EXISTS (SELECT 1 FROM sys.foreign_keys WHERE name = 'fk_self_assessments_Pathways1')
  ALTER TABLE [dbo].[self_assessments] DROP CONSTRAINT [fk_self_assessments_Pathways1];

IF EXISTS (SELECT 1 FROM sys.foreign_keys WHERE name = 'fk_traineeDetail_jobseekers_education1')
  ALTER TABLE [dbo].[TraineeDetail] DROP CONSTRAINT [fk_traineeDetail_jobseekers_education1];

-- Drop tables (dependency order: children first)
IF OBJECT_ID('[dbo].[sa_possible_answers]', 'U') IS NOT NULL DROP TABLE [dbo].[sa_possible_answers];
IF OBJECT_ID('[dbo].[sa_questions]', 'U') IS NOT NULL DROP TABLE [dbo].[sa_questions];
IF OBJECT_ID('[dbo].[self_assessments]', 'U') IS NOT NULL DROP TABLE [dbo].[self_assessments];

IF OBJECT_ID('[dbo].[proj_based_tech_assessments]', 'U') IS NOT NULL DROP TABLE [dbo].[proj_based_tech_assessments];

IF OBJECT_ID('[dbo].[ProviderTestimonials]', 'U') IS NOT NULL DROP TABLE [dbo].[ProviderTestimonials];

IF OBJECT_ID('[dbo].[company_social_links]', 'U') IS NOT NULL DROP TABLE [dbo].[company_social_links];
IF OBJECT_ID('[dbo].[company_testimonials]', 'U') IS NOT NULL DROP TABLE [dbo].[company_testimonials];

IF OBJECT_ID('[dbo].[_OtherPriorityPopulations]', 'U') IS NOT NULL DROP TABLE [dbo].[_OtherPriorityPopulations];
IF OBJECT_ID('[dbo].[OtherPriorityPopulations]', 'U') IS NOT NULL DROP TABLE [dbo].[OtherPriorityPopulations];

IF OBJECT_ID('[dbo].[TraineeDetail]', 'U') IS NOT NULL DROP TABLE [dbo].[TraineeDetail];

IF OBJECT_ID('[dbo].[social_media_platforms]', 'U') IS NOT NULL DROP TABLE [dbo].[social_media_platforms];

COMMIT TRAN;

END TRY
BEGIN CATCH

IF @@TRANCOUNT > 0
BEGIN
    ROLLBACK TRAN;
END;
THROW

END CATCH

