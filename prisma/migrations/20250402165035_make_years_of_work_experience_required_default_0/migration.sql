BEGIN TRY

BEGIN TRAN;

-- AlterTable
ALTER TABLE [dbo].[jobseekers] ALTER COLUMN [years_work_exp] SMALLINT NOT NULL;
ALTER TABLE [dbo].[jobseekers] ADD CONSTRAINT [jobseekers_years_work_exp_df] DEFAULT 0 FOR [years_work_exp];

COMMIT TRAN;

END TRY
BEGIN CATCH

IF @@TRANCOUNT > 0
BEGIN
    ROLLBACK TRAN;
END;
THROW

END CATCH
