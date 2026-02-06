BEGIN TRY

BEGIN TRAN;

-- AlterTable
EXEC SP_RENAME N'dbo.cip_table_pkey', N'cip_pkey';

-- AlterTable
EXEC SP_RENAME N'dbo.socc_table_2010_pkey', N'socc_2010_pkey';

-- AlterTable
EXEC SP_RENAME N'dbo.socc_table_2018_pkey', N'socc_2018_pkey';

-- AddForeignKey
ALTER TABLE [dbo].[socc2018_to_cip2020_map] ADD CONSTRAINT [socc2018_to_cip2020_map_socc_code_fkey] FOREIGN KEY ([socc_code]) REFERENCES [dbo].[socc_2018]([socc_code]) ON DELETE NO ACTION ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE [dbo].[socc2018_to_cip2020_map] ADD CONSTRAINT [socc2018_to_cip2020_map_cip_code_fkey] FOREIGN KEY ([cip_code]) REFERENCES [dbo].[cip]([cip_code]) ON DELETE NO ACTION ON UPDATE CASCADE;

COMMIT TRAN;

END TRY
BEGIN CATCH

IF @@TRANCOUNT > 0
BEGIN
    ROLLBACK TRAN;
END;
THROW

END CATCH
