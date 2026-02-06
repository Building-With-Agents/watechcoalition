BEGIN TRY

    BEGIN TRAN;

-- CreateTable
    CREATE TABLE [dbo].[users] (
                                   [id] UNIQUEIDENTIFIER NOT NULL CONSTRAINT [users_id_df] DEFAULT newid(),
                                   [role] VARCHAR(255) NOT NULL,
                                   [first_name] VARCHAR(255),
                                   [last_name] VARCHAR(255),
                                   [birthdate] DATETIME,
                                   [email] VARCHAR(255) NOT NULL,
                                   [email_verified] DATETIME,
                                   [phoneCountryCode] VARCHAR(100),
                                   [phone] VARCHAR(16),
                                   [zip] VARCHAR(5),
                                   [photo_url] VARCHAR(255),
                                   [has_agreed_terms] BIT NOT NULL CONSTRAINT [users_has_agreed_terms_df] DEFAULT 0,
                                   [created_at] DATETIME NOT NULL,
                                   [updated_at] DATETIME,
                                   [is_marked_deletion] DATETIME,
                                   CONSTRAINT [contacts_PRIMARY] PRIMARY KEY NONCLUSTERED ([id]),
                                   CONSTRAINT [users_id_key] UNIQUE NONCLUSTERED ([id]),
                                   CONSTRAINT [users_email_key] UNIQUE NONCLUSTERED ([email])
    );

-- CreateTable
    CREATE TABLE [dbo].[Account] (
                                     [id] UNIQUEIDENTIFIER NOT NULL,
                                     [user_id] UNIQUEIDENTIFIER NOT NULL,
                                     [type] NVARCHAR(255) NOT NULL,
                                     [provider] NVARCHAR(255) NOT NULL,
                                     [provider_account_id] NVARCHAR(255) NOT NULL,
                                     [refresh_token] NVARCHAR(max),
                                     [access_token] NVARCHAR(max),
                                     [expires_at] INT,
                                     [token_type] NVARCHAR(255),
                                     [scope] NVARCHAR(255),
                                     [id_token] NVARCHAR(max),
                                     [session_state] NVARCHAR(255),
                                     [refresh_token_expires_in] INT,
                                     [createdAt] DATETIME NOT NULL CONSTRAINT [Account_createdAt_df] DEFAULT CURRENT_TIMESTAMP,
                                     [updatedAt] DATETIME NOT NULL,
                                     CONSTRAINT [Account_pkey] PRIMARY KEY CLUSTERED ([id]),
                                     CONSTRAINT [Account_provider_provider_account_id_key] UNIQUE NONCLUSTERED ([provider],[provider_account_id])
    );

-- CreateTable
    CREATE TABLE [dbo].[Session] (
                                     [id] UNIQUEIDENTIFIER NOT NULL,
                                     [sessionToken] NVARCHAR(255) NOT NULL,
                                     [userId] UNIQUEIDENTIFIER NOT NULL,
                                     [expires] DATETIME NOT NULL,
                                     [createdAt] DATETIME NOT NULL CONSTRAINT [Session_createdAt_df] DEFAULT CURRENT_TIMESTAMP,
                                     [updatedAt] DATETIME NOT NULL,
                                     CONSTRAINT [Session_pkey] PRIMARY KEY CLUSTERED ([id]),
                                     CONSTRAINT [Session_sessionToken_key] UNIQUE NONCLUSTERED ([sessionToken])
    );

-- CreateTable
    CREATE TABLE [dbo].[VerificationToken] (
                                               [identifier] NVARCHAR(255) NOT NULL,
                                               [token] NVARCHAR(255) NOT NULL,
                                               [expires] DATETIME NOT NULL,
                                               CONSTRAINT [VerificationToken_identifier_token_key] UNIQUE NONCLUSTERED ([identifier],[token])
    );

-- CreateTable
    CREATE TABLE [dbo].[Authenticator] (
                                           [credentialId] NVARCHAR(255) NOT NULL,
                                           [userId] UNIQUEIDENTIFIER NOT NULL,
                                           [providerAccountId] NVARCHAR(255) NOT NULL,
                                           [credentialPublicKey] NVARCHAR(max) NOT NULL,
                                           [counter] INT NOT NULL,
                                           [credentialDeviceType] NVARCHAR(255) NOT NULL,
                                           [credentialBackedUp] BIT NOT NULL,
                                           [transports] NVARCHAR(255),
                                           CONSTRAINT [Authenticator_pkey] PRIMARY KEY CLUSTERED ([userId],[credentialId]),
                                           CONSTRAINT [Authenticator_credentialId_key] UNIQUE NONCLUSTERED ([credentialId])
    );

-- CreateTable
    CREATE TABLE [dbo].[certificates] (
                                          [certification_id] UNIQUEIDENTIFIER NOT NULL,
                                          [jobseeker_id] UNIQUEIDENTIFIER NOT NULL,
                                          [name] VARCHAR(255) NOT NULL,
                                          [logo_url] VARCHAR(255),
                                          [issuing_org] VARCHAR(255) NOT NULL,
                                          [credential_id] VARCHAR(255),
                                          [credential_url] VARCHAR(255),
                                          [status] VARCHAR(45),
                                          [issue_date] DATETIME,
                                          [expiration_date] DATETIME,
                                          [description] NTEXT,
                                          CONSTRAINT [certificates_PRIMARY] PRIMARY KEY NONCLUSTERED ([certification_id])
    );

-- CreateTable
    CREATE TABLE [dbo].[cfa_admin] (
                                       [admin_id] UNIQUEIDENTIFIER NOT NULL,
                                       [user_id] UNIQUEIDENTIFIER NOT NULL,
                                       CONSTRAINT [cfa_admin_PRIMARY] PRIMARY KEY NONCLUSTERED ([admin_id])
    );

-- CreateTable
    CREATE TABLE [dbo].[companies] (
                                       [company_id] UNIQUEIDENTIFIER NOT NULL,
                                       [industry_sector_id] UNIQUEIDENTIFIER,
                                       [company_name] VARCHAR(255) NOT NULL,
                                       [company_logo_url] VARCHAR(255),
                                       [about_us] VARCHAR(255) NOT NULL,
                                       [company_email] VARCHAR(255) NOT NULL,
                                       [year_founded] INT NOT NULL,
                                       [company_website_url] VARCHAR(255),
                                       [company_video_url] VARCHAR(255),
                                       [company_phone] VARCHAR(16),
                                       [company_mission] VARCHAR(255),
                                       [company_vision] VARCHAR(255),
                                       [size] VARCHAR(45) NOT NULL CONSTRAINT [DF__companies__size__3F466844] DEFAULT 'less than 10',
                                       [estimated_annual_hires] INT,
                                       [is_approved] BIT NOT NULL CONSTRAINT [DF_companies__is_approved] DEFAULT 0,
                                       [createdBy] UNIQUEIDENTIFIER,
                                       CONSTRAINT [companies_PRIMARY] PRIMARY KEY NONCLUSTERED ([company_id]),
                                       CONSTRAINT [companies_company_name_key] UNIQUE NONCLUSTERED ([company_name])
    );

-- CreateTable
    CREATE TABLE [dbo].[bookmarked_jobseekers] (
                                                   [id] UNIQUEIDENTIFIER NOT NULL,
                                                   [jobseeker_id] UNIQUEIDENTIFIER NOT NULL,
                                                   [company_id] UNIQUEIDENTIFIER NOT NULL,
                                                   [employer_id] UNIQUEIDENTIFIER,
                                                   CONSTRAINT [bookmarked_jobseekers_PRIMARY] PRIMARY KEY NONCLUSTERED ([id])
    );

-- CreateTable
    CREATE TABLE [dbo].[company_addresses] (
                                               [company_address_id] UNIQUEIDENTIFIER NOT NULL,
                                               [company_id] UNIQUEIDENTIFIER NOT NULL,
                                               [zip_region] VARCHAR(5) NOT NULL,
                                               CONSTRAINT [company_addresses_PRIMARY] PRIMARY KEY NONCLUSTERED ([company_address_id]),
                                               CONSTRAINT [company_addresses_company_id_zip_unique] UNIQUE NONCLUSTERED ([company_id],[zip_region])
    );

-- CreateTable
    CREATE TABLE [dbo].[company_social_links] (
                                                  [social_media_id] UNIQUEIDENTIFIER NOT NULL,
                                                  [company_id] UNIQUEIDENTIFIER NOT NULL,
                                                  [employer_id] UNIQUEIDENTIFIER,
                                                  [social_platform_id] UNIQUEIDENTIFIER NOT NULL,
                                                  [social_url] VARCHAR(255) NOT NULL,
                                                  CONSTRAINT [company_social_links_PRIMARY] PRIMARY KEY NONCLUSTERED ([social_media_id])
    );

-- CreateTable
    CREATE TABLE [dbo].[company_testimonials] (
                                                  [testimonial_id] UNIQUEIDENTIFIER NOT NULL,
                                                  [company_id] UNIQUEIDENTIFIER NOT NULL,
                                                  [employer_id] UNIQUEIDENTIFIER,
                                                  [text] VARCHAR(255) NOT NULL,
                                                  [author] VARCHAR(255) NOT NULL,
                                                  CONSTRAINT [company_testimonials_PRIMARY] PRIMARY KEY NONCLUSTERED ([testimonial_id])
    );

-- CreateTable
    CREATE TABLE [dbo].[edu_providers] (
                                           [id] UNIQUEIDENTIFIER NOT NULL CONSTRAINT [edu_providers_id_df] DEFAULT newid(),
                                           [edu_type] VARCHAR(50),
                                           [name] VARCHAR(255),
                                           [contact] VARCHAR(45),
                                           [contact_email] VARCHAR(255),
                                           [edu_url] VARCHAR(255),
                                           [mission] TEXT,
                                           [providerDescription] TEXT,
                                           [setsApartStatement] TEXT,
                                           [screeningCriteria] TEXT,
                                           [recruitingSources] TEXT,
                                           [programCount] VARCHAR(3),
                                           [cost] TEXT,
                                           [isAdminReviewed] BIT NOT NULL CONSTRAINT [edu_providers_isAdminReviewed_df] DEFAULT 0,
                                           [isCoalitionMember] BIT NOT NULL CONSTRAINT [edu_providers_isCoalitionMember_df] DEFAULT 0,
                                           [userId] UNIQUEIDENTIFIER,
                                           CONSTRAINT [edu_providers_PRIMARY] PRIMARY KEY NONCLUSTERED ([id]),
                                           CONSTRAINT [edu_providers_id_UNIQUE] UNIQUE NONCLUSTERED ([id]),
                                           CONSTRAINT [edu_providers_name_key] UNIQUE NONCLUSTERED ([name])
    );

