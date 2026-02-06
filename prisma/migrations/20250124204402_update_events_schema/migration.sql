
BEGIN TRY

BEGIN TRAN;


-- AlterTable
ALTER TABLE [dbo].[events] ALTER COLUMN [location] VARCHAR(255) NOT NULL;
ALTER TABLE [dbo].[events] DROP COLUMN [linkTitle],
[zoomSignUpLink];
ALTER TABLE [dbo].[events] ADD CONSTRAINT [events_location_df] DEFAULT 'Remote' FOR [location];
ALTER TABLE [dbo].[events] ADD [duration] INT NOT NULL CONSTRAINT [events_duration_df] DEFAULT 90,
[joinMeetingLink] VARCHAR(2083),
[registrationLink] VARCHAR(2083);




COMMIT TRAN;

END TRY
BEGIN CATCH

IF @@TRANCOUNT > 0
BEGIN
    ROLLBACK TRAN;
END;
THROW

END CATCH
