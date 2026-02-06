
BEGIN TRY

BEGIN TRAN;



-- AlterTable
ALTER TABLE [dbo].[job_postings] ADD [is_apprenticeship] BIT NOT NULL CONSTRAINT [job_postings_is_apprenticeship_df] DEFAULT 0;


COMMIT TRAN;

END TRY
BEGIN CATCH

IF @@TRANCOUNT > 0
BEGIN
    ROLLBACK TRAN;
END;
THROW

END CATCH