-- CreateTable
    CREATE TABLE [dbo].[ProviderTestimonials] (
                                                  [id] UNIQUEIDENTIFIER NOT NULL CONSTRAINT [ProviderTestimonials_id_df] DEFAULT newid(),
                                                  [eduProviderId] UNIQUEIDENTIFIER NOT NULL,
                                                  [url] VARCHAR(45),
                                                  [author] VARCHAR(45),
                                                  [quote] TEXT,
                                                  CONSTRAINT [provider_testimonials_PRIMARY] PRIMARY KEY NONCLUSTERED ([id]),
                                                  CONSTRAINT [provider_testimonials_id_UNIQUE] UNIQUE NONCLUSTERED ([id])
    );

-- CreateTable
    CREATE TABLE [dbo].[edu_addresses] (
                                           [edu_address_id] UNIQUEIDENTIFIER NOT NULL,
                                           [edu_provider_id] UNIQUEIDENTIFIER NOT NULL,
                                           [street1] VARCHAR(255) NOT NULL,
                                           [street2] VARCHAR(255),
                                           [zip] VARCHAR(5) NOT NULL,
                                           CONSTRAINT [edu_addresses_PRIMARY] PRIMARY KEY NONCLUSTERED ([edu_address_id])
    );

-- CreateTable
    CREATE TABLE [dbo].[educators] (
                                       [educator_id] UNIQUEIDENTIFIER NOT NULL,
                                       [user_id] UNIQUEIDENTIFIER NOT NULL,
                                       [edu_providers_id] UNIQUEIDENTIFIER NOT NULL,
                                       CONSTRAINT [educators_PRIMARY] PRIMARY KEY NONCLUSTERED ([educator_id])
    );

-- CreateTable
    CREATE TABLE [dbo].[TraineeDetail] (
                                           [jobseekerId] UNIQUEIDENTIFIER NOT NULL,
                                           [isVerified] BIT NOT NULL CONSTRAINT [DF_trainee_isVerified] DEFAULT 0,
                                           [firstName] VARCHAR(45) NOT NULL,
                                           [lastName] VARCHAR(45) NOT NULL,
                                           [programTitle] VARCHAR(45) NOT NULL,
                                           [enrollmentStatus] VARCHAR(45) NOT NULL,
                                           [startDate] DATE NOT NULL,
                                           [exitDate] DATE NOT NULL,
                                           [nonCompletionReason] VARCHAR(45),
                                           CONSTRAINT [traineeDetail_PRIMARY] PRIMARY KEY NONCLUSTERED ([jobseekerId])
    );

-- CreateTable
    CREATE TABLE [dbo].[OtherPriorityPopulations] (
                                                      [id] UNIQUEIDENTIFIER NOT NULL,
                                                      [option] VARCHAR(45) NOT NULL,
                                                      CONSTRAINT [otherPriorityPopulations_PRIMARY] PRIMARY KEY NONCLUSTERED ([id])
    );

-- CreateTable
    CREATE TABLE [dbo].[CareerPrepAssessment] (
                                                  [jobseekerId] UNIQUEIDENTIFIER NOT NULL,
                                                  [assessmentDate] DATETIME NOT NULL CONSTRAINT [CareerPrepAssessment_assessmentDate_df] DEFAULT CURRENT_TIMESTAMP,
                                                  [interestPathway] VARCHAR(45),
                                                  [pronouns] VARCHAR(15) NOT NULL,
                                                  [expectedEduCompletion] VARCHAR(45) NOT NULL,
                                                  [experienceWithApplying] BIT NOT NULL,
                                                  [experienceWithInterview] BIT NOT NULL,
                                                  [prevWorkExperience] BIT NOT NULL CONSTRAINT [CareerPrepAssessment_prevWorkExperience_df] DEFAULT 0,
                                                  [streetAddress] VARCHAR(255),
                                                  [priorityPopulations] TEXT,
                                                  [updatedAt] DATETIME NOT NULL,
                                                  CONSTRAINT [career_prep_app_PRIMARY] PRIMARY KEY NONCLUSTERED ([jobseekerId])
    );

-- CreateTable
    CREATE TABLE [dbo].[CybersecurityRating] (
                                                 [jobseekerId] UNIQUEIDENTIFIER NOT NULL,
                                                 [networking] TINYINT NOT NULL,
                                                 [projectManagement] TINYINT NOT NULL,
                                                 [securityTools] TINYINT NOT NULL,
                                                 [operatingSystems] TINYINT NOT NULL,
                                                 [programming] TINYINT NOT NULL,
                                                 [cryptography] TINYINT NOT NULL,
                                                 [cloudSecurity] TINYINT NOT NULL,
                                                 [incidentResponse] TINYINT NOT NULL,
                                                 [dataSecurity] TINYINT NOT NULL,
                                                 [technicalSupport] TINYINT NOT NULL,
                                                 [computationalThinking] TINYINT NOT NULL,
                                                 [apiUsage] TINYINT NOT NULL,
                                                 [updatedAt] DATETIME NOT NULL,
                                                 [overallAverage] FLOAT,
                                                 CONSTRAINT [cybersecurity_rating_PRIMARY] PRIMARY KEY NONCLUSTERED ([jobseekerId])
    );

-- CreateTable
    CREATE TABLE [dbo].[DataAnalyticsRating] (
                                                 [jobseekerId] UNIQUEIDENTIFIER NOT NULL,
                                                 [dataAnalysis] TINYINT NOT NULL,
                                                 [sqlProgramming] TINYINT NOT NULL,
                                                 [pythonPackages] TINYINT NOT NULL,
                                                 [dataScience] TINYINT NOT NULL,
                                                 [dataEngineering] TINYINT NOT NULL,
                                                 [tableau] TINYINT NOT NULL,
                                                 [machineLearning] TINYINT NOT NULL,
                                                 [rProgramming] TINYINT NOT NULL,
                                                 [projectManagement] TINYINT NOT NULL,
                                                 [dataVisualization] TINYINT NOT NULL,
                                                 [dataStructures] TINYINT NOT NULL,
                                                 [bigOComplexity] TINYINT NOT NULL,
                                                 [sortingAlgorithms] TINYINT NOT NULL,
                                                 [databases] TINYINT NOT NULL,
                                                 [computationalThinking] TINYINT NOT NULL,
                                                 [updatedAt] DATETIME NOT NULL,
                                                 [overallAverage] FLOAT,
                                                 CONSTRAINT [data_analytics_rating_PRIMARY] PRIMARY KEY NONCLUSTERED ([jobseekerId])
    );

-- CreateTable
    CREATE TABLE [dbo].[ITCloudRating] (
                                           [jobseekerId] UNIQUEIDENTIFIER NOT NULL,
                                           [techSupport] TINYINT NOT NULL,
                                           [activeDirectory] TINYINT NOT NULL,
                                           [projectManagement] TINYINT NOT NULL,
                                           [helpDeskSupport] TINYINT NOT NULL,
                                           [windowsServers] TINYINT NOT NULL,
                                           [sqlProgramming] TINYINT NOT NULL,
                                           [computerHardware] TINYINT NOT NULL,
                                           [operatingSystems] TINYINT NOT NULL,
                                           [systemAdmin] TINYINT NOT NULL,
                                           [networkAdmin] TINYINT NOT NULL,
                                           [virtualization] TINYINT NOT NULL,
                                           [coreCloudServices] TINYINT NOT NULL,
                                           [apiUsage] TINYINT NOT NULL,
                                           [httpResponseCodes] TINYINT NOT NULL,
                                           [computationalThinking] TINYINT NOT NULL,
                                           [updatedAt] DATETIME NOT NULL,
                                           [overallAverage] FLOAT,
                                           CONSTRAINT [it_cloud_rating_PRIMARY] PRIMARY KEY NONCLUSTERED ([jobseekerId])
    );

-- CreateTable
    CREATE TABLE [dbo].[SoftwareDevRating] (
                                               [jobseekerId] UNIQUEIDENTIFIER NOT NULL,
                                               [softwareEngineering] TINYINT NOT NULL,
                                               [softwareDevelopmentLifecycle] TINYINT NOT NULL,
                                               [programmingLanguages] TINYINT NOT NULL,
                                               [dataStructuresAndAlgorithms] TINYINT NOT NULL,
                                               [softwareArchitecture] TINYINT NOT NULL,
                                               [versionControl] TINYINT NOT NULL,
                                               [databaseManagement] TINYINT NOT NULL,
                                               [devOps] TINYINT NOT NULL,
                                               [cloudComputing] TINYINT NOT NULL,
                                               [conceptualSystemsThinking] TINYINT NOT NULL,
                                               [problemSolving] TINYINT NOT NULL,
                                               [fundamentalCodingConcepts] TINYINT NOT NULL,
                                               [debugging] TINYINT NOT NULL,
                                               [computationalThinking] TINYINT NOT NULL,
                                               [softwareOptimization] TINYINT NOT NULL,
                                               [updatedAt] DATETIME NOT NULL,
                                               [overallAverage] FLOAT,
                                               CONSTRAINT [software_dev_rating_PRIMARY] PRIMARY KEY NONCLUSTERED ([jobseekerId])
    );

-- CreateTable
    CREATE TABLE [dbo].[DurableSkillsRating] (
                                                 [jobseekerId] UNIQUEIDENTIFIER NOT NULL,
                                                 [emotionManagement] TINYINT NOT NULL,
                                                 [empathy] TINYINT NOT NULL,
                                                 [goalSetting] TINYINT NOT NULL,
                                                 [timeManagement] TINYINT NOT NULL,
                                                 [adaptability] TINYINT NOT NULL,
                                                 [criticalThinking] TINYINT NOT NULL,
                                                 [creativity] TINYINT NOT NULL,
                                                 [resilience] TINYINT NOT NULL,
                                                 [communication] TINYINT NOT NULL,
                                                 [activeListening] TINYINT NOT NULL,
                                                 [conflictResolution] TINYINT NOT NULL,
                                                 [nonverbalCommunication] TINYINT NOT NULL,
                                                 [teamwork] TINYINT NOT NULL,
                                                 [trustBuilding] TINYINT NOT NULL,
                                                 [leadership] TINYINT NOT NULL,
                                                 [perspectiveTaking] TINYINT NOT NULL,
                                                 [culturalAwareness] TINYINT NOT NULL,
                                                 [relationshipBuilding] TINYINT NOT NULL,
                                                 [documentationSkills] TINYINT NOT NULL,
                                                 [updatedAt] DATETIME NOT NULL,
                                                 [overallAverage] FLOAT,
                                                 CONSTRAINT [durable_skills_rating_PRIMARY] PRIMARY KEY NONCLUSTERED ([jobseekerId])
    );

