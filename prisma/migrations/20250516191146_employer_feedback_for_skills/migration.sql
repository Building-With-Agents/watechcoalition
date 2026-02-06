/*
  Warnings:

  - You are about to alter the column `overallAverage` on the `BrandingRating` table. The data in that column could be lost. The data in that column will be cast from `Decimal(3,2)` to `Float`.
  - You are about to alter the column `overallAverage` on the `CybersecurityRating` table. The data in that column could be lost. The data in that column will be cast from `Decimal(3,2)` to `Float`.
  - You are about to alter the column `overallAverage` on the `DataAnalyticsRating` table. The data in that column could be lost. The data in that column will be cast from `Decimal(3,2)` to `Float`.
  - You are about to alter the column `overallAverage` on the `DurableSkillsRating` table. The data in that column could be lost. The data in that column will be cast from `Decimal(3,2)` to `Float`.
  - You are about to alter the column `overallAverage` on the `ITCloudRating` table. The data in that column could be lost. The data in that column will be cast from `Decimal(3,2)` to `Float`.
  - You are about to alter the column `overallAverage` on the `SoftwareDevRating` table. The data in that column could be lost. The data in that column will be cast from `Decimal(3,2)` to `Float`.

*/
BEGIN TRY

BEGIN TRAN;


-- CreateTable
CREATE TABLE [dbo].[EmployerJobRoleFeedBack] (
    [id] UNIQUEIDENTIFIER NOT NULL CONSTRAINT [EmployerJobRoleFeedBack_id_df] DEFAULT newid(),
    [jobRoleId] UNIQUEIDENTIFIER NOT NULL,
    [skillId] UNIQUEIDENTIFIER NOT NULL,
    [likertRating] INT NOT NULL,
    [submiterid] UNIQUEIDENTIFIER NOT NULL,
    CONSTRAINT [EmployerJobRoleFeedBack_pkey] PRIMARY KEY CLUSTERED ([id])
);

-- AddForeignKey
ALTER TABLE [dbo].[EmployerJobRoleFeedBack] ADD CONSTRAINT [EmployerJobRoleFeedBack_submiterid_fkey] FOREIGN KEY ([submiterid]) REFERENCES [dbo].[users]([id]) ON DELETE NO ACTION ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE [dbo].[EmployerJobRoleFeedBack] ADD CONSTRAINT [EmployerJobRoleFeedBack_skillId_fkey] FOREIGN KEY ([skillId]) REFERENCES [dbo].[skills]([skill_id]) ON DELETE NO ACTION ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE [dbo].[EmployerJobRoleFeedBack] ADD CONSTRAINT [EmployerJobRoleFeedBack_jobRoleId_fkey] FOREIGN KEY ([jobRoleId]) REFERENCES [dbo].[JobRole]([id]) ON DELETE NO ACTION ON UPDATE CASCADE;

COMMIT TRAN;

END TRY
BEGIN CATCH

IF @@TRANCOUNT > 0
BEGIN
    ROLLBACK TRAN;
END;
THROW

END CATCH
