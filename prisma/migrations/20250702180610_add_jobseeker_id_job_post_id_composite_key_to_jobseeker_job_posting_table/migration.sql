BEGIN TRY

BEGIN TRAN;

-- CreateIndex
ALTER TABLE [dbo].[JobseekerJobPosting] ADD CONSTRAINT [JobseekerJobPosting_jobseekerId_jobPostId_key] UNIQUE NONCLUSTERED ([jobseekerId], [jobPostId]);

COMMIT TRAN;

END TRY
BEGIN CATCH

IF @@TRANCOUNT > 0
BEGIN
    ROLLBACK TRAN;
END;
THROW

END CATCH