-- CreateTable
    CREATE TABLE [dbo].[BrandingRating] (
                                            [jobseekerId] UNIQUEIDENTIFIER NOT NULL,
                                            [personalBrand] TINYINT NOT NULL,
                                            [onlinePresence] TINYINT NOT NULL,
                                            [elevatorPitch] TINYINT NOT NULL,
                                            [resumeEffectiveness] TINYINT NOT NULL,
                                            [coverLetterEffectiveness] TINYINT NOT NULL,
                                            [interviewExperience] TINYINT NOT NULL,
                                            [responseTechnique] TINYINT NOT NULL,
                                            [followUpImportance] TINYINT NOT NULL,
                                            [onlineNetworking] TINYINT NOT NULL,
                                            [eventNetworking] TINYINT NOT NULL,
                                            [relationshipManagement] TINYINT NOT NULL,
                                            [jobSearchStrategy] TINYINT NOT NULL,
                                            [materialDistribution] TINYINT NOT NULL,
                                            [networkingTechniques] TINYINT NOT NULL,
                                            [onboardingBestPractices] TINYINT NOT NULL,
                                            [developmentPlan] TINYINT NOT NULL,
                                            [mentorship] TINYINT NOT NULL,
                                            [updatedAt] DATETIME NOT NULL,
                                            [overallAverage] FLOAT,
                                            CONSTRAINT [branding_rating_PRIMARY] PRIMARY KEY NONCLUSTERED ([jobseekerId])
    );

-- CreateTable
    CREATE TABLE [dbo].[CaseMgmt] (
                                      [jobseekerId] UNIQUEIDENTIFIER NOT NULL,
                                      [managerId] UNIQUEIDENTIFIER,
                                      [prepEnrollmentStatus] VARCHAR(30) NOT NULL,
                                      [careerPrepTrack] VARCHAR(15),
                                      [prepStartDate] DATETIME,
                                      [prepExpectedEndDate] DATETIME,
                                      [prepActualEndDate] DATETIME,
                                      [createdAt] DATETIME NOT NULL CONSTRAINT [CaseMgmt_createdAt_df] DEFAULT CURRENT_TIMESTAMP,
                                      [updatedAt] DATETIME NOT NULL,
                                      CONSTRAINT [case_mgmt_PRIMARY] PRIMARY KEY NONCLUSTERED ([jobseekerId])
    );

-- CreateTable
    CREATE TABLE [dbo].[CaseMgmtNotes] (
                                           [id] NVARCHAR(1000) NOT NULL CONSTRAINT [CaseMgmtNotes_id_df] DEFAULT newid(),
                                           [jobseekerId] UNIQUEIDENTIFIER NOT NULL,
                                           [date] DATETIME,
                                           [noteType] VARCHAR(15) NOT NULL,
                                           [noteContent] NTEXT NOT NULL,
                                           [createdBy] UNIQUEIDENTIFIER NOT NULL,
                                           [createdAt] DATETIME NOT NULL CONSTRAINT [CaseMgmtNotes_createdAt_df] DEFAULT CURRENT_TIMESTAMP,
                                           [updatedAt] DATETIME NOT NULL,
                                           CONSTRAINT [case_mgmt_notes_PRIMARY] PRIMARY KEY NONCLUSTERED ([id])
    );

-- CreateTable
    CREATE TABLE [dbo].[employers] (
                                       [employer_id] UNIQUEIDENTIFIER NOT NULL,
                                       [user_id] UNIQUEIDENTIFIER NOT NULL,
                                       [company_id] UNIQUEIDENTIFIER,
                                       [work_address_id] UNIQUEIDENTIFIER,
                                       [job_title] VARCHAR(255),
                                       [linkedin_url] VARCHAR(255),
                                       [has_agreed_terms] BIT NOT NULL CONSTRAINT [employers_has_agreed_terms_df] DEFAULT 0,
                                       [is_verified_employee] BIT NOT NULL CONSTRAINT [DF__employers__is_verified] DEFAULT 0,
                                       CONSTRAINT [employers_PRIMARY] PRIMARY KEY NONCLUSTERED ([employer_id]),
                                       CONSTRAINT [employers_employer_id_UNIQUE] UNIQUE NONCLUSTERED ([employer_id]),
                                       CONSTRAINT [employers_user_id_key] UNIQUE NONCLUSTERED ([user_id])
    );

-- CreateTable
    CREATE TABLE [dbo].[industry_sectors] (
                                              [industry_sector_id] UNIQUEIDENTIFIER NOT NULL,
                                              [sector_title] VARCHAR(255) NOT NULL,
                                              CONSTRAINT [industry_sectors_PRIMARY] PRIMARY KEY NONCLUSTERED ([industry_sector_id])
    );

-- CreateTable
    CREATE TABLE [dbo].[job_postings] (
                                          [job_posting_id] UNIQUEIDENTIFIER NOT NULL,
                                          [company_id] UNIQUEIDENTIFIER NOT NULL,
                                          [location_id] UNIQUEIDENTIFIER NOT NULL,
                                          [employer_id] UNIQUEIDENTIFIER,
                                          [tech_area_id] UNIQUEIDENTIFIER,
                                          [sector_id] UNIQUEIDENTIFIER,
                                          [job_title] VARCHAR(255) NOT NULL,
                                          [job_description] VARCHAR(255) NOT NULL,
                                          [is_internship] BIT NOT NULL CONSTRAINT [DF__job_posti__is_in__571DF1D5] DEFAULT 0,
                                          [is_paid] BIT NOT NULL CONSTRAINT [DF__job_posti__is_pa__5812160E] DEFAULT 1,
                                          [employment_type] NVARCHAR(255) NOT NULL CONSTRAINT [DF__job_posti__emplo__59063A47] DEFAULT 'N''full-time''',
                                          [location] NVARCHAR(255) NOT NULL,
                                          [salary_range] VARCHAR(45) NOT NULL,
                                          [county] VARCHAR(255) NOT NULL,
                                          [zip] VARCHAR(45) NOT NULL,
                                          [publish_date] DATETIME NOT NULL,
                                          [unpublish_date] DATETIME NOT NULL,
                                          [job_post_url] VARCHAR(255),
                                          [assessment_url] VARCHAR(255),
                                          CONSTRAINT [job_postings_PRIMARY] PRIMARY KEY NONCLUSTERED ([job_posting_id]),
                                          CONSTRAINT [job_postings_job_listing_id_UNIQUE] UNIQUE NONCLUSTERED ([job_posting_id])
    );

-- CreateTable
    CREATE TABLE [dbo].[JobseekerJobPosting] (
                                                 [id] UNIQUEIDENTIFIER NOT NULL,
                                                 [jobPostId] UNIQUEIDENTIFIER NOT NULL,
                                                 [jobseekerId] UNIQUEIDENTIFIER NOT NULL,
                                                 [jobStatus] VARCHAR(45) NOT NULL CONSTRAINT [JobseekerJobPosting_jobStatus_df] DEFAULT 'Bookmarked',
                                                 [savedAt] DATETIME2 NOT NULL CONSTRAINT [JobseekerJobPosting_savedAt_df] DEFAULT CURRENT_TIMESTAMP,
                                                 [appliedDate] DATETIME2,
                                                 [followUpDate] DATETIME2,
                                                 CONSTRAINT [jobseeker_job_posting_PRIMARY] PRIMARY KEY NONCLUSTERED ([id])
    );

-- CreateTable
    CREATE TABLE [dbo].[jobseeker_has_skills] (
                                                  [jobseeker_id] UNIQUEIDENTIFIER NOT NULL,
                                                  [skill_id] UNIQUEIDENTIFIER NOT NULL,
                                                  CONSTRAINT [jobseeker_has_skills_PRIMARY] PRIMARY KEY NONCLUSTERED ([jobseeker_id],[skill_id])
    );

-- CreateTable
    CREATE TABLE [dbo].[jobseekers] (
                                        [jobseeker_id] UNIQUEIDENTIFIER NOT NULL,
                                        [user_id] UNIQUEIDENTIFIER NOT NULL,
                                        [targeted_pathway] UNIQUEIDENTIFIER,
                                        [is_enrolled_ed_program] BIT NOT NULL,
                                        [highest_level_of_study_completed] VARCHAR(255),
                                        [current_grade_level] VARCHAR(45),
                                        [current_enrolled_ed_program] VARCHAR(255),
                                        [intern_hours_required] SMALLINT NOT NULL CONSTRAINT [DF__jobseeker__inter__6383C8BA] DEFAULT 0,
                                        [intro_headline] VARCHAR(max),
                                        [current_job_title] VARCHAR(255),
                                        [linkedin_url] VARCHAR(255),
                                        [years_work_exp] SMALLINT,
                                        [months_internship_exp] SMALLINT,
                                        [portfolio_url] VARCHAR(255),
                                        [portfolio_password] NVARCHAR(255),
                                        [video_url] VARCHAR(255),
                                        [employment_type_sought] NVARCHAR(255),
                                        [is_marked_deletion] DATETIME,
                                        [assignedPool] VARCHAR(20),
                                        [careerPrepComplete] BIT NOT NULL CONSTRAINT [jobseekers_careerPrepComplete_df] DEFAULT 0,
                                        [careerPrepTrackRecommendation] VARCHAR(25),
                                        [created_at] DATETIME2 NOT NULL CONSTRAINT [jobseekers_created_at_df] DEFAULT CURRENT_TIMESTAMP,
                                        [updated_at] DATETIME2,
                                        CONSTRAINT [jobseekers_PRIMARY] PRIMARY KEY NONCLUSTERED ([jobseeker_id]),
                                        CONSTRAINT [jobseekers_learner_id_UNIQUE] UNIQUE NONCLUSTERED ([jobseeker_id]),
                                        CONSTRAINT [jobseekers_user_id_key] UNIQUE NONCLUSTERED ([user_id])
    );

