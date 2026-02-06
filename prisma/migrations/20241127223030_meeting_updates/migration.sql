
BEGIN TRY

BEGIN TRAN;

-- DropForeignKey
ALTER TABLE [dbo].[CaseMgmtNotes] DROP CONSTRAINT [CaseMgmtNotes_meetingId_fkey];


-- AlterTable
ALTER TABLE [dbo].[CaseMgmtNotes] DROP COLUMN [meetingId];

-- AlterTable
ALTER TABLE [dbo].[Meeting] DROP COLUMN [duration];


COMMIT TRAN;

END TRY
BEGIN CATCH

IF @@TRANCOUNT > 0
BEGIN
    ROLLBACK TRAN;
END;
THROW

END CATCH
