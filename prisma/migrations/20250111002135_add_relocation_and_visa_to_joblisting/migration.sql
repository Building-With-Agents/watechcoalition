
BEGIN TRY

BEGIN TRAN;


-- AlterTable
ALTER TABLE [dbo].[job_postings] ADD [offer_visa_sponsorship] BIT NOT NULL CONSTRAINT [job_postings_offer_visa_sponsorship_df] DEFAULT 0,
[relocation_services_available] BIT NOT NULL CONSTRAINT [job_postings_relocation_services_available_df] DEFAULT 0;


COMMIT TRAN;

END TRY
BEGIN CATCH

IF @@TRANCOUNT > 0
BEGIN
    ROLLBACK TRAN;
END;
THROW

END CATCH
