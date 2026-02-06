/*
  Simplify changing the PK on cip_to_socc_map by renaming in place
  – just drop the old composite key and make cip_code the sole PK.
*/

BEGIN TRY
    BEGIN TRANSACTION;

    ----------------------------------------------------------------
    -- Drop the old composite-PK constraint
    ----------------------------------------------------------------
    ALTER TABLE dbo.cip_to_socc_map
        DROP CONSTRAINT PK_cip_to_socc_map;

    ----------------------------------------------------------------
    -- Add the new primary key on cip_code only
    ----------------------------------------------------------------
    ALTER TABLE dbo.cip_to_socc_map
        ADD CONSTRAINT PK_cip_to_socc_map
            PRIMARY KEY CLUSTERED (cip_code);

    COMMIT TRANSACTION;
END TRY
BEGIN CATCH
    IF @@TRANCOUNT > 0
        ROLLBACK TRANSACTION;
    THROW;
END CATCH;
