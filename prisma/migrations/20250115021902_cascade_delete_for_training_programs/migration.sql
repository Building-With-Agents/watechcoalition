
BEGIN TRY

BEGIN TRAN;

-- DropForeignKey
ALTER TABLE [dbo].[provider_program_has_skills] DROP CONSTRAINT [fk_training_program_has_skills_training_program1];

-- DropForeignKey
ALTER TABLE [dbo].[provider_programs] DROP CONSTRAINT [fk_training_program_training_provider1];

-- AddForeignKey
ALTER TABLE [dbo].[provider_program_has_skills] ADD CONSTRAINT [fk_training_program_has_skills_training_program1] FOREIGN KEY ([training_program_id]) REFERENCES [dbo].[provider_programs]([training_program_id]) ON DELETE CASCADE ON UPDATE NO ACTION;

-- AddForeignKey
ALTER TABLE [dbo].[provider_programs] ADD CONSTRAINT [fk_training_program_training_provider1] FOREIGN KEY ([edu_provider_id]) REFERENCES [dbo].[edu_providers]([id]) ON DELETE CASCADE ON UPDATE NO ACTION;

COMMIT TRAN;

END TRY
BEGIN CATCH

IF @@TRANCOUNT > 0
BEGIN
    ROLLBACK TRAN;
END;
THROW

END CATCH
