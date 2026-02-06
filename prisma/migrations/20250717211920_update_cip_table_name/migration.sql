-- prisma/migrations/.../migration.sql
SET NOCOUNT ON;
BEGIN TRANSACTION;

-- 1) drop the existing FK
ALTER TABLE [dbo].[cip_to_socc_map]
    DROP CONSTRAINT [cip_to_socc_map_cip_code_fkey];

-- 2) rename the table
EXEC sp_rename 'dbo.cip_table', 'cip';

-- 3) re-add the FK against the new table name
ALTER TABLE [dbo].[cip_to_socc_map]
    ADD CONSTRAINT [cip_to_socc_map_cip_code_fkey]
        FOREIGN KEY ([cip_code])
            REFERENCES [dbo].[cip]([cip_code])
            ON UPDATE NO ACTION
            ON DELETE NO ACTION;

COMMIT TRANSACTION;
