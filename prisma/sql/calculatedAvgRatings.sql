BEGIN TRY

    BEGIN TRAN;

    -- CybersecurityRating Table
    IF EXISTS (
        SELECT 1
        FROM INFORMATION_SCHEMA.COLUMNS
        WHERE TABLE_NAME = 'CybersecurityRating' AND COLUMN_NAME = 'overallAverage'
    )
        BEGIN
            ALTER TABLE CybersecurityRating DROP COLUMN overallAverage;
        END

    ALTER TABLE CybersecurityRating
        ADD overallAverage AS (
            CAST(
                    ROUND(
                            (networking + projectManagement + securityTools + operatingSystems + programming +
                             cryptography + cloudSecurity + incidentResponse + dataSecurity + technicalSupport +
                             computationalThinking + apiUsage) / 12.0, 2
                    ) AS DECIMAL(3, 2)
            )
            );

    -- DataAnalyticsRating Table
    IF EXISTS (
        SELECT 1
        FROM INFORMATION_SCHEMA.COLUMNS
        WHERE TABLE_NAME = 'DataAnalyticsRating' AND COLUMN_NAME = 'overallAverage'
    )
        BEGIN
            ALTER TABLE DataAnalyticsRating DROP COLUMN overallAverage;
        END

    ALTER TABLE DataAnalyticsRating
        ADD overallAverage AS (
            CAST(
                    ROUND(
                            (dataAnalysis + sqlProgramming + pythonPackages + dataScience + dataEngineering +
                             tableau + machineLearning + rProgramming + projectManagement + dataVisualization +
                             dataStructures + bigOComplexity + sortingAlgorithms + databases +
                             computationalThinking) / 15.0, 2
                    ) AS DECIMAL(3, 2)
            )
            );

    -- ITCloudRating Table
    IF EXISTS (
        SELECT 1
        FROM INFORMATION_SCHEMA.COLUMNS
        WHERE TABLE_NAME = 'ITCloudRating' AND COLUMN_NAME = 'overallAverage'
    )
        BEGIN
            ALTER TABLE ITCloudRating DROP COLUMN overallAverage;
        END

    ALTER TABLE ITCloudRating
        ADD overallAverage AS (
            CAST(
                    ROUND(
                            (techSupport + activeDirectory + projectManagement + helpDeskSupport + windowsServers +
                             sqlProgramming + computerHardware + operatingSystems + systemAdmin + networkAdmin +
                             virtualization + coreCloudServices + apiUsage + httpResponseCodes +
                             computationalThinking) / 15.0, 2
                    ) AS DECIMAL(3, 2)
            )
            );

    -- SoftwareDevRating Table
    IF EXISTS (
        SELECT 1
        FROM INFORMATION_SCHEMA.COLUMNS
        WHERE TABLE_NAME = 'SoftwareDevRating' AND COLUMN_NAME = 'overallAverage'
    )
        BEGIN
            ALTER TABLE SoftwareDevRating DROP COLUMN overallAverage;
        END

    ALTER TABLE SoftwareDevRating
        ADD overallAverage AS (
            CAST(
                    ROUND(
                            (softwareEngineering + softwareDevelopmentLifecycle + programmingLanguages +
                             dataStructuresAndAlgorithms +
                             softwareArchitecture + versionControl + databaseManagement + devOps + cloudComputing +
                             conceptualSystemsThinking + problemSolving + fundamentalCodingConcepts + debugging +
                             computationalThinking + softwareOptimization) / 15.0, 2
                    ) AS DECIMAL(3, 2)
            )
            );

    -- DurableSkillsRating Table
    IF EXISTS (
        SELECT 1
        FROM INFORMATION_SCHEMA.COLUMNS
        WHERE TABLE_NAME = 'DurableSkillsRating' AND COLUMN_NAME = 'overallAverage'
    )
        BEGIN
            ALTER TABLE DurableSkillsRating DROP COLUMN overallAverage;
        END

    ALTER TABLE DurableSkillsRating
        ADD overallAverage AS (
            CAST(
                    ROUND(
                            (emotionManagement + empathy + goalSetting + timeManagement + adaptability +
                             criticalThinking + creativity + resilience + communication + activeListening +
                             conflictResolution + nonverbalCommunication + teamwork + trustBuilding +
                             leadership + perspectiveTaking + culturalAwareness + relationshipBuilding +
                             documentationSkills) / 19.0, 2
                    ) AS DECIMAL(3, 2)
            )
            );

    -- BrandingRating Table
    IF EXISTS (
        SELECT 1
        FROM INFORMATION_SCHEMA.COLUMNS
        WHERE TABLE_NAME = 'BrandingRating' AND COLUMN_NAME = 'overallAverage'
    )
        BEGIN
            ALTER TABLE BrandingRating DROP COLUMN overallAverage;
        END

    ALTER TABLE BrandingRating
        ADD overallAverage AS (
            CAST(
                    ROUND(
                            (personalBrand + onlinePresence + elevatorPitch + resumeEffectiveness +
                             coverLetterEffectiveness + interviewExperience + responseTechnique +
                             followUpImportance + onlineNetworking + eventNetworking +
                             relationshipManagement + jobSearchStrategy + materialDistribution +
                             networkingTechniques + onboardingBestPractices + developmentPlan +
                             mentorship) / 17.0, 2
                    ) AS DECIMAL(3, 2)
            )
            );

    COMMIT TRAN;

END TRY
BEGIN CATCH

    IF @@TRANCOUNT > 0
        BEGIN
            ROLLBACK TRAN;
        END;
    THROW;

END CATCH;
