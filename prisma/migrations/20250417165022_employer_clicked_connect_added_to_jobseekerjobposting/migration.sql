BEGIN TRY

BEGIN TRAN;

-- AlterTable
ALTER TABLE [dbo].[JobseekerJobPosting] ADD [employerClickedConnect] BIT NOT NULL CONSTRAINT [JobseekerJobPosting_employerClickedConnect_df] DEFAULT 0;

COMMIT TRAN;

END TRY
BEGIN CATCH

IF @@TRANCOUNT > 0
BEGIN
    ROLLBACK TRAN;
END;
THROW

END CATCH
