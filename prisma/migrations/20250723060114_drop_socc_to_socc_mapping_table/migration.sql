
BEGIN TRY

BEGIN TRAN;

-- DropForeignKey
ALTER TABLE [dbo].[socc_to_socc_map_2010_2018] DROP CONSTRAINT [socc_to_socc_map_2010_2018_socc_code_2010_fkey];

-- DropForeignKey
ALTER TABLE [dbo].[socc_to_socc_map_2010_2018] DROP CONSTRAINT [socc_to_socc_map_2010_2018_socc_code_2018_fkey];

-- DropTable
DROP TABLE [dbo].[socc_to_socc_map_2010_2018];

COMMIT TRAN;

END TRY
BEGIN CATCH

IF @@TRANCOUNT > 0
BEGIN
    ROLLBACK TRAN;
END;
THROW

END CATCH
