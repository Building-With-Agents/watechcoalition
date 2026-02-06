BEGIN TRY

BEGIN TRAN;

-- DropForeignKey
ALTER TABLE [dbo].[socc_to_socc_map_2010_2018] DROP CONSTRAINT [socc_to_socc_map_2010_2018_socc_code_2010_fkey];

-- CreateTable
CREATE TABLE [dbo].[socc_table_2010] (
    [socc_code] NVARCHAR(1000) NOT NULL,
    [title] NVARCHAR(1000) NOT NULL,
    [description] NVARCHAR(1000),
    CONSTRAINT [socc_table_2010_pkey] PRIMARY KEY CLUSTERED ([socc_code])
);

-- AddForeignKey
ALTER TABLE [dbo].[socc_to_socc_map_2010_2018] ADD CONSTRAINT [socc_to_socc_map_2010_2018_socc_code_2010_fkey] FOREIGN KEY ([socc_code_2010]) REFERENCES [dbo].[socc_table_2010]([socc_code]) ON DELETE NO ACTION ON UPDATE NO ACTION;

COMMIT TRAN;

END TRY
BEGIN CATCH

IF @@TRANCOUNT > 0
BEGIN
    ROLLBACK TRAN;
END;
THROW

END CATCH
