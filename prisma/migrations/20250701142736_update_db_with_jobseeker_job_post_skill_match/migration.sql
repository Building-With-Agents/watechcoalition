
BEGIN TRY

BEGIN TRAN;

-- AlterTable
ALTER TABLE [dbo].[JobseekerJobPosting] ADD [analysisDate] DATETIME2,
[elevatorPitch] NTEXT,
[gabAnalysis] NTEXT,
[generatedResume] NTEXT,
[linkedInProfileUpdate] NTEXT,
[totalMatchScore] FLOAT;


-- CreateTable
CREATE TABLE [dbo].[JobseekerJobPostingSkillMatch] (
    [jobseekerJobPostingId] UNIQUEIDENTIFIER NOT NULL,
    [jobSkill] VARCHAR(255) NOT NULL,
    [jobseekerSkill] VARCHAR(255) NOT NULL,
    [matchScore] FLOAT NOT NULL,
    CONSTRAINT [JobseekerJobPostingSkillMatch_pkey] PRIMARY KEY CLUSTERED ([jobseekerJobPostingId])
);

-- AddForeignKey
ALTER TABLE [dbo].[JobseekerJobPostingSkillMatch] ADD CONSTRAINT [JobseekerJobPostingSkillMatch_jobseekerJobPostingId_fkey] FOREIGN KEY ([jobseekerJobPostingId]) REFERENCES [dbo].[JobseekerJobPosting]([id]) ON DELETE NO ACTION ON UPDATE CASCADE;

COMMIT TRAN;

END TRY
BEGIN CATCH

IF @@TRANCOUNT > 0
BEGIN
    ROLLBACK TRAN;
END;
THROW

END CATCH
