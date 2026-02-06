BEGIN TRY

BEGIN TRAN;

-- CreateTable
CREATE TABLE [dbo].[cip_table] (
    [cip_code] NVARCHAR(1000) NOT NULL,
    [title] NVARCHAR(1000) NOT NULL,
    [description] NVARCHAR(1000),
    CONSTRAINT [cip_table_pkey] PRIMARY KEY CLUSTERED ([cip_code])
);

-- CreateTable
CREATE TABLE [dbo].[socc_table_2018] (
    [socc_code] NVARCHAR(1000) NOT NULL,
    [title] NVARCHAR(1000) NOT NULL,
    [description] NVARCHAR(1000),
    CONSTRAINT [socc_table_2018_pkey] PRIMARY KEY CLUSTERED ([socc_code])
);

-- CreateTable
CREATE TABLE [dbo].[cip_to_socc_map] (
    [cip_code] NVARCHAR(1000) NOT NULL,
    [socc_code] NVARCHAR(1000) NOT NULL,
    CONSTRAINT [cip_to_socc_map_pkey] PRIMARY KEY CLUSTERED ([cip_code],[socc_code])
);

-- CreateTable
CREATE TABLE [dbo].[socc_to_cip_map_2018] (
    [socc_code] NVARCHAR(1000) NOT NULL,
    [cip_code] NVARCHAR(1000) NOT NULL,
    CONSTRAINT [socc_to_cip_map_2018_pkey] PRIMARY KEY CLUSTERED ([socc_code],[cip_code])
);

-- CreateTable
CREATE TABLE [dbo].[socc_to_socc_map_2010_2018] (
    [socc_code_2010] NVARCHAR(1000) NOT NULL,
    [socc_code_2018] NVARCHAR(1000) NOT NULL,
    CONSTRAINT [socc_to_socc_map_2010_2018_pkey] PRIMARY KEY CLUSTERED ([socc_code_2010],[socc_code_2018])
);

-- AddForeignKey
ALTER TABLE [dbo].[cip_to_socc_map] ADD CONSTRAINT [cip_to_socc_map_cip_code_fkey] FOREIGN KEY ([cip_code]) REFERENCES [dbo].[cip_table]([cip_code]) ON DELETE NO ACTION ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE [dbo].[cip_to_socc_map] ADD CONSTRAINT [cip_to_socc_map_socc_code_fkey] FOREIGN KEY ([socc_code]) REFERENCES [dbo].[socc_table_2018]([socc_code]) ON DELETE NO ACTION ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE [dbo].[socc_to_socc_map_2010_2018] ADD CONSTRAINT [socc_to_socc_map_2010_2018_socc_code_2010_fkey] FOREIGN KEY ([socc_code_2010]) REFERENCES [dbo].[socc_table_2018]([socc_code]) ON DELETE NO ACTION ON UPDATE NO ACTION;

-- AddForeignKey
ALTER TABLE [dbo].[socc_to_socc_map_2010_2018] ADD CONSTRAINT [socc_to_socc_map_2010_2018_socc_code_2018_fkey] FOREIGN KEY ([socc_code_2018]) REFERENCES [dbo].[socc_table_2018]([socc_code]) ON DELETE NO ACTION ON UPDATE NO ACTION;

COMMIT TRAN;

END TRY
BEGIN CATCH

IF @@TRANCOUNT > 0
BEGIN
    ROLLBACK TRAN;
END;
THROW

END CATCH