-- CreateTable
    CREATE TABLE [dbo].[jobseekers_private_data] (
                                                     [jobseeker_private_data_id] UNIQUEIDENTIFIER NOT NULL,
                                                     [jobseeker_id] UNIQUEIDENTIFIER NOT NULL,
                                                     [ssn] VARCHAR(255),
                                                     [is_authorized_to_work_in_usa] BIT,
                                                     [job_sponsorship_required] BIT,
                                                     [is_veteran] VARCHAR(45) NOT NULL CONSTRAINT [DF__jobseeker__is_ve__3E1D39E1] DEFAULT '',
                                                     [disability_status] VARCHAR(45) NOT NULL CONSTRAINT [jobseekers_private_data_disability_status_df] DEFAULT '',
                                                     [disability] VARCHAR(45),
                                                     [gender] VARCHAR(45) NOT NULL CONSTRAINT [jobseekers_private_data_gender_df] DEFAULT '',
                                                     [race] VARCHAR(45) NOT NULL CONSTRAINT [jobseekers_private_data_race_df] DEFAULT '',
                                                     [ethnicity] VARCHAR(45) NOT NULL CONSTRAINT [jobseekers_private_data_ethnicity_df] DEFAULT '',
                                                     CONSTRAINT [jobseekers_private_data_PRIMARY] PRIMARY KEY NONCLUSTERED ([jobseeker_private_data_id]),
                                                     CONSTRAINT [jobseekers_private_data_learner_private_data_id_UNIQUE] UNIQUE NONCLUSTERED ([jobseeker_private_data_id]),
                                                     CONSTRAINT [jobseekers_private_data_jobseeker_id_key] UNIQUE NONCLUSTERED ([jobseeker_id])
    );

-- CreateTable
    CREATE TABLE [dbo].[jobseekers_education] (
                                                  [jobseeker_ed_id] UNIQUEIDENTIFIER NOT NULL CONSTRAINT [jobseekers_education_jobseeker_ed_id_df] DEFAULT newid(),
                                                  [jobseeker_id] UNIQUEIDENTIFIER NOT NULL,
                                                  [edu_provider_id] UNIQUEIDENTIFIER NOT NULL,
                                                  [program_id] UNIQUEIDENTIFIER,
                                                  [ed_program] NVARCHAR(45) NOT NULL,
                                                  [ed_system] NVARCHAR(255),
                                                  [is_tech_degree] BIT CONSTRAINT [jobseekers_education_is_tech_degree_df] DEFAULT 0,
                                                  [is_enrolled] BIT NOT NULL,
                                                  [enrollment_status] VARCHAR(45) NOT NULL CONSTRAINT [jobseekers_education_enrollment_status_df] DEFAULT 'unknown',
                                                  [start_date] DATE NOT NULL,
                                                  [graduation_date] DATE NOT NULL,
                                                  [degree_type] NVARCHAR(45),
                                                  [major] NVARCHAR(45),
                                                  [minor] NVARCHAR(45),
                                                  [gpa] NVARCHAR(45),
                                                  [description] NTEXT,
                                                  CONSTRAINT [jobseekers_education_pkey] PRIMARY KEY CLUSTERED ([jobseeker_ed_id])
    );

-- CreateTable
    CREATE TABLE [dbo].[JobPlacement] (
                                          [job_placement_id] UNIQUEIDENTIFIER NOT NULL CONSTRAINT [JobPlacement_job_placement_id_df] DEFAULT newid(),
                                          [companyId] UNIQUEIDENTIFIER,
                                          [employmentStatus] VARCHAR(45),
                                          [jobStartDate] DATETIME,
                                          [employmentType] VARCHAR(45),
                                          [earnLearnType] VARCHAR(45),
                                          [naicsCode] VARCHAR(45),
                                          [employerName] VARCHAR(45) NOT NULL,
                                          [hourlyEarnings] VARCHAR(15) NOT NULL,
                                          CONSTRAINT [job_placement_PRIMARY] PRIMARY KEY NONCLUSTERED ([job_placement_id])
    );

-- CreateTable
    CREATE TABLE [dbo].[pathway_has_skills] (
                                                [pathway_id] UNIQUEIDENTIFIER NOT NULL,
                                                [skill_id] UNIQUEIDENTIFIER NOT NULL,
                                                CONSTRAINT [pathway_has_skills_PRIMARY] PRIMARY KEY NONCLUSTERED ([pathway_id],[skill_id])
    );

-- CreateTable
    CREATE TABLE [dbo].[pathway_subcategories] (
                                                   [pathway_subcategory_id] UNIQUEIDENTIFIER NOT NULL,
                                                   [pathway_id] UNIQUEIDENTIFIER NOT NULL,
                                                   [pw_subcategory_name] VARCHAR(45) NOT NULL,
                                                   [subcategory_assessment_url] VARCHAR(255),
                                                   CONSTRAINT [pathway_subcategories_PRIMARY] PRIMARY KEY NONCLUSTERED ([pathway_subcategory_id],[pathway_id])
    );

-- CreateTable
    CREATE TABLE [dbo].[pathways] (
                                      [pathway_id] UNIQUEIDENTIFIER NOT NULL,
                                      [pathway_title] VARCHAR(255) NOT NULL,
                                      CONSTRAINT [pathways_PRIMARY] PRIMARY KEY NONCLUSTERED ([pathway_id]),
                                      CONSTRAINT [pathways_pathway_title_key] UNIQUE NONCLUSTERED ([pathway_title])
    );

-- CreateTable
    CREATE TABLE [dbo].[proj_based_tech_assessments] (
                                                         [proj_based_tech_assessment_id] UNIQUEIDENTIFIER NOT NULL,
                                                         [pathway_id] UNIQUEIDENTIFIER NOT NULL,
                                                         [url] VARCHAR(255) NOT NULL,
                                                         [title] VARCHAR(255) NOT NULL,
                                                         CONSTRAINT [proj_based_tech_assessments_PRIMARY] PRIMARY KEY NONCLUSTERED ([proj_based_tech_assessment_id]),
                                                         CONSTRAINT [proj_based_tech_assessments_proj_based_tech_assessment_id_UNIQUE] UNIQUE NONCLUSTERED ([proj_based_tech_assessment_id])
    );

-- CreateTable
    CREATE TABLE [dbo].[project_experiences] (
                                                 [proj_exp_id] UNIQUEIDENTIFIER NOT NULL CONSTRAINT [project_experiences_proj_exp_id_df] DEFAULT newid(),
                                                 [jobseeker_id] UNIQUEIDENTIFIER NOT NULL,
                                                 [project_title] VARCHAR(255) NOT NULL,
                                                 [jobseeker_role] VARCHAR(255) NOT NULL,
                                                 [start_date] DATETIME NOT NULL,
                                                 [completion_date] DATETIME NOT NULL,
                                                 [problem_solved_description] NTEXT NOT NULL,
                                                 [team_size] SMALLINT NOT NULL,
                                                 [repo_url] VARCHAR(255),
                                                 [demo_url] VARCHAR(255),
                                                 CONSTRAINT [project_experiences_PRIMARY] PRIMARY KEY NONCLUSTERED ([proj_exp_id])
    );

-- CreateTable
    CREATE TABLE [dbo].[project_has_skills] (
                                                [proj_exp_id] UNIQUEIDENTIFIER NOT NULL,
                                                [skill_id] UNIQUEIDENTIFIER NOT NULL,
                                                CONSTRAINT [project_has_skills_PRIMARY] PRIMARY KEY NONCLUSTERED ([proj_exp_id],[skill_id])
    );

-- CreateTable
    CREATE TABLE [dbo].[sa_possible_answers] (
                                                 [sa_possible_answer_id] UNIQUEIDENTIFIER NOT NULL,
                                                 [sa_question_id] UNIQUEIDENTIFIER NOT NULL,
                                                 [answer_text] VARCHAR(255),
                                                 [is_correct] BIT NOT NULL CONSTRAINT [DF__sa_possib__is_co__1332DBDC] DEFAULT 1,
                                                 CONSTRAINT [sa_possible_answers_PRIMARY] PRIMARY KEY NONCLUSTERED ([sa_possible_answer_id]),
                                                 CONSTRAINT [sa_possible_answers_sa_possible_answer_id_UNIQUE] UNIQUE NONCLUSTERED ([sa_possible_answer_id])
    );

-- CreateTable
    CREATE TABLE [dbo].[sa_questions] (
                                          [sa_question_id] UNIQUEIDENTIFIER NOT NULL,
                                          [self_assessment_id] UNIQUEIDENTIFIER NOT NULL,
                                          [question_topic] NVARCHAR(255) NOT NULL,
                                          [question_type] NVARCHAR(255) NOT NULL,
                                          [text] VARCHAR(255) NOT NULL,
                                          [option_count] INT,
                                          CONSTRAINT [sa_questions_PRIMARY] PRIMARY KEY NONCLUSTERED ([sa_question_id]),
                                          CONSTRAINT [sa_questions_sa_question_id_UNIQUE] UNIQUE NONCLUSTERED ([sa_question_id])
    );

-- CreateTable
    CREATE TABLE [dbo].[self_assessments] (
                                              [self_assessment_id] UNIQUEIDENTIFIER NOT NULL,
                                              [pathway_id] UNIQUEIDENTIFIER NOT NULL,
                                              CONSTRAINT [self_assessments_PRIMARY] PRIMARY KEY NONCLUSTERED ([self_assessment_id]),
                                              CONSTRAINT [self_assessments_self_assessment_id_UNIQUE] UNIQUE NONCLUSTERED ([self_assessment_id])
    );

-- CreateTable
    CREATE TABLE [dbo].[skill_subcategories] (
                                                 [skill_subcategory_id] UNIQUEIDENTIFIER NOT NULL CONSTRAINT [skill_subcategories_skill_subcategory_id_df] DEFAULT (newid()),
                                                 [subcategory_name] VARCHAR(255) NOT NULL,
                                                 [subcategory_description] VARCHAR(255) NOT NULL,
                                                 CONSTRAINT [skill_subcategories_PRIMARY] PRIMARY KEY NONCLUSTERED ([skill_subcategory_id]),
                                                 CONSTRAINT [skill_subcategories_skill_category_id_UNIQUE] UNIQUE NONCLUSTERED ([skill_subcategory_id])
    );

