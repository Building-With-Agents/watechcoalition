BEGIN TRY

BEGIN TRAN;

-- AlterTable
ALTER TABLE [dbo].[companies] DROP CONSTRAINT [companies_leadType_df];
ALTER TABLE [dbo].[companies] DROP COLUMN [leadType];
ALTER TABLE [dbo].[companies] ADD [engagementType] NVARCHAR(1000) CONSTRAINT [companies_engagementType_df] DEFAULT 'Lead';

COMMIT TRAN;

END TRY
BEGIN CATCH

IF @@TRANCOUNT > 0
BEGIN
    ROLLBACK TRAN;
END;
THROW

END CATCH
