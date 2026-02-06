
-- Insert SOCC v2010 into consolidated socc table
BEGIN TRY
    BEGIN TRANSACTION;

    INSERT INTO dbo.socc (id, code, title, description, version)
    SELECT
        NEWID()            AS id,
        socc_code          AS code,
        title              AS title,
        description        AS description,
        '2010'             AS version
    FROM dbo.socc_2010;

    COMMIT TRANSACTION;
END TRY
BEGIN CATCH
    IF @@TRANCOUNT > 0
        ROLLBACK TRANSACTION;

    THROW;  -- re-raises the original error
END CATCH;

-- Insert SOCC v2018 into consolidated socc table
BEGIN TRY
    BEGIN TRANSACTION;

    INSERT INTO dbo.socc (id, code, title, description, version)
    SELECT
        NEWID()            AS id,
        socc_code          AS code,
        title              AS title,
        description        AS description,
        '2018'             AS version
    FROM dbo.socc_2018;

    COMMIT TRANSACTION;
END TRY
BEGIN CATCH
    IF @@TRANCOUNT > 0
        ROLLBACK TRANSACTION;

    THROW;  -- re-raises the original error
END CATCH;

-- delete redundant values where both v2010 and v2018 socc codes share the exact title.
BEGIN TRY
    BEGIN TRANSACTION;

    DELETE tgt
    FROM dbo.socc AS tgt
    WHERE
        tgt.version = '2010'
      AND EXISTS (
        SELECT 1
        FROM dbo.socc AS oth
        WHERE oth.code    = tgt.code
          AND oth.title   = tgt.title
          AND oth.version <> '2010'
    );

    COMMIT TRANSACTION;
END TRY
BEGIN CATCH
    IF @@TRANCOUNT > 0
        ROLLBACK TRANSACTION;
    THROW;
END CATCH;
