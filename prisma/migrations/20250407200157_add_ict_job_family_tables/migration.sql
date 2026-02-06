BEGIN TRY

BEGIN TRAN;

-- CreateTable
CREATE TABLE [dbo].[Training] (
    [id] UNIQUEIDENTIFIER NOT NULL CONSTRAINT [Training_id_df] DEFAULT newid(),
    [title] VARCHAR(255) NOT NULL,
    [url] VARCHAR(2083) NOT NULL,
    [provider] VARCHAR(255),
    [skillsDeveloped] TEXT,
    CONSTRAINT [Training_pkey] PRIMARY KEY CLUSTERED ([id])
);

-- CreateTable
CREATE TABLE [dbo].[PathwayTraining] (
    [id] UNIQUEIDENTIFIER NOT NULL CONSTRAINT [PathwayTraining_id_df] DEFAULT newid(),
    [pathwayId] UNIQUEIDENTIFIER,
    [trainingId] UNIQUEIDENTIFIER NOT NULL,
    CONSTRAINT [PathwayTraining_pkey] PRIMARY KEY CLUSTERED ([id]),
    CONSTRAINT [PathwayTraining_pathwayId_trainingId_key] UNIQUE NONCLUSTERED ([pathwayId],[trainingId])
);

-- CreateTable
CREATE TABLE [dbo].[JobRole] (
    [id] UNIQUEIDENTIFIER NOT NULL CONSTRAINT [JobRole_id_df] DEFAULT newid(),
    [pathwayId] UNIQUEIDENTIFIER,
    [title] VARCHAR(255) NOT NULL,
    [jobLevel] VARCHAR(20) NOT NULL,
    [jobDescription] TEXT,
    [principalTasks] TEXT,
    [principalSkills] TEXT,
    [aiImpact] TEXT,
    [keyInsights] TEXT,
    [aiTransformation] TEXT,
    CONSTRAINT [JobRole_pkey] PRIMARY KEY CLUSTERED ([id])
);

-- CreateTable
CREATE TABLE [dbo].[JobRoleTraining] (
    [id] UNIQUEIDENTIFIER NOT NULL CONSTRAINT [JobRoleTraining_id_df] DEFAULT newid(),
    [jobRoleId] UNIQUEIDENTIFIER NOT NULL,
    [trainingId] UNIQUEIDENTIFIER NOT NULL,
    CONSTRAINT [JobRoleTraining_pkey] PRIMARY KEY CLUSTERED ([id]),
    CONSTRAINT [JobRoleTraining_jobRoleId_trainingId_key] UNIQUE NONCLUSTERED ([jobRoleId],[trainingId])
);

-- CreateTable
CREATE TABLE [dbo].[JobRoleSkill] (
    [id] UNIQUEIDENTIFIER NOT NULL CONSTRAINT [JobRoleSkill_id_df] DEFAULT newid(),
    [jobRoleId] UNIQUEIDENTIFIER NOT NULL,
    [skillId] UNIQUEIDENTIFIER NOT NULL,
    [aiImpact] VARCHAR(20) NOT NULL,
    [currentProficiency] VARCHAR(50) NOT NULL,
    [futureRelevance] VARCHAR(50) NOT NULL,
    [trainingRequired] BIT NOT NULL CONSTRAINT [JobRoleSkill_trainingRequired_df] DEFAULT 0,
    CONSTRAINT [JobRoleSkill_pkey] PRIMARY KEY CLUSTERED ([id]),
    CONSTRAINT [JobRoleSkill_jobRoleId_skillId_key] UNIQUE NONCLUSTERED ([jobRoleId],[skillId])
);

-- AddForeignKey
ALTER TABLE [dbo].[PathwayTraining] ADD CONSTRAINT [PathwayTraining_trainingId_fkey] FOREIGN KEY ([trainingId]) REFERENCES [dbo].[Training]([id]) ON DELETE NO ACTION ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE [dbo].[PathwayTraining] ADD CONSTRAINT [PathwayTraining_pathwayId_fkey] FOREIGN KEY ([pathwayId]) REFERENCES [dbo].[pathways]([pathway_id]) ON DELETE SET NULL ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE [dbo].[JobRole] ADD CONSTRAINT [JobRole_pathwayId_fkey] FOREIGN KEY ([pathwayId]) REFERENCES [dbo].[pathways]([pathway_id]) ON DELETE SET NULL ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE [dbo].[JobRoleTraining] ADD CONSTRAINT [JobRoleTraining_jobRoleId_fkey] FOREIGN KEY ([jobRoleId]) REFERENCES [dbo].[JobRole]([id]) ON DELETE NO ACTION ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE [dbo].[JobRoleTraining] ADD CONSTRAINT [JobRoleTraining_trainingId_fkey] FOREIGN KEY ([trainingId]) REFERENCES [dbo].[Training]([id]) ON DELETE NO ACTION ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE [dbo].[JobRoleSkill] ADD CONSTRAINT [JobRoleSkill_jobRoleId_fkey] FOREIGN KEY ([jobRoleId]) REFERENCES [dbo].[JobRole]([id]) ON DELETE NO ACTION ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE [dbo].[JobRoleSkill] ADD CONSTRAINT [JobRoleSkill_skillId_fkey] FOREIGN KEY ([skillId]) REFERENCES [dbo].[skills]([skill_id]) ON DELETE NO ACTION ON UPDATE CASCADE;

COMMIT TRAN;

END TRY
BEGIN CATCH

IF @@TRANCOUNT > 0
BEGIN
    ROLLBACK TRAN;
END;
THROW

END CATCH
