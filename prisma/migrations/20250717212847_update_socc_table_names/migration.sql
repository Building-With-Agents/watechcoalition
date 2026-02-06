/*
  Rename socc_table_2010 → socc_2010
  Rename socc_table_2018 → socc_2018
  Preserve existing data and FKs
*/
SET NOCOUNT ON;
BEGIN TRY
    BEGIN TRANSACTION;

    -- 1) Drop FKs that point at the tables you’re renaming
    ALTER TABLE [dbo].[cip_to_socc_map]
        DROP CONSTRAINT [cip_to_socc_map_socc_code_fkey];

    ALTER TABLE [dbo].[socc_to_socc_map_2010_2018]
        DROP CONSTRAINT [socc_to_socc_map_2010_2018_socc_code_2018_fkey];

    ALTER TABLE [dbo].[socc_to_socc_map_2010_2018]
        DROP CONSTRAINT [socc_to_socc_map_2010_2018_socc_code_2010_fkey];

    -- 2) Rename the tables in place
    EXEC sp_rename 'dbo.socc_table_2010', 'socc_2010';
    EXEC sp_rename 'dbo.socc_table_2018', 'socc_2018';

    -- 3) Re-create FKs against the new table names
    ALTER TABLE [dbo].[cip_to_socc_map]
        ADD CONSTRAINT [cip_to_socc_map_socc_code_fkey]
            FOREIGN KEY ([socc_code])
                REFERENCES [dbo].[socc_2018]([socc_code])
                ON DELETE NO ACTION ON UPDATE CASCADE;

    ALTER TABLE [dbo].[socc_to_socc_map_2010_2018]
        ADD CONSTRAINT [socc_to_socc_map_2010_2018_socc_code_2018_fkey]
            FOREIGN KEY ([socc_code_2018])
                REFERENCES [dbo].[socc_2018]([socc_code])
                ON DELETE NO ACTION ON UPDATE NO ACTION;

    ALTER TABLE [dbo].[socc_to_socc_map_2010_2018]
        ADD CONSTRAINT [socc_to_socc_map_2010_2018_socc_code_2010_fkey]
            FOREIGN KEY ([socc_code_2010])
                REFERENCES [dbo].[socc_2010]([socc_code])
                ON DELETE NO ACTION ON UPDATE NO ACTION;

    COMMIT TRANSACTION;
END TRY
BEGIN CATCH
    IF @@TRANCOUNT > 0 ROLLBACK TRANSACTION;
    THROW;
END CATCH;