-- CreateTable
    CREATE TABLE [dbo].[skills] (
                                    [skill_id] UNIQUEIDENTIFIER NOT NULL,
                                    [skill_subcategory_id] UNIQUEIDENTIFIER NOT NULL,
                                    [skill_name] VARCHAR(255) NOT NULL,
                                    [skill_info_url] VARCHAR(255) NOT NULL CONSTRAINT [skills_skill_info_url_df] DEFAULT '',
                                    CONSTRAINT [skills_PRIMARY] PRIMARY KEY NONCLUSTERED ([skill_id]),
                                    CONSTRAINT [skills_skill_id_UNIQUE] UNIQUE NONCLUSTERED ([skill_id])
    );

-- CreateTable
    CREATE TABLE [dbo].[social_media_platforms] (
                                                    [social_platform_id] UNIQUEIDENTIFIER NOT NULL,
                                                    [platform] VARCHAR(45) NOT NULL,
                                                    [social_logo_url] VARCHAR(255) NOT NULL,
                                                    CONSTRAINT [social_media_platforms_PRIMARY] PRIMARY KEY NONCLUSTERED ([social_platform_id])
    );

-- CreateTable
    CREATE TABLE [dbo].[technology_areas] (
                                              [id] UNIQUEIDENTIFIER NOT NULL,
                                              [title] VARCHAR(255) NOT NULL,
                                              CONSTRAINT [technology_areas_PRIMARY] PRIMARY KEY NONCLUSTERED ([id])
    );

-- CreateTable
    CREATE TABLE [dbo].[provider_program_has_skills] (
                                                         [training_program_id] UNIQUEIDENTIFIER NOT NULL,
                                                         [skill_id] UNIQUEIDENTIFIER NOT NULL,
                                                         CONSTRAINT [training_program_has_skills_PRIMARY] PRIMARY KEY NONCLUSTERED ([training_program_id],[skill_id])
    );

-- CreateTable
    CREATE TABLE [dbo].[provider_programs] (
                                               [training_program_id] UNIQUEIDENTIFIER NOT NULL,
                                               [program_id] UNIQUEIDENTIFIER NOT NULL,
                                               [edu_provider_id] UNIQUEIDENTIFIER NOT NULL,
                                               [pathway_id] UNIQUEIDENTIFIER,
                                               [target_job_roles] TEXT,
                                               [description] TEXT,
                                               [cost] VARCHAR(255),
                                               [months] VARCHAR(45),
                                               [hoursPerWeek] VARCHAR(45),
                                               [targetPopulation] TEXT,
                                               [serviceArea] TEXT,
                                               [pathways] TEXT,
                                               [programDescription] TEXT,
                                               [target_population] TEXT,
                                               CONSTRAINT [training_programs_PRIMARY] PRIMARY KEY NONCLUSTERED ([training_program_id]),
                                               CONSTRAINT [training_programs_training_program_id_UNIQUE] UNIQUE NONCLUSTERED ([training_program_id])
    );

-- CreateTable
    CREATE TABLE [dbo].[programs] (
                                      [id] UNIQUEIDENTIFIER NOT NULL,
                                      [title] NVARCHAR(255) NOT NULL,
                                      CONSTRAINT [programs_pkey] PRIMARY KEY CLUSTERED ([id]),
                                      CONSTRAINT [programs_id_UNIQUE] UNIQUE NONCLUSTERED ([id]),
                                      CONSTRAINT [programs_title_key] UNIQUE NONCLUSTERED ([title])
    );

-- CreateTable
    CREATE TABLE [dbo].[volunteer_has_skills] (
                                                  [volunteer_skills_id] UNIQUEIDENTIFIER NOT NULL,
                                                  [volunteer_id] UNIQUEIDENTIFIER NOT NULL,
                                                  [skill_id] UNIQUEIDENTIFIER NOT NULL,
                                                  CONSTRAINT [volunteer_has_skills_PRIMARY] PRIMARY KEY NONCLUSTERED ([volunteer_skills_id])
    );

-- CreateTable
    CREATE TABLE [dbo].[volunteers] (
                                        [volunteer_id] UNIQUEIDENTIFIER NOT NULL,
                                        [user_id] UNIQUEIDENTIFIER NOT NULL,
                                        [volunteer_type] NVARCHAR(255) NOT NULL,
                                        CONSTRAINT [volunteers_PRIMARY] PRIMARY KEY NONCLUSTERED ([volunteer_id]),
                                        CONSTRAINT [volunteers_mentor_id_UNIQUE] UNIQUE NONCLUSTERED ([volunteer_id])
    );

-- CreateTable
    CREATE TABLE [dbo].[work_experiences] (
                                              [work_id] UNIQUEIDENTIFIER NOT NULL,
                                              [jobseeker_id] UNIQUEIDENTIFIER NOT NULL,
                                              [tech_area_id] UNIQUEIDENTIFIER,
                                              [sector_id] UNIQUEIDENTIFIER,
                                              [company] VARCHAR(255) NOT NULL,
                                              [is_internship] BIT NOT NULL CONSTRAINT [DF__work_expe__is_in__75A278F5] DEFAULT 0,
                                              [job_title] VARCHAR(45) NOT NULL,
                                              [is_current_job] BIT NOT NULL CONSTRAINT [DF__work_expe__is_cu__76969D2E] DEFAULT 0,
                                              [start_date] DATETIME NOT NULL,
                                              [end_date] DATETIME,
                                              [responsibilities] NTEXT NOT NULL,
                                              CONSTRAINT [work_experiences_PRIMARY] PRIMARY KEY NONCLUSTERED ([work_id])
    );

-- CreateTable
    CREATE TABLE [dbo].[postal_geo_data] (
                                             [zip] VARCHAR(5) NOT NULL,
                                             [city] NVARCHAR(100) NOT NULL,
                                             [county] NVARCHAR(100) NOT NULL,
                                             [state_code] VARCHAR(2) NOT NULL,
                                             [state] NVARCHAR(100) NOT NULL,
                                             [lat] FLOAT(53) NOT NULL,
                                             [lng] FLOAT(53) NOT NULL,
                                             CONSTRAINT [postal_codes_PRIMARY] PRIMARY KEY NONCLUSTERED ([zip])
    );

-- CreateTable
    CREATE TABLE [dbo].[_OtherPriorityPopulations] (
                                                       [A] UNIQUEIDENTIFIER NOT NULL,
                                                       [B] UNIQUEIDENTIFIER NOT NULL,
                                                       CONSTRAINT [_OtherPriorityPopulations_AB_unique] UNIQUE NONCLUSTERED ([A],[B])
    );

-- CreateTable
    CREATE TABLE [dbo].[_JobPostingSkills] (
                                               [A] UNIQUEIDENTIFIER NOT NULL,
                                               [B] UNIQUEIDENTIFIER NOT NULL,
                                               CONSTRAINT [_JobPostingSkills_AB_unique] UNIQUE NONCLUSTERED ([A],[B])
    );

-- CreateIndex
    CREATE NONCLUSTERED INDEX [Account_user_id_idx] ON [dbo].[Account]([user_id]);

-- CreateIndex
    CREATE NONCLUSTERED INDEX [Session_userId_idx] ON [dbo].[Session]([userId]);

-- CreateIndex
    CREATE NONCLUSTERED INDEX [fk_certificates_jobseeker1_idx] ON [dbo].[certificates]([jobseeker_id]);

-- CreateIndex
    CREATE NONCLUSTERED INDEX [cfa_admin_fk_admin_contacts1_idx] ON [dbo].[cfa_admin]([user_id]);

-- CreateIndex
    CREATE NONCLUSTERED INDEX [companies_fk_company_industry_sectors1_idx] ON [dbo].[companies]([industry_sector_id]);

-- CreateIndex
    CREATE NONCLUSTERED INDEX [company_addresses_fk_company_address_company1_idx] ON [dbo].[company_addresses]([company_id]);

-- CreateIndex
    CREATE NONCLUSTERED INDEX [company_social_links_fk_social_media_company_company1_idx] ON [dbo].[company_social_links]([company_id]);

-- CreateIndex
    CREATE NONCLUSTERED INDEX [company_social_links_fk_social_media_company_social_media_platform1_idx] ON [dbo].[company_social_links]([social_platform_id]);

-- CreateIndex
    CREATE NONCLUSTERED INDEX [fk_company_testimonials_company1_idx] ON [dbo].[company_testimonials]([company_id]);

-- CreateIndex
    CREATE NONCLUSTERED INDEX [edu_addresses_fk_edu_address_edu_institution1_idx] ON [dbo].[edu_addresses]([edu_provider_id]);

-- CreateIndex
    CREATE NONCLUSTERED INDEX [fk_educators_contacts1_idx] ON [dbo].[educators]([user_id]);

-- CreateIndex
    CREATE NONCLUSTERED INDEX [fk_educators_edu_institution1_idx] ON [dbo].[educators]([edu_providers_id]);

-- CreateIndex
    CREATE NONCLUSTERED INDEX [fk_case_mgmt_admin1_idx] ON [dbo].[CaseMgmt]([managerId]);

-- CreateIndex
    CREATE NONCLUSTERED INDEX [fk_case_mgmt_jobseeker1_idx] ON [dbo].[CaseMgmt]([jobseekerId]);

-- CreateIndex
    CREATE NONCLUSTERED INDEX [employers_fk_employer_user1_idx] ON [dbo].[employers]([user_id]);

-- CreateIndex
    CREATE NONCLUSTERED INDEX [fk_employers_company1_idx] ON [dbo].[employers]([company_id]);

-- CreateIndex
    CREATE NONCLUSTERED INDEX [fk_job_postings_company_addresses1_idx] ON [dbo].[job_postings]([location_id]);

-- CreateIndex
    CREATE NONCLUSTERED INDEX [fk_job_postings_companies1_idx] ON [dbo].[job_postings]([company_id]);

-- CreateIndex
    CREATE NONCLUSTERED INDEX [fk_job_postings_employers1_idx] ON [dbo].[job_postings]([employer_id]);

-- CreateIndex
    CREATE NONCLUSTERED INDEX [fk_job_postings_technology_areas1_idx] ON [dbo].[job_postings]([tech_area_id]);

-- CreateIndex
    CREATE NONCLUSTERED INDEX [jobseeker_has_skills_fk_jobseeker_has_skill_jobseeker1_idx] ON [dbo].[jobseeker_has_skills]([jobseeker_id]);

