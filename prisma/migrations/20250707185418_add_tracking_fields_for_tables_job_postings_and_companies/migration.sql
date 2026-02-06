BEGIN TRY

BEGIN TRAN;

-- AlterTable
ALTER TABLE [dbo].[companies] ADD [leadType] NVARCHAR(1000) CONSTRAINT [companies_leadType_df] DEFAULT 'cold';

-- AlterTable
ALTER TABLE [dbo].[job_postings] ADD [status] NVARCHAR(1000) CONSTRAINT [job_postings_status_df] DEFAULT 'open';

COMMIT TRAN;

END TRY
BEGIN CATCH

IF @@TRANCOUNT > 0
BEGIN
    ROLLBACK TRAN;
END;
THROW

END CATCH
