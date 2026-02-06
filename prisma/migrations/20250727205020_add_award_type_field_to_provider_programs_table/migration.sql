BEGIN TRY

BEGIN TRAN;

-- AlterTable
EXEC SP_RENAME N'dbo.PK_cip', N'cip_pkey';

-- AlterTable
ALTER TABLE [dbo].[provider_programs] ADD [awardType] NVARCHAR(100);

COMMIT TRAN;

END TRY
BEGIN CATCH

IF @@TRANCOUNT > 0
BEGIN
    ROLLBACK TRAN;
END;
THROW

END CATCH
