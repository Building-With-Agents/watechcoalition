
BEGIN TRY

BEGIN TRAN;



-- CreateTable
CREATE TABLE [dbo].[events] (
    [id] UNIQUEIDENTIFIER NOT NULL CONSTRAINT [events_id_df] DEFAULT newid(),
    [name] VARCHAR(255) NOT NULL,
    [description] TEXT,
    [location] VARCHAR(255),
    [date] DATETIME NOT NULL,
    [zoomSignUpLink] VARCHAR(2083),
    [linkTitle] VARCHAR(255),
    [blurb] VARCHAR(255),
    [eventType] VARCHAR(50) NOT NULL,
    [createdAt] DATETIME NOT NULL CONSTRAINT [events_createdAt_df] DEFAULT CURRENT_TIMESTAMP,
    [updatedAt] DATETIME,
    [createdById] UNIQUEIDENTIFIER,
    CONSTRAINT [events_pkey] PRIMARY KEY CLUSTERED ([id])
);

-- CreateTable
CREATE TABLE [dbo].[events_on_users] (
    [id] UNIQUEIDENTIFIER NOT NULL CONSTRAINT [events_on_users_id_df] DEFAULT newid(),
    [eventId] UNIQUEIDENTIFIER NOT NULL,
    [userId] UNIQUEIDENTIFIER NOT NULL,
    CONSTRAINT [events_on_users_pkey] PRIMARY KEY CLUSTERED ([id]),
    CONSTRAINT [events_on_users_eventId_userId_key] UNIQUE NONCLUSTERED ([eventId],[userId])
);

-- AddForeignKey
ALTER TABLE [dbo].[events] ADD CONSTRAINT [events_createdById_fkey] FOREIGN KEY ([createdById]) REFERENCES [dbo].[users]([id]) ON DELETE SET NULL ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE [dbo].[events_on_users] ADD CONSTRAINT [events_on_users_eventId_fkey] FOREIGN KEY ([eventId]) REFERENCES [dbo].[events]([id]) ON DELETE NO ACTION ON UPDATE NO ACTION;

-- AddForeignKey
ALTER TABLE [dbo].[events_on_users] ADD CONSTRAINT [events_on_users_userId_fkey] FOREIGN KEY ([userId]) REFERENCES [dbo].[users]([id]) ON DELETE CASCADE ON UPDATE CASCADE;

COMMIT TRAN;

END TRY
BEGIN CATCH

IF @@TRANCOUNT > 0
BEGIN
    ROLLBACK TRAN;
END;
THROW

END CATCH
