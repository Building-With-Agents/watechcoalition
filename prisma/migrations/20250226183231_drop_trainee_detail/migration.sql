/*
  Warnings:

  - You are about to drop the `_OtherPriorityPopulations` table. If the table is not empty, all the data it contains will be lost.
  - You are about to drop the `TraineeDetail` table. If the table is not empty, all the data it contains will be lost.

*/
BEGIN TRY

BEGIN TRAN;

-- DropForeignKey
ALTER TABLE [dbo].[_OtherPriorityPopulations] DROP CONSTRAINT [_OtherPriorityPopulations_A_fkey];

-- DropForeignKey
ALTER TABLE [dbo].[_OtherPriorityPopulations] DROP CONSTRAINT [_OtherPriorityPopulations_B_fkey];

-- DropForeignKey
ALTER TABLE [dbo].[TraineeDetail] DROP CONSTRAINT [fk_traineeDetail_jobseekers1];

-- DropTable
DROP TABLE [dbo].[_OtherPriorityPopulations];

-- DropTable
DROP TABLE [dbo].[TraineeDetail];

COMMIT TRAN;

END TRY
BEGIN CATCH

IF @@TRANCOUNT > 0
BEGIN
    ROLLBACK TRAN;
END;
THROW

END CATCH