-- CreateIndex
    CREATE NONCLUSTERED INDEX [jobseeker_has_skills_fk_jobseeker_has_skill_skill1_idx] ON [dbo].[jobseeker_has_skills]([skill_id]);

-- CreateIndex
    CREATE NONCLUSTERED INDEX [jobseekers_fk_jobseeker_Pathways1_idx] ON [dbo].[jobseekers]([targeted_pathway]);

-- CreateIndex
    CREATE NONCLUSTERED INDEX [jobseekers_fk_learner_user1_idx] ON [dbo].[jobseekers]([user_id]);

-- CreateIndex
    CREATE NONCLUSTERED INDEX [jobseekers_private_data_fk_user_learner_private_data_user1] ON [dbo].[jobseekers_private_data]([jobseeker_id]);

-- CreateIndex
    CREATE NONCLUSTERED INDEX [fk_jobseeker_education_jobseeker1_idx] ON [dbo].[jobseekers_education]([jobseeker_id]);

-- CreateIndex
    CREATE NONCLUSTERED INDEX [fk_jobseeker_education_edu_institution1_idx] ON [dbo].[jobseekers_education]([edu_provider_id]);

-- CreateIndex
    CREATE NONCLUSTERED INDEX [pathway_has_skills_fk_Pathways_has_skill_Pathways1_idx] ON [dbo].[pathway_has_skills]([pathway_id]);

-- CreateIndex
    CREATE NONCLUSTERED INDEX [pathway_has_skills_fk_Pathways_has_skill_skill1_idx] ON [dbo].[pathway_has_skills]([skill_id]);

-- CreateIndex
    CREATE NONCLUSTERED INDEX [fk_pathway_subcategories_pathways1_idx] ON [dbo].[pathway_subcategories]([pathway_id]);

-- CreateIndex
    CREATE NONCLUSTERED INDEX [fk_proj_based_tech_assessments_Pathways1_idx] ON [dbo].[proj_based_tech_assessments]([pathway_id]);

-- CreateIndex
    CREATE NONCLUSTERED INDEX [project_experiences_fk_project_experience_jobseeker1_idx] ON [dbo].[project_experiences]([jobseeker_id]);

-- CreateIndex
    CREATE NONCLUSTERED INDEX [project_has_skills_fk_project_experience_has_skill_project_experience1_idx] ON [dbo].[project_has_skills]([proj_exp_id]);

-- CreateIndex
    CREATE NONCLUSTERED INDEX [project_has_skills_fk_project_experience_has_skill_skill1_idx] ON [dbo].[project_has_skills]([skill_id]);

-- CreateIndex
    CREATE NONCLUSTERED INDEX [sa_possible_answers_fk_sa_possible_answer_sa_question1_idx] ON [dbo].[sa_possible_answers]([sa_question_id]);

-- CreateIndex
    CREATE NONCLUSTERED INDEX [sa_questions_fk_sa_question_self_assessment1_idx] ON [dbo].[sa_questions]([self_assessment_id]);

-- CreateIndex
    CREATE NONCLUSTERED INDEX [fk_self_assessments_Pathways1_idx] ON [dbo].[self_assessments]([pathway_id]);

-- CreateIndex
    CREATE NONCLUSTERED INDEX [skills_fk_skill_skill_category_idx] ON [dbo].[skills]([skill_subcategory_id]);

-- CreateIndex
    CREATE NONCLUSTERED INDEX [fk_training_program_has_skills_skills1_idx] ON [dbo].[provider_program_has_skills]([skill_id]);

-- CreateIndex
    CREATE NONCLUSTERED INDEX [fk_training_program_has_skills_training_program1_idx] ON [dbo].[provider_program_has_skills]([training_program_id]);

-- CreateIndex
    CREATE NONCLUSTERED INDEX [training_programs_fk_training_program_training_provider1_idx] ON [dbo].[provider_programs]([edu_provider_id]);

-- CreateIndex
    CREATE NONCLUSTERED INDEX [training_programs_fk_training_program_Pathways1_idx] ON [dbo].[provider_programs]([pathway_id]);

-- CreateIndex
    CREATE NONCLUSTERED INDEX [volunteer_has_skills_fk_volunteer_has_skill_skill1_idx] ON [dbo].[volunteer_has_skills]([skill_id]);

-- CreateIndex
    CREATE NONCLUSTERED INDEX [volunteer_has_skills_fk_volunteer_has_skill_volunteer1_idx] ON [dbo].[volunteer_has_skills]([volunteer_id]);

-- CreateIndex
    CREATE NONCLUSTERED INDEX [volunteers_fk_mentor_user1_idx] ON [dbo].[volunteers]([user_id]);

-- CreateIndex
    CREATE NONCLUSTERED INDEX [fk_work_experience_jobseeker1_idx] ON [dbo].[work_experiences]([sector_id]);

-- CreateIndex
    CREATE NONCLUSTERED INDEX [fk_work_experiences_technology_areas1_idx] ON [dbo].[work_experiences]([tech_area_id]);

-- CreateIndex
    CREATE NONCLUSTERED INDEX [work_experiences_fk_work_experience_jobseeker1_idx] ON [dbo].[work_experiences]([jobseeker_id]);

-- CreateIndex
    CREATE NONCLUSTERED INDEX [postal_code_lat_lng_idx] ON [dbo].[postal_geo_data]([lat], [lng]);

-- CreateIndex
    CREATE NONCLUSTERED INDEX [_OtherPriorityPopulations_B_index] ON [dbo].[_OtherPriorityPopulations]([B]);

-- CreateIndex
    CREATE NONCLUSTERED INDEX [_JobPostingSkills_B_index] ON [dbo].[_JobPostingSkills]([B]);

-- AddForeignKey
    ALTER TABLE [dbo].[users] ADD CONSTRAINT [fk_user_address_postgeodata1] FOREIGN KEY ([zip]) REFERENCES [dbo].[postal_geo_data]([zip]) ON DELETE SET NULL ON UPDATE NO ACTION;

-- AddForeignKey
    ALTER TABLE [dbo].[Account] ADD CONSTRAINT [Account_user_id_fkey] FOREIGN KEY ([user_id]) REFERENCES [dbo].[users]([id]) ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
    ALTER TABLE [dbo].[Session] ADD CONSTRAINT [Session_userId_fkey] FOREIGN KEY ([userId]) REFERENCES [dbo].[users]([id]) ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
    ALTER TABLE [dbo].[Authenticator] ADD CONSTRAINT [Authenticator_userId_fkey] FOREIGN KEY ([userId]) REFERENCES [dbo].[users]([id]) ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
    ALTER TABLE [dbo].[certificates] ADD CONSTRAINT [fk_certificates_jobseeker1] FOREIGN KEY ([jobseeker_id]) REFERENCES [dbo].[jobseekers]([jobseeker_id]) ON DELETE CASCADE ON UPDATE NO ACTION;

-- AddForeignKey
    ALTER TABLE [dbo].[cfa_admin] ADD CONSTRAINT [fk_admin_contacts1] FOREIGN KEY ([user_id]) REFERENCES [dbo].[users]([id]) ON DELETE NO ACTION ON UPDATE NO ACTION;

-- AddForeignKey
    ALTER TABLE [dbo].[companies] ADD CONSTRAINT [companies_createdBy_fkey] FOREIGN KEY ([createdBy]) REFERENCES [dbo].[users]([id]) ON DELETE NO ACTION ON UPDATE CASCADE;

-- AddForeignKey
    ALTER TABLE [dbo].[companies] ADD CONSTRAINT [fk_company_industry_sectors1] FOREIGN KEY ([industry_sector_id]) REFERENCES [dbo].[industry_sectors]([industry_sector_id]) ON DELETE SET NULL ON UPDATE NO ACTION;

-- AddForeignKey
    ALTER TABLE [dbo].[bookmarked_jobseekers] ADD CONSTRAINT [fk_jobseekers1] FOREIGN KEY ([jobseeker_id]) REFERENCES [dbo].[jobseekers]([jobseeker_id]) ON DELETE NO ACTION ON UPDATE NO ACTION;

-- AddForeignKey
    ALTER TABLE [dbo].[bookmarked_jobseekers] ADD CONSTRAINT [fk_companies1] FOREIGN KEY ([company_id]) REFERENCES [dbo].[companies]([company_id]) ON DELETE NO ACTION ON UPDATE NO ACTION;

-- AddForeignKey
    ALTER TABLE [dbo].[bookmarked_jobseekers] ADD CONSTRAINT [fk_employers1] FOREIGN KEY ([employer_id]) REFERENCES [dbo].[employers]([employer_id]) ON DELETE SET NULL ON UPDATE NO ACTION;

-- AddForeignKey
    ALTER TABLE [dbo].[company_addresses] ADD CONSTRAINT [fk_company_address_company1] FOREIGN KEY ([company_id]) REFERENCES [dbo].[companies]([company_id]) ON DELETE NO ACTION ON UPDATE NO ACTION;

-- AddForeignKey
    ALTER TABLE [dbo].[company_addresses] ADD CONSTRAINT [fk_company_address_postgeodata1] FOREIGN KEY ([zip_region]) REFERENCES [dbo].[postal_geo_data]([zip]) ON DELETE NO ACTION ON UPDATE NO ACTION;

-- AddForeignKey
    ALTER TABLE [dbo].[company_social_links] ADD CONSTRAINT [fk_social_media_company_company1] FOREIGN KEY ([company_id]) REFERENCES [dbo].[companies]([company_id]) ON DELETE NO ACTION ON UPDATE NO ACTION;

-- AddForeignKey
    ALTER TABLE [dbo].[company_social_links] ADD CONSTRAINT [fk_social_media_company_social_media_platform1] FOREIGN KEY ([social_platform_id]) REFERENCES [dbo].[social_media_platforms]([social_platform_id]) ON DELETE NO ACTION ON UPDATE NO ACTION;

-- AddForeignKey
    ALTER TABLE [dbo].[company_social_links] ADD CONSTRAINT [fk_social_media_employer_employer1] FOREIGN KEY ([employer_id]) REFERENCES [dbo].[employers]([employer_id]) ON DELETE SET NULL ON UPDATE NO ACTION;

