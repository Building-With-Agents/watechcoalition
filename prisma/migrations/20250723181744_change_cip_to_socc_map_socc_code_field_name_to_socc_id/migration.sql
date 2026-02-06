/*
  This migration simply renames:
    - cip.cip_code       → cip.code
    - cip_to_socc_map.socc_code → cip_to_socc_map.socc_id

  Then re-wires PKs and FKs to use the new names.
*/

BEGIN TRY
    BEGIN TRANSACTION;

    ----------------------------------------------------------------
    -- 1) Drop FKs that reference the soon-to-be-renamed columns
    ----------------------------------------------------------------
    ALTER TABLE dbo.[provider_programs]
        DROP CONSTRAINT [provider_programs_cipCode_fkey];

    ALTER TABLE dbo.[cip_to_socc_map]
        DROP CONSTRAINT [cip_to_socc_map_cip_code_fkey];
    ALTER TABLE dbo.[cip_to_socc_map]
        DROP CONSTRAINT [cip_to_socc_map_socc_code_fkey];

    ALTER TABLE dbo.[socc2018_to_cip2020_map]
        DROP CONSTRAINT [socc2018_to_cip2020_map_cip_code_fkey];

    ----------------------------------------------------------------
    -- 2) Rename the columns in place
    ----------------------------------------------------------------
    EXEC sp_rename
         @objname = N'dbo.cip.cip_code',
         @newname  = N'code',
         @objtype  = N'COLUMN';

    EXEC sp_rename
         @objname = N'dbo.cip_to_socc_map.socc_code',
         @newname  = N'socc_id',
         @objtype  = N'COLUMN';

    -- (cip_to_socc_map.cip_code stays the same)

    ----------------------------------------------------------------
    -- 3) Drop & re-create PKs so they point at the new names
    ----------------------------------------------------------------
    -- CIP table
    ALTER TABLE dbo.cip
        DROP CONSTRAINT [cip_pkey];
    ALTER TABLE dbo.cip
        ADD CONSTRAINT [PK_cip]
            PRIMARY KEY CLUSTERED ([code]);

    -- CIP-TO-SOCC map table (composite)
    ALTER TABLE dbo.cip_to_socc_map
        DROP CONSTRAINT [cip_to_socc_map_pkey];
    ALTER TABLE dbo.cip_to_socc_map
        ADD CONSTRAINT [PK_cip_to_socc_map]
            PRIMARY KEY CLUSTERED ([cip_code],[socc_id]);

    ----------------------------------------------------------------
    -- 4) Re-add FKs against the renamed columns
    ----------------------------------------------------------------
    ALTER TABLE dbo.[provider_programs]
        ADD CONSTRAINT [provider_programs_cipCode_fkey]
            FOREIGN KEY([cipCode])
                REFERENCES dbo.cip([code])
                ON DELETE SET NULL
                ON UPDATE CASCADE;

    ALTER TABLE dbo.[cip_to_socc_map]
        ADD CONSTRAINT [cip_to_socc_map_cip_code_fkey]
            FOREIGN KEY([cip_code])
                REFERENCES dbo.cip([code])
                ON DELETE NO ACTION
                ON UPDATE CASCADE;

    ALTER TABLE dbo.[cip_to_socc_map]
        ADD CONSTRAINT [cip_to_socc_map_socc_id_fkey]
            FOREIGN KEY([socc_id])
                REFERENCES dbo.socc([id])
                ON DELETE NO ACTION
                ON UPDATE CASCADE;

    ALTER TABLE dbo.[socc2018_to_cip2020_map]
        ADD CONSTRAINT [socc2018_to_cip2020_map_cip_code_fkey]
            FOREIGN KEY([cip_code])
                REFERENCES dbo.cip([code])
                ON DELETE NO ACTION
                ON UPDATE CASCADE;

    COMMIT TRANSACTION;
END TRY
BEGIN CATCH
    IF @@TRANCOUNT > 0
        ROLLBACK TRANSACTION;
    THROW;
END CATCH;
