BEGIN TRY

BEGIN TRAN;

-- AlterTable
ALTER TABLE [dbo].[JobseekerJobPostingSkillMatch] DROP CONSTRAINT [JobseekerJobPostingSkillMatch_pkey];
ALTER TABLE [dbo].[JobseekerJobPostingSkillMatch] ADD CONSTRAINT JobseekerJobPostingSkillMatch_pkey PRIMARY KEY CLUSTERED ([jobseekerJobPostingId],[jobSkill]);

COMMIT TRAN;

END TRY
BEGIN CATCH

IF @@TRANCOUNT > 0
BEGIN
    ROLLBACK TRAN;
END;
THROW

END CATCH
