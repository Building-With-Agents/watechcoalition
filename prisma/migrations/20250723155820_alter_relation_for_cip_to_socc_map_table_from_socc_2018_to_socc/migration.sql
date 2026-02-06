/*
  Warnings:

  - A unique constraint covering the columns `[cip_code,socc_code]` on the table `cip_to_socc_map` will be added. If there are existing duplicate values, this will fail.
*/

BEGIN TRY
    BEGIN TRANSACTION;

    ----------------------------------------------------------------
    -- 0) Stage (cip_code → real GUID) lookups for version=2018
    ----------------------------------------------------------------
    CREATE TABLE #MapFix (
                             cip_code    NVARCHAR(1000)    NOT NULL,
                             new_socc_id UNIQUEIDENTIFIER NOT NULL
    );

    INSERT INTO #MapFix (cip_code, new_socc_id)
    SELECT
        m.cip_code,
        s.id
    FROM dbo.cip_to_socc_map AS m
             INNER JOIN dbo.socc AS s
                        ON m.socc_code = s.code
                            AND s.version  = '2018';

    ----------------------------------------------------------------
    -- 1) Add a staging column of the right type (GUID)
    ----------------------------------------------------------------
    ALTER TABLE dbo.cip_to_socc_map
        ADD socc_code_guid UNIQUEIDENTIFIER NULL;

    ----------------------------------------------------------------
    -- 2) Populate it from our temp‐table
    ----------------------------------------------------------------
    UPDATE m
    SET m.socc_code_guid = f.new_socc_id
    FROM dbo.cip_to_socc_map AS m
             JOIN #MapFix AS f
                  ON m.cip_code = f.cip_code;

    ----------------------------------------------------------------
    -- 3) Drop old constraints & column
    ----------------------------------------------------------------
    ALTER TABLE dbo.cip_to_socc_map
        DROP CONSTRAINT [cip_to_socc_map_socc_code_fkey];

    ALTER TABLE dbo.cip_to_socc_map
        DROP CONSTRAINT [cip_to_socc_map_pkey];

    ALTER TABLE dbo.cip_to_socc_map
        DROP COLUMN socc_code;

    ----------------------------------------------------------------
    -- 4) Rename and tighten up the new column
    ----------------------------------------------------------------
    EXEC sp_rename
         N'dbo.cip_to_socc_map.socc_code_guid',
         N'socc_code',
         N'COLUMN';

    ALTER TABLE dbo.cip_to_socc_map
        ALTER COLUMN socc_code UNIQUEIDENTIFIER NOT NULL;

    ----------------------------------------------------------------
    -- 5) Remove any duplicate (cip_code, socc_code) rows
    ----------------------------------------------------------------
    ;WITH Dupes AS (
        SELECT
            cip_code,
            socc_code,
            ROW_NUMBER() OVER (
                PARTITION BY cip_code, socc_code
                ORDER BY (SELECT NULL)
                ) AS rn
        FROM dbo.cip_to_socc_map
    )
     DELETE m
     FROM dbo.cip_to_socc_map AS m
              JOIN Dupes AS d
                   ON m.cip_code  = d.cip_code
                       AND m.socc_code = d.socc_code
     WHERE d.rn > 1;

    ----------------------------------------------------------------
    -- 6) Recreate PK and FK on the correct types
    ----------------------------------------------------------------
    ALTER TABLE dbo.cip_to_socc_map
        ADD CONSTRAINT [cip_to_socc_map_pkey]
            PRIMARY KEY CLUSTERED (cip_code, socc_code);

    ALTER TABLE dbo.cip_to_socc_map
        ADD CONSTRAINT [cip_to_socc_map_socc_code_fkey]
            FOREIGN KEY (socc_code)
                REFERENCES dbo.socc(id)
                ON UPDATE CASCADE
                ON DELETE NO ACTION;

    ----------------------------------------------------------------
    -- 7) Clean up
    ----------------------------------------------------------------
    DROP TABLE #MapFix;

    COMMIT TRANSACTION;
END TRY
BEGIN CATCH
    IF @@TRANCOUNT > 0
        ROLLBACK TRANSACTION;

    IF OBJECT_ID('tempdb..#MapFix') IS NOT NULL
        DROP TABLE #MapFix;

    THROW;
END CATCH;
