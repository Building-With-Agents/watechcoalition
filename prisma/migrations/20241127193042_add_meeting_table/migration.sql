
BEGIN TRY

BEGIN TRAN;

-- AlterTable
ALTER TABLE [dbo].[CaseMgmtNotes] ADD [meetingId] UNIQUEIDENTIFIER;

-- CreateTable
CREATE TABLE [dbo].[Meeting] (
    [id] UNIQUEIDENTIFIER NOT NULL CONSTRAINT [Meeting_id_df] DEFAULT newid(),
    [jobseekerId] UNIQUEIDENTIFIER NOT NULL,
    [title] VARCHAR(45) NOT NULL,
    [meetingAgenda] NTEXT,
    [meetingDate] DATETIME NOT NULL,
    [duration] TIME NOT NULL,
    [updatedAt] DATETIME NOT NULL,
    CONSTRAINT [meeting_PRIMARY] PRIMARY KEY NONCLUSTERED ([id])
);

-- AddForeignKey
ALTER TABLE [dbo].[CaseMgmtNotes] ADD CONSTRAINT [CaseMgmtNotes_meetingId_fkey] FOREIGN KEY ([meetingId]) REFERENCES [dbo].[Meeting]([id]) ON DELETE SET NULL ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE [dbo].[Meeting] ADD CONSTRAINT [fk_meeting_case_mgmt1] FOREIGN KEY ([jobseekerId]) REFERENCES [dbo].[CaseMgmt]([jobseekerId]) ON DELETE NO ACTION ON UPDATE NO ACTION;

COMMIT TRAN;

END TRY
BEGIN CATCH

IF @@TRANCOUNT > 0
BEGIN
    ROLLBACK TRAN;
END;
THROW

END CATCH
