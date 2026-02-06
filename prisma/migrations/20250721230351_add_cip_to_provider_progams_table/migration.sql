BEGIN TRY

BEGIN TRAN;

-- AlterTable
ALTER TABLE [dbo].[provider_programs] ADD [cipCode] NVARCHAR(1000);

-- AddForeignKey
ALTER TABLE [dbo].[provider_programs] ADD CONSTRAINT [provider_programs_cipCode_fkey] FOREIGN KEY ([cipCode]) REFERENCES [dbo].[cip]([cip_code]) ON DELETE SET NULL ON UPDATE CASCADE;

COMMIT TRAN;

END TRY
BEGIN CATCH

IF @@TRANCOUNT > 0
BEGIN
    ROLLBACK TRAN;
END;
THROW

END CATCH
