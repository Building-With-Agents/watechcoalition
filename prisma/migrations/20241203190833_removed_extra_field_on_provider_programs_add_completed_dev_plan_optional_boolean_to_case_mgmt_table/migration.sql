/*
  Warnings:
  - You are about to drop the column `target_population` on the `provider_programs` table. All the data in the column will be lost.
*/

BEGIN TRY

BEGIN TRAN;

-- AlterTable
ALTER TABLE [dbo].[CaseMgmt] ADD [completedDevPlan] BIT;

-- AlterTable
ALTER TABLE [dbo].[provider_programs] DROP COLUMN [target_population];

COMMIT TRAN;

END TRY
BEGIN CATCH

IF @@TRANCOUNT > 0
BEGIN
    ROLLBACK TRAN;
END;
THROW

END CATCH
