BEGIN TRY

    BEGIN TRAN;

-- Conditionally Drop Constraint
    IF EXISTS (
        SELECT 1
        FROM sys.default_constraints
        WHERE parent_object_id = OBJECT_ID('[dbo].[JobseekerJobPosting]')
          AND name = 'JobseekerJobPosting_jobStatus_df'
    )
        BEGIN
            ALTER TABLE [dbo].[JobseekerJobPosting] DROP CONSTRAINT [JobseekerJobPosting_jobStatus_df];
        END;

-- Add or Modify Constraints
    ALTER TABLE [dbo].[JobseekerJobPosting] ADD CONSTRAINT [JobseekerJobPosting_jobStatus_df] DEFAULT 'Not Selected' FOR [jobStatus];
    ALTER TABLE [dbo].[JobseekerJobPosting] ADD [isBookmarked] BIT CONSTRAINT [JobseekerJobPosting_isBookmarked_df] DEFAULT 0;

    COMMIT TRAN;

END TRY
BEGIN CATCH

    IF @@TRANCOUNT > 0
        BEGIN
            ROLLBACK TRAN;
        END;
    THROW;

END CATCH
