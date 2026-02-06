/*
  Warnings:

  - You are about to drop the column `cost` on the `provider_programs` table. All the data in the column will be lost.

*/
BEGIN TRY

BEGIN TRAN;

-- AlterTable
ALTER TABLE [dbo].[provider_programs] DROP COLUMN [cost];
ALTER TABLE [dbo].[provider_programs] ADD [about] TEXT,
[costSummary] TEXT,
[eduLevel] VARCHAR(45),
[faq] TEXT,
[fees] VARCHAR(25),
[getStartedUrl] VARCHAR(255),
[locationType] VARCHAR(25),
[locations] TEXT,
[programLength] TEXT,
[tuition] VARCHAR(25);

COMMIT TRAN;

END TRY
BEGIN CATCH

IF @@TRANCOUNT > 0
BEGIN
    ROLLBACK TRAN;
END;
THROW

END CATCH
