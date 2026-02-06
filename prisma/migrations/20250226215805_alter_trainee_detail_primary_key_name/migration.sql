BEGIN TRY

    BEGIN TRAN;

-- DropForeignKey
    ALTER TABLE [dbo].[_OtherPriorityPopulations] DROP CONSTRAINT [_OtherPriorityPopulations_B_fkey];

-- DropForeignKey
    ALTER TABLE [dbo].[TraineeDetail] DROP CONSTRAINT [fk_traineeDetail_jobseekers_education1];

-- AlterTable
    ALTER TABLE [dbo].[TraineeDetail] DROP CONSTRAINT [traineeDetail_PRIMARY];
    ALTER TABLE [dbo].[TraineeDetail] DROP COLUMN [jobseekerId];
    ALTER TABLE [dbo].[TraineeDetail] ADD [jobseekerEdId] UNIQUEIDENTIFIER NOT NULL;
    ALTER TABLE [dbo].[TraineeDetail] ADD CONSTRAINT traineeDetail_PRIMARY PRIMARY KEY NONCLUSTERED ([jobseekerEdId]);


-- AddForeignKey
    ALTER TABLE [dbo].[TraineeDetail] ADD CONSTRAINT [fk_traineeDetail_jobseekers_education1] FOREIGN KEY ([jobseekerEdId]) REFERENCES [dbo].[jobseekers_education]([jobseeker_ed_id]) ON DELETE CASCADE ON UPDATE NO ACTION;

-- AddForeignKey
    ALTER TABLE [dbo].[_OtherPriorityPopulations] ADD CONSTRAINT [_OtherPriorityPopulations_B_fkey] FOREIGN KEY ([B]) REFERENCES [dbo].[TraineeDetail]([jobseekerEdId]) ON DELETE CASCADE ON UPDATE CASCADE;

    COMMIT TRAN;

END TRY
BEGIN CATCH

    IF @@TRANCOUNT > 0
        BEGIN
            ROLLBACK TRAN;
        END;
    THROW

END CATCH