-- AddForeignKey
    ALTER TABLE [dbo].[company_testimonials] ADD CONSTRAINT [fk_company_testimonials_company1] FOREIGN KEY ([company_id]) REFERENCES [dbo].[companies]([company_id]) ON DELETE NO ACTION ON UPDATE NO ACTION;

-- AddForeignKey
    ALTER TABLE [dbo].[company_testimonials] ADD CONSTRAINT [fk_company_testimonals_employer1] FOREIGN KEY ([employer_id]) REFERENCES [dbo].[employers]([employer_id]) ON DELETE SET NULL ON UPDATE CASCADE;

-- AddForeignKey
    ALTER TABLE [dbo].[edu_providers] ADD CONSTRAINT [edu_providers_userId_fkey] FOREIGN KEY ([userId]) REFERENCES [dbo].[users]([id]) ON DELETE SET NULL ON UPDATE CASCADE;

-- AddForeignKey
    ALTER TABLE [dbo].[ProviderTestimonials] ADD CONSTRAINT [ProviderTestimonials_eduProviderId_fkey] FOREIGN KEY ([eduProviderId]) REFERENCES [dbo].[edu_providers]([id]) ON DELETE NO ACTION ON UPDATE CASCADE;

-- AddForeignKey
    ALTER TABLE [dbo].[edu_addresses] ADD CONSTRAINT [fk_edu_address_edu_institution1] FOREIGN KEY ([edu_provider_id]) REFERENCES [dbo].[edu_providers]([id]) ON DELETE NO ACTION ON UPDATE NO ACTION;

-- AddForeignKey
    ALTER TABLE [dbo].[edu_addresses] ADD CONSTRAINT [fk_edu_address_postgeodata1] FOREIGN KEY ([zip]) REFERENCES [dbo].[postal_geo_data]([zip]) ON DELETE NO ACTION ON UPDATE NO ACTION;

-- AddForeignKey
    ALTER TABLE [dbo].[educators] ADD CONSTRAINT [fk_educators_contacts1] FOREIGN KEY ([user_id]) REFERENCES [dbo].[users]([id]) ON DELETE NO ACTION ON UPDATE NO ACTION;

-- AddForeignKey
    ALTER TABLE [dbo].[educators] ADD CONSTRAINT [fk_educators_edu_institution1] FOREIGN KEY ([edu_providers_id]) REFERENCES [dbo].[edu_providers]([id]) ON DELETE NO ACTION ON UPDATE NO ACTION;

-- AddForeignKey
    ALTER TABLE [dbo].[TraineeDetail] ADD CONSTRAINT [fk_traineeDetail_jobseekers1] FOREIGN KEY ([jobseekerId]) REFERENCES [dbo].[jobseekers]([jobseeker_id]) ON DELETE CASCADE ON UPDATE NO ACTION;

-- AddForeignKey
    ALTER TABLE [dbo].[CareerPrepAssessment] ADD CONSTRAINT [fk_career_prep_app_jobseeker1] FOREIGN KEY ([jobseekerId]) REFERENCES [dbo].[jobseekers]([jobseeker_id]) ON DELETE NO ACTION ON UPDATE NO ACTION;

-- AddForeignKey
    ALTER TABLE [dbo].[CybersecurityRating] ADD CONSTRAINT [fk_cybersecurity_rating_career_prep_assessment1] FOREIGN KEY ([jobseekerId]) REFERENCES [dbo].[CareerPrepAssessment]([jobseekerId]) ON DELETE NO ACTION ON UPDATE CASCADE;

-- AddForeignKey
    ALTER TABLE [dbo].[DataAnalyticsRating] ADD CONSTRAINT [fk_data_analytics_rating_career_prep_assessment1] FOREIGN KEY ([jobseekerId]) REFERENCES [dbo].[CareerPrepAssessment]([jobseekerId]) ON DELETE NO ACTION ON UPDATE CASCADE;

-- AddForeignKey
    ALTER TABLE [dbo].[ITCloudRating] ADD CONSTRAINT [fk_it_cloud_rating_career_prep_assessment1] FOREIGN KEY ([jobseekerId]) REFERENCES [dbo].[CareerPrepAssessment]([jobseekerId]) ON DELETE NO ACTION ON UPDATE CASCADE;

-- AddForeignKey
    ALTER TABLE [dbo].[SoftwareDevRating] ADD CONSTRAINT [fk_software_dev_rating_career_prep_assessment1] FOREIGN KEY ([jobseekerId]) REFERENCES [dbo].[CareerPrepAssessment]([jobseekerId]) ON DELETE NO ACTION ON UPDATE CASCADE;

-- AddForeignKey
    ALTER TABLE [dbo].[DurableSkillsRating] ADD CONSTRAINT [fk_durable_skills_rating_career_prep_assessment1] FOREIGN KEY ([jobseekerId]) REFERENCES [dbo].[CareerPrepAssessment]([jobseekerId]) ON DELETE NO ACTION ON UPDATE CASCADE;

-- AddForeignKey
    ALTER TABLE [dbo].[BrandingRating] ADD CONSTRAINT [fk_branding_rating_career_prep_assessment1] FOREIGN KEY ([jobseekerId]) REFERENCES [dbo].[CareerPrepAssessment]([jobseekerId]) ON DELETE NO ACTION ON UPDATE CASCADE;

-- AddForeignKey
    ALTER TABLE [dbo].[CaseMgmt] ADD CONSTRAINT [CaseMgmt_jobseekerId_fkey] FOREIGN KEY ([jobseekerId]) REFERENCES [dbo].[CareerPrepAssessment]([jobseekerId]) ON DELETE NO ACTION ON UPDATE CASCADE;

-- AddForeignKey
    ALTER TABLE [dbo].[CaseMgmt] ADD CONSTRAINT [fk_case_mgmt_user1] FOREIGN KEY ([managerId]) REFERENCES [dbo].[users]([id]) ON DELETE SET NULL ON UPDATE NO ACTION;

-- AddForeignKey
    ALTER TABLE [dbo].[CaseMgmtNotes] ADD CONSTRAINT [fk_case_mgmt_notes_case_mgmt1] FOREIGN KEY ([jobseekerId]) REFERENCES [dbo].[CareerPrepAssessment]([jobseekerId]) ON DELETE NO ACTION ON UPDATE NO ACTION;

-- AddForeignKey
    ALTER TABLE [dbo].[CaseMgmtNotes] ADD CONSTRAINT [fk_case_mgmt_notes_user1] FOREIGN KEY ([createdBy]) REFERENCES [dbo].[users]([id]) ON DELETE NO ACTION ON UPDATE NO ACTION;

-- AddForeignKey
    ALTER TABLE [dbo].[employers] ADD CONSTRAINT [fk_employer_user1] FOREIGN KEY ([user_id]) REFERENCES [dbo].[users]([id]) ON DELETE NO ACTION ON UPDATE NO ACTION;

-- AddForeignKey
    ALTER TABLE [dbo].[employers] ADD CONSTRAINT [fk_employers_company1] FOREIGN KEY ([company_id]) REFERENCES [dbo].[companies]([company_id]) ON DELETE SET NULL ON UPDATE NO ACTION;

-- AddForeignKey
    ALTER TABLE [dbo].[employers] ADD CONSTRAINT [fk_employers_company_addresses] FOREIGN KEY ([work_address_id]) REFERENCES [dbo].[company_addresses]([company_address_id]) ON DELETE SET NULL ON UPDATE NO ACTION;

-- AddForeignKey
    ALTER TABLE [dbo].[job_postings] ADD CONSTRAINT [fk_job_postings_companies1] FOREIGN KEY ([company_id]) REFERENCES [dbo].[companies]([company_id]) ON DELETE NO ACTION ON UPDATE NO ACTION;

-- AddForeignKey
    ALTER TABLE [dbo].[job_postings] ADD CONSTRAINT [fk_job_postings_employers1] FOREIGN KEY ([employer_id]) REFERENCES [dbo].[employers]([employer_id]) ON DELETE SET NULL ON UPDATE NO ACTION;

-- AddForeignKey
    ALTER TABLE [dbo].[job_postings] ADD CONSTRAINT [fk_job_postings_technology_areas1] FOREIGN KEY ([tech_area_id]) REFERENCES [dbo].[technology_areas]([id]) ON DELETE SET NULL ON UPDATE NO ACTION;

-- AddForeignKey
    ALTER TABLE [dbo].[job_postings] ADD CONSTRAINT [fk_job_postings_company_addresses1] FOREIGN KEY ([location_id]) REFERENCES [dbo].[company_addresses]([company_address_id]) ON DELETE NO ACTION ON UPDATE NO ACTION;

-- AddForeignKey
    ALTER TABLE [dbo].[job_postings] ADD CONSTRAINT [fk_job_postings_industry_sectors1] FOREIGN KEY ([sector_id]) REFERENCES [dbo].[industry_sectors]([industry_sector_id]) ON DELETE NO ACTION ON UPDATE NO ACTION;

-- AddForeignKey
    ALTER TABLE [dbo].[JobseekerJobPosting] ADD CONSTRAINT [JobseekerJobPosting_jobPostId_fkey] FOREIGN KEY ([jobPostId]) REFERENCES [dbo].[job_postings]([job_posting_id]) ON DELETE NO ACTION ON UPDATE CASCADE;

-- AddForeignKey
    ALTER TABLE [dbo].[JobseekerJobPosting] ADD CONSTRAINT [JobseekerJobPosting_jobseekerId_fkey] FOREIGN KEY ([jobseekerId]) REFERENCES [dbo].[jobseekers]([jobseeker_id]) ON DELETE NO ACTION ON UPDATE CASCADE;

-- AddForeignKey
    ALTER TABLE [dbo].[jobseeker_has_skills] ADD CONSTRAINT [fk_jobseeker_has_skill_jobseeker1] FOREIGN KEY ([jobseeker_id]) REFERENCES [dbo].[jobseekers]([jobseeker_id]) ON DELETE CASCADE ON UPDATE NO ACTION;

-- AddForeignKey
    ALTER TABLE [dbo].[jobseeker_has_skills] ADD CONSTRAINT [fk_jobseeker_has_skill_skill1] FOREIGN KEY ([skill_id]) REFERENCES [dbo].[skills]([skill_id]) ON DELETE NO ACTION ON UPDATE NO ACTION;

-- AddForeignKey
    ALTER TABLE [dbo].[jobseekers] ADD CONSTRAINT [fk_jobseeker_Pathways1] FOREIGN KEY ([targeted_pathway]) REFERENCES [dbo].[pathways]([pathway_id]) ON DELETE SET NULL ON UPDATE NO ACTION;

