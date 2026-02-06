BEGIN TRY

BEGIN TRAN;

-- AlterTable
ALTER TABLE [dbo].[job_postings] ADD [minimumEducationLevel] VARCHAR(2083),
[requiredCertifications] VARCHAR(2083),
[trainingRequirements] VARCHAR(2083);

COMMIT TRAN;

END TRY
BEGIN CATCH

IF @@TRANCOUNT > 0
BEGIN
    ROLLBACK TRAN;
END;
THROW

END CATCH
