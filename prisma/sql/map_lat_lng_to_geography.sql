-- noinspection SqlDropIndexedColumnForFile

BEGIN TRY
    BEGIN TRANSACTION;

    -- Drop the index on lat/lng columns
    IF EXISTS (SELECT 1 FROM sys.indexes WHERE name = 'postal_code_lat_lng_idx' AND object_id = OBJECT_ID('postal_geo_data'))
        BEGIN
            DROP INDEX postal_code_lat_lng_idx ON postal_geo_data;
        END

    -- Add the new GEOGRAPHY column
    ALTER TABLE postal_geo_data
        ADD location GEOGRAPHY;

    -- Update existing data to populate the GEOGRAPHY column
    UPDATE postal_geo_data
    SET location = geography::Point(lat, lng, 4326);

    -- Drop the old lat/lng columns
    ALTER TABLE postal_geo_data
        DROP COLUMN lat, lng;

    -- If all operations are successful, commit the transaction
    COMMIT;
END TRY
BEGIN CATCH
    -- If any error occurs, rollback the transaction
    ROLLBACK;

    -- Output the error information
    DECLARE @ErrorMessage NVARCHAR(4000);
    DECLARE @ErrorSeverity INT;
    DECLARE @ErrorState INT;

    SELECT @ErrorMessage = ERROR_MESSAGE(),
           @ErrorSeverity = ERROR_SEVERITY(),
           @ErrorState = ERROR_STATE();

    RAISERROR (@ErrorMessage, @ErrorSeverity, @ErrorState);
END CATCH;
