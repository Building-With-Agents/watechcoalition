BEGIN TRY

    BEGIN TRAN;

-- Drop the dependent default constraint
    ALTER TABLE [dbo].[employers] DROP CONSTRAINT [employers_has_agreed_terms_df];

-- Drop the column
    ALTER TABLE [dbo].[employers] DROP COLUMN [has_agreed_terms];

    COMMIT TRAN;

END TRY
BEGIN CATCH

    IF @@TRANCOUNT > 0
        BEGIN
            ROLLBACK TRAN;
        END;
    THROW;

END CATCH
