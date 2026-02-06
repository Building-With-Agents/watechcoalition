/*
  Rename socc_to_cip_map_2018 → socc2018_to_cip2020_map
  (and its PK), preserving all data and FKs.
*/
SET NOCOUNT ON;
BEGIN TRY
    BEGIN TRANSACTION;

    -- 1) Drop the FK on cip_to_socc_map that points at the old table name
    ALTER TABLE [dbo].[cip_to_socc_map]
        DROP CONSTRAINT [cip_to_socc_map_cip_code_fkey];

    -- 2) Rename the table itself
    EXEC sp_rename
         @objname = N'dbo.socc_to_cip_map_2018',
         @newname  = N'socc2018_to_cip2020_map',
         @objtype  = N'OBJECT';

    -- 3) Rename its primary‐key constraint
    EXEC sp_rename
         @objname = N'dbo.socc_to_cip_map_2018_pkey',
         @newname  = N'socc2018_to_cip2020_map_pkey',
         @objtype  = N'OBJECT';

    -- 4) Recreate the FK now pointing at the new table name
    ALTER TABLE [dbo].[cip_to_socc_map]
        ADD CONSTRAINT [cip_to_socc_map_cip_code_fkey]
            FOREIGN KEY ([cip_code])
                REFERENCES [dbo].[cip]([cip_code])
                ON DELETE NO ACTION
                ON UPDATE CASCADE;

    COMMIT TRANSACTION;
END TRY
BEGIN CATCH
    IF @@TRANCOUNT > 0
        ROLLBACK TRANSACTION;
    THROW;
END CATCH;
