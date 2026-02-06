/*
  Warnings:

  - The primary key for the `cip_to_socc_map` table will be changed. If it partially fails, the table could be left without primary key constraint.

*/
BEGIN TRY

BEGIN TRAN;

-- AlterTable
ALTER TABLE [dbo].[cip_to_socc_map] DROP CONSTRAINT [PK_cip_to_socc_map];
ALTER TABLE [dbo].[cip_to_socc_map] ADD CONSTRAINT cip_to_socc_PRIMARY PRIMARY KEY NONCLUSTERED ([cip_code],[socc_id]);

COMMIT TRAN;

END TRY
BEGIN CATCH

IF @@TRANCOUNT > 0
BEGIN
    ROLLBACK TRAN;
END;
THROW

END CATCH
