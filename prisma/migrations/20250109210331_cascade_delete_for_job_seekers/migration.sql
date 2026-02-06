BEGIN TRY

BEGIN TRAN;

-- DropForeignKey
ALTER TABLE [dbo].[BrandingRating] DROP CONSTRAINT [fk_branding_rating_career_prep_assessment1];

-- DropForeignKey
ALTER TABLE [dbo].[CareerPrepAssessment] DROP CONSTRAINT [fk_career_prep_app_jobseeker1];

-- DropForeignKey
ALTER TABLE [dbo].[CaseMgmt] DROP CONSTRAINT [CaseMgmt_jobseekerId_fkey];

-- DropForeignKey
ALTER TABLE [dbo].[CaseMgmtNotes] DROP CONSTRAINT [fk_case_mgmt_notes_case_mgmt1];

-- DropForeignKey
ALTER TABLE [dbo].[CybersecurityRating] DROP CONSTRAINT [fk_cybersecurity_rating_career_prep_assessment1];

-- DropForeignKey
ALTER TABLE [dbo].[DataAnalyticsRating] DROP CONSTRAINT [fk_data_analytics_rating_career_prep_assessment1];

-- DropForeignKey
ALTER TABLE [dbo].[DurableSkillsRating] DROP CONSTRAINT [fk_durable_skills_rating_career_prep_assessment1];

-- DropForeignKey
ALTER TABLE [dbo].[ITCloudRating] DROP CONSTRAINT [fk_it_cloud_rating_career_prep_assessment1];

-- DropForeignKey
ALTER TABLE [dbo].[Meeting] DROP CONSTRAINT [fk_meeting_case_mgmt1];

-- DropForeignKey
ALTER TABLE [dbo].[SoftwareDevRating] DROP CONSTRAINT [fk_software_dev_rating_career_prep_assessment1];



-- AddForeignKey
ALTER TABLE [dbo].[CareerPrepAssessment] ADD CONSTRAINT [fk_career_prep_app_jobseeker1] FOREIGN KEY ([jobseekerId]) REFERENCES [dbo].[jobseekers]([jobseeker_id]) ON DELETE CASCADE ON UPDATE NO ACTION;

-- AddForeignKey
ALTER TABLE [dbo].[CybersecurityRating] ADD CONSTRAINT [fk_cybersecurity_rating_career_prep_assessment1] FOREIGN KEY ([jobseekerId]) REFERENCES [dbo].[CareerPrepAssessment]([jobseekerId]) ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE [dbo].[DataAnalyticsRating] ADD CONSTRAINT [fk_data_analytics_rating_career_prep_assessment1] FOREIGN KEY ([jobseekerId]) REFERENCES [dbo].[CareerPrepAssessment]([jobseekerId]) ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE [dbo].[ITCloudRating] ADD CONSTRAINT [fk_it_cloud_rating_career_prep_assessment1] FOREIGN KEY ([jobseekerId]) REFERENCES [dbo].[CareerPrepAssessment]([jobseekerId]) ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE [dbo].[SoftwareDevRating] ADD CONSTRAINT [fk_software_dev_rating_career_prep_assessment1] FOREIGN KEY ([jobseekerId]) REFERENCES [dbo].[CareerPrepAssessment]([jobseekerId]) ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE [dbo].[DurableSkillsRating] ADD CONSTRAINT [fk_durable_skills_rating_career_prep_assessment1] FOREIGN KEY ([jobseekerId]) REFERENCES [dbo].[CareerPrepAssessment]([jobseekerId]) ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE [dbo].[BrandingRating] ADD CONSTRAINT [fk_branding_rating_career_prep_assessment1] FOREIGN KEY ([jobseekerId]) REFERENCES [dbo].[CareerPrepAssessment]([jobseekerId]) ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE [dbo].[CaseMgmt] ADD CONSTRAINT [CaseMgmt_jobseekerId_fkey] FOREIGN KEY ([jobseekerId]) REFERENCES [dbo].[CareerPrepAssessment]([jobseekerId]) ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE [dbo].[CaseMgmtNotes] ADD CONSTRAINT [fk_case_mgmt_notes_case_mgmt1] FOREIGN KEY ([jobseekerId]) REFERENCES [dbo].[CareerPrepAssessment]([jobseekerId]) ON DELETE CASCADE ON UPDATE NO ACTION;

-- AddForeignKey
ALTER TABLE [dbo].[Meeting] ADD CONSTRAINT [fk_meeting_case_mgmt1] FOREIGN KEY ([jobseekerId]) REFERENCES [dbo].[CaseMgmt]([jobseekerId]) ON DELETE CASCADE ON UPDATE NO ACTION;

COMMIT TRAN;

END TRY
BEGIN CATCH

IF @@TRANCOUNT > 0
BEGIN
    ROLLBACK TRAN;
END;
THROW

END CATCH
