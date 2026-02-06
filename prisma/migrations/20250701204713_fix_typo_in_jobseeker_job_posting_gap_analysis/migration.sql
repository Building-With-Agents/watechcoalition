BEGIN TRY

BEGIN TRAN;

-- AlterTable
ALTER TABLE [dbo].[JobseekerJobPosting] DROP COLUMN [gabAnalysis];
ALTER TABLE [dbo].[JobseekerJobPosting] ADD [gapAnalysis] NTEXT;

COMMIT TRAN;

END TRY
BEGIN CATCH

IF @@TRANCOUNT > 0
BEGIN
    ROLLBACK TRAN;
END;
THROW

END CATCH