-- AddForeignKey
    ALTER TABLE [dbo].[jobseekers] ADD CONSTRAINT [fk_learner_user1] FOREIGN KEY ([user_id]) REFERENCES [dbo].[users]([id]) ON DELETE NO ACTION ON UPDATE NO ACTION;

-- AddForeignKey
    ALTER TABLE [dbo].[jobseekers_private_data] ADD CONSTRAINT [fk_user_learner_private_data_user1] FOREIGN KEY ([jobseeker_id]) REFERENCES [dbo].[jobseekers]([jobseeker_id]) ON DELETE CASCADE ON UPDATE NO ACTION;

-- AddForeignKey
    ALTER TABLE [dbo].[jobseekers_education] ADD CONSTRAINT [fk_jobseeker_education_jobseeker1] FOREIGN KEY ([jobseeker_id]) REFERENCES [dbo].[jobseekers]([jobseeker_id]) ON DELETE CASCADE ON UPDATE NO ACTION;

-- AddForeignKey
    ALTER TABLE [dbo].[jobseekers_education] ADD CONSTRAINT [fk_jobseeker_education_edu_institution1] FOREIGN KEY ([edu_provider_id]) REFERENCES [dbo].[edu_providers]([id]) ON DELETE NO ACTION ON UPDATE CASCADE;

-- AddForeignKey
    ALTER TABLE [dbo].[jobseekers_education] ADD CONSTRAINT [fk_jobseeker_education_programs1] FOREIGN KEY ([program_id]) REFERENCES [dbo].[programs]([id]) ON DELETE SET NULL ON UPDATE NO ACTION;

-- AddForeignKey
    ALTER TABLE [dbo].[JobPlacement] ADD CONSTRAINT [fk_job_placement_jobseeker1] FOREIGN KEY ([job_placement_id]) REFERENCES [dbo].[jobseekers]([jobseeker_id]) ON DELETE NO ACTION ON UPDATE NO ACTION;

-- AddForeignKey
    ALTER TABLE [dbo].[JobPlacement] ADD CONSTRAINT [fk_job_placement_companies1] FOREIGN KEY ([companyId]) REFERENCES [dbo].[companies]([company_id]) ON DELETE SET NULL ON UPDATE NO ACTION;

-- AddForeignKey
    ALTER TABLE [dbo].[pathway_has_skills] ADD CONSTRAINT [fk_Pathways_has_skill_Pathways1] FOREIGN KEY ([pathway_id]) REFERENCES [dbo].[pathways]([pathway_id]) ON DELETE NO ACTION ON UPDATE NO ACTION;

-- AddForeignKey
    ALTER TABLE [dbo].[pathway_has_skills] ADD CONSTRAINT [fk_Pathways_has_skill_skill1] FOREIGN KEY ([skill_id]) REFERENCES [dbo].[skills]([skill_id]) ON DELETE NO ACTION ON UPDATE NO ACTION;

-- AddForeignKey
    ALTER TABLE [dbo].[pathway_subcategories] ADD CONSTRAINT [fk_pathway_subcategories_pathways1] FOREIGN KEY ([pathway_id]) REFERENCES [dbo].[pathways]([pathway_id]) ON DELETE NO ACTION ON UPDATE NO ACTION;

-- AddForeignKey
    ALTER TABLE [dbo].[proj_based_tech_assessments] ADD CONSTRAINT [fk_proj_based_tech_assessments_Pathways1] FOREIGN KEY ([pathway_id]) REFERENCES [dbo].[pathways]([pathway_id]) ON DELETE NO ACTION ON UPDATE NO ACTION;

-- AddForeignKey
    ALTER TABLE [dbo].[project_experiences] ADD CONSTRAINT [fk_project_experience_jobseeker1] FOREIGN KEY ([jobseeker_id]) REFERENCES [dbo].[jobseekers]([jobseeker_id]) ON DELETE CASCADE ON UPDATE NO ACTION;

-- AddForeignKey
    ALTER TABLE [dbo].[project_has_skills] ADD CONSTRAINT [fk_project_experience_has_skill_project_experience1] FOREIGN KEY ([proj_exp_id]) REFERENCES [dbo].[project_experiences]([proj_exp_id]) ON DELETE CASCADE ON UPDATE NO ACTION;

-- AddForeignKey
    ALTER TABLE [dbo].[project_has_skills] ADD CONSTRAINT [fk_project_experience_has_skill_skill1] FOREIGN KEY ([skill_id]) REFERENCES [dbo].[skills]([skill_id]) ON DELETE NO ACTION ON UPDATE NO ACTION;

-- AddForeignKey
    ALTER TABLE [dbo].[sa_possible_answers] ADD CONSTRAINT [fk_sa_possilbe_answer_sa_question1] FOREIGN KEY ([sa_question_id]) REFERENCES [dbo].[sa_questions]([sa_question_id]) ON DELETE NO ACTION ON UPDATE NO ACTION;

-- AddForeignKey
    ALTER TABLE [dbo].[sa_questions] ADD CONSTRAINT [fk_sa_question_self_assessment] FOREIGN KEY ([self_assessment_id]) REFERENCES [dbo].[self_assessments]([self_assessment_id]) ON DELETE NO ACTION ON UPDATE NO ACTION;

-- AddForeignKey
    ALTER TABLE [dbo].[self_assessments] ADD CONSTRAINT [fk_self_assessments_Pathways1] FOREIGN KEY ([pathway_id]) REFERENCES [dbo].[pathways]([pathway_id]) ON DELETE NO ACTION ON UPDATE NO ACTION;

-- AddForeignKey
    ALTER TABLE [dbo].[skills] ADD CONSTRAINT [fk_skill_skill_category] FOREIGN KEY ([skill_subcategory_id]) REFERENCES [dbo].[skill_subcategories]([skill_subcategory_id]) ON DELETE NO ACTION ON UPDATE NO ACTION;

-- AddForeignKey
    ALTER TABLE [dbo].[provider_program_has_skills] ADD CONSTRAINT [fk_training_program_has_skills_skills1] FOREIGN KEY ([skill_id]) REFERENCES [dbo].[skills]([skill_id]) ON DELETE NO ACTION ON UPDATE NO ACTION;

-- AddForeignKey
    ALTER TABLE [dbo].[provider_program_has_skills] ADD CONSTRAINT [fk_training_program_has_skills_training_program1] FOREIGN KEY ([training_program_id]) REFERENCES [dbo].[provider_programs]([training_program_id]) ON DELETE NO ACTION ON UPDATE NO ACTION;

-- AddForeignKey
    ALTER TABLE [dbo].[provider_programs] ADD CONSTRAINT [fk_training_program_training_provider1] FOREIGN KEY ([edu_provider_id]) REFERENCES [dbo].[edu_providers]([id]) ON DELETE NO ACTION ON UPDATE NO ACTION;

-- AddForeignKey
    ALTER TABLE [dbo].[provider_programs] ADD CONSTRAINT [fk_provider_programs_programs1] FOREIGN KEY ([program_id]) REFERENCES [dbo].[programs]([id]) ON DELETE NO ACTION ON UPDATE NO ACTION;

-- AddForeignKey
    ALTER TABLE [dbo].[volunteer_has_skills] ADD CONSTRAINT [fk_volunteer_has_skill_skill1] FOREIGN KEY ([skill_id]) REFERENCES [dbo].[skills]([skill_id]) ON DELETE NO ACTION ON UPDATE NO ACTION;

-- AddForeignKey
    ALTER TABLE [dbo].[volunteer_has_skills] ADD CONSTRAINT [fk_volunteer_has_skill_volunteer1] FOREIGN KEY ([volunteer_id]) REFERENCES [dbo].[volunteers]([volunteer_id]) ON DELETE NO ACTION ON UPDATE NO ACTION;

-- AddForeignKey
    ALTER TABLE [dbo].[volunteers] ADD CONSTRAINT [fk_mentor_user1] FOREIGN KEY ([user_id]) REFERENCES [dbo].[users]([id]) ON DELETE NO ACTION ON UPDATE NO ACTION;

-- AddForeignKey
    ALTER TABLE [dbo].[work_experiences] ADD CONSTRAINT [fk_work_experience_jobseeker1] FOREIGN KEY ([jobseeker_id]) REFERENCES [dbo].[jobseekers]([jobseeker_id]) ON DELETE CASCADE ON UPDATE NO ACTION;

-- AddForeignKey
    ALTER TABLE [dbo].[work_experiences] ADD CONSTRAINT [fk_work_experiences_technology_areas1] FOREIGN KEY ([tech_area_id]) REFERENCES [dbo].[technology_areas]([id]) ON DELETE SET NULL ON UPDATE NO ACTION;

-- AddForeignKey
    ALTER TABLE [dbo].[work_experiences] ADD CONSTRAINT [fk_work_eperiences_industry_sectors1] FOREIGN KEY ([sector_id]) REFERENCES [dbo].[industry_sectors]([industry_sector_id]) ON DELETE SET NULL ON UPDATE NO ACTION;

-- AddForeignKey
    ALTER TABLE [dbo].[_OtherPriorityPopulations] ADD CONSTRAINT [_OtherPriorityPopulations_A_fkey] FOREIGN KEY ([A]) REFERENCES [dbo].[OtherPriorityPopulations]([id]) ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
    ALTER TABLE [dbo].[_OtherPriorityPopulations] ADD CONSTRAINT [_OtherPriorityPopulations_B_fkey] FOREIGN KEY ([B]) REFERENCES [dbo].[TraineeDetail]([jobseekerId]) ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
    ALTER TABLE [dbo].[_JobPostingSkills] ADD CONSTRAINT [_JobPostingSkills_A_fkey] FOREIGN KEY ([A]) REFERENCES [dbo].[job_postings]([job_posting_id]) ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
    ALTER TABLE [dbo].[_JobPostingSkills] ADD CONSTRAINT [_JobPostingSkills_B_fkey] FOREIGN KEY ([B]) REFERENCES [dbo].[skills]([skill_id]) ON DELETE CASCADE ON UPDATE CASCADE;

    COMMIT TRAN;

END TRY
BEGIN CATCH

    IF @@TRANCOUNT > 0
        BEGIN
            ROLLBACK TRAN;
        END;
    THROW

END CATCH
