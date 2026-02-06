
BEGIN TRY

BEGIN TRAN;

    -- Drop the unwanted primary key constraint
    IF EXISTS (
        SELECT 1
        FROM sys.key_constraints kc
        WHERE kc.name = 'PK_cip_to_socc_map'
          AND kc.parent_object_id = OBJECT_ID('dbo.cip_to_socc_map')
    )
        BEGIN
            ALTER TABLE dbo.cip_to_socc_map
                DROP CONSTRAINT PK_cip_to_socc_map;
        END

COMMIT TRAN;

END TRY
BEGIN CATCH

IF @@TRANCOUNT > 0
BEGIN
    ROLLBACK TRAN;
END;
THROW

END CATCH
