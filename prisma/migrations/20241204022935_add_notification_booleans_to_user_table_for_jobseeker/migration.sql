BEGIN TRY

BEGIN TRAN;

-- AlterTable
ALTER TABLE [dbo].[users] ADD [sendCareerOpportunities] BIT CONSTRAINT [users_sendCareerOpportunities_df] DEFAULT 0,
[sendNewJobPosts] BIT CONSTRAINT [users_sendNewJobPosts_df] DEFAULT 0;

COMMIT TRAN;

END TRY
BEGIN CATCH

IF @@TRANCOUNT > 0
BEGIN
    ROLLBACK TRAN;
END;
THROW

END CATCH
