BEGIN TRY

    BEGIN TRAN;

-- AlterTable
    ALTER TABLE edu_providers DROP CONSTRAINT edu_providers_name_key;
    ALTER TABLE [dbo].[edu_providers] ALTER COLUMN [name] VARCHAR(255) NOT NULL;
    ALTER TABLE edu_providers
        ADD CONSTRAINT edu_providers_name_key UNIQUE (name)
    COMMIT TRAN;

END TRY
BEGIN CATCH

    IF @@TRANCOUNT > 0
        BEGIN
            ROLLBACK TRAN;
        END;
    THROW

END CATCH
