BEGIN TRY

BEGIN TRAN;

-- CreateTable
CREATE TABLE [dbo].[TraineeDetail] (
    [jobseekerId] UNIQUEIDENTIFIER NOT NULL,
    [isVerified] BIT NOT NULL CONSTRAINT [DF_trainee_isVerified] DEFAULT 0,
    [firstName] VARCHAR(45) NOT NULL,
    [lastName] VARCHAR(45) NOT NULL,
    [programTitle] VARCHAR(45) NOT NULL,
    [enrollmentStatus] VARCHAR(45) NOT NULL,
    [startDate] DATE NOT NULL,
    [exitDate] DATE NOT NULL,
    [nonCompletionReason] VARCHAR(45),
    CONSTRAINT [traineeDetail_PRIMARY] PRIMARY KEY NONCLUSTERED ([jobseekerId])
);

-- CreateTable
CREATE TABLE [dbo].[_OtherPriorityPopulations] (
    [A] UNIQUEIDENTIFIER NOT NULL,
    [B] UNIQUEIDENTIFIER NOT NULL,
    CONSTRAINT [_OtherPriorityPopulations_AB_unique] UNIQUE NONCLUSTERED ([A],[B])
);

-- CreateIndex
CREATE NONCLUSTERED INDEX [_OtherPriorityPopulations_B_index] ON [dbo].[_OtherPriorityPopulations]([B]);

-- AddForeignKey
ALTER TABLE [dbo].[TraineeDetail] ADD CONSTRAINT [fk_traineeDetail_jobseekers_education1] FOREIGN KEY ([jobseekerId]) REFERENCES [dbo].[jobseekers_education]([jobseeker_ed_id]) ON DELETE CASCADE ON UPDATE NO ACTION;

-- AddForeignKey
ALTER TABLE [dbo].[_OtherPriorityPopulations] ADD CONSTRAINT [_OtherPriorityPopulations_A_fkey] FOREIGN KEY ([A]) REFERENCES [dbo].[OtherPriorityPopulations]([id]) ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE [dbo].[_OtherPriorityPopulations] ADD CONSTRAINT [_OtherPriorityPopulations_B_fkey] FOREIGN KEY ([B]) REFERENCES [dbo].[TraineeDetail]([jobseekerId]) ON DELETE CASCADE ON UPDATE CASCADE;

COMMIT TRAN;

END TRY
BEGIN CATCH

IF @@TRANCOUNT > 0
BEGIN
    ROLLBACK TRAN;
END;
THROW

END CATCH
