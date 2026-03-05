-- =================================================================
-- PostgreSQL schema for watechcoalition reference data (dbo schema)
-- Generated from pg_dump, cleaned for idempotent seeding.
--
-- Agent-managed tables (raw_ingested_jobs, normalized_jobs,
-- job_ingestion_runs) are NOT included — they are created by
-- agents/common/data_store/migrations.py:run_migrations().
--
-- Usage: psql -U postgres -d talent_finder -f schema.sql
--        (or executed by seed_pg_database.py)
-- =================================================================

-- Extensions
CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

--
-- PostgreSQL database dump
--


-- Dumped from database version 16.13 (Debian 16.13-1.pgdg12+1)
-- Dumped by pg_dump version 16.13 (Debian 16.13-1.pgdg12+1)


--
-- Name: dbo; Type: SCHEMA; Schema: -; Owner: -
--

CREATE SCHEMA IF NOT EXISTS dbo;


--
-- Name: _jobpostingskills; Type: TABLE; Schema: dbo; Owner: -
--

CREATE TABLE dbo._jobpostingskills (
    a text NOT NULL,
    b text NOT NULL
);


--
-- Name: _otherprioritypopulations; Type: TABLE; Schema: dbo; Owner: -
--

CREATE TABLE dbo._otherprioritypopulations (
    a text NOT NULL,
    b text NOT NULL
);


--
-- Name: _prisma_migrations; Type: TABLE; Schema: dbo; Owner: -
--

CREATE TABLE dbo._prisma_migrations (
    id text NOT NULL,
    checksum text NOT NULL,
    finished_at timestamp with time zone,
    migration_name character varying(250) NOT NULL,
    logs character varying,
    rolled_back_at timestamp with time zone,
    started_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    applied_steps_count integer DEFAULT 0 NOT NULL
);


--
-- Name: account; Type: TABLE; Schema: dbo; Owner: -
--

CREATE TABLE dbo.account (
    id text NOT NULL,
    user_id text NOT NULL,
    type character varying(255) NOT NULL,
    provider character varying(255) NOT NULL,
    provider_account_id character varying(255) NOT NULL,
    refresh_token character varying,
    access_token character varying,
    expires_at integer,
    token_type character varying(255) DEFAULT NULL::character varying,
    scope character varying(255) DEFAULT NULL::character varying,
    id_token character varying,
    session_state character varying(255) DEFAULT NULL::character varying,
    refresh_token_expires_in integer,
    createdat timestamp with time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updatedat timestamp with time zone NOT NULL
);


--
-- Name: authenticator; Type: TABLE; Schema: dbo; Owner: -
--

CREATE TABLE dbo.authenticator (
    credentialid character varying(255) NOT NULL,
    userid text NOT NULL,
    provideraccountid character varying(255) NOT NULL,
    credentialpublickey character varying NOT NULL,
    counter integer NOT NULL,
    credentialdevicetype character varying(255) NOT NULL,
    credentialbackedup boolean NOT NULL,
    transports character varying(255) DEFAULT NULL::character varying
);


--
-- Name: bookmarked_jobseekers; Type: TABLE; Schema: dbo; Owner: -
--

CREATE TABLE dbo.bookmarked_jobseekers (
    id text NOT NULL,
    jobseeker_id text NOT NULL,
    company_id text NOT NULL,
    employer_id text,
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP NOT NULL
);


--
-- Name: brandingrating; Type: TABLE; Schema: dbo; Owner: -
--

CREATE TABLE dbo.brandingrating (
    jobseekerid text NOT NULL,
    personalbrand smallint NOT NULL,
    onlinepresence smallint NOT NULL,
    elevatorpitch smallint NOT NULL,
    resumeeffectiveness smallint NOT NULL,
    coverlettereffectiveness smallint NOT NULL,
    interviewexperience smallint NOT NULL,
    responsetechnique smallint NOT NULL,
    followupimportance smallint NOT NULL,
    onlinenetworking smallint NOT NULL,
    eventnetworking smallint NOT NULL,
    relationshipmanagement smallint NOT NULL,
    jobsearchstrategy smallint NOT NULL,
    materialdistribution smallint NOT NULL,
    networkingtechniques smallint NOT NULL,
    onboardingbestpractices smallint NOT NULL,
    developmentplan smallint NOT NULL,
    mentorship smallint NOT NULL,
    updatedat timestamp with time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    overallaverage numeric,
    createdat timestamp with time zone DEFAULT CURRENT_TIMESTAMP NOT NULL
);


--
-- Name: careerprepassessment; Type: TABLE; Schema: dbo; Owner: -
--

CREATE TABLE dbo.careerprepassessment (
    jobseekerid text NOT NULL,
    assessmentdate timestamp with time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    interestpathway text,
    pronouns text NOT NULL,
    expectededucompletion text NOT NULL,
    experiencewithapplying boolean NOT NULL,
    experiencewithinterview boolean NOT NULL,
    prevworkexperience boolean DEFAULT false NOT NULL,
    streetaddress text,
    prioritypopulations text,
    updatedat timestamp with time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    createdat timestamp with time zone DEFAULT CURRENT_TIMESTAMP NOT NULL
);


--
-- Name: casemgmt; Type: TABLE; Schema: dbo; Owner: -
--

CREATE TABLE dbo.casemgmt (
    jobseekerid text NOT NULL,
    managerid text,
    prepenrollmentstatus text NOT NULL,
    careerpreptrack text,
    prepstartdate timestamp with time zone,
    prepexpectedenddate timestamp with time zone,
    prepactualenddate timestamp with time zone,
    createdat timestamp with time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updatedat timestamp with time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    assignedcareerpreptrack text
);


--
-- Name: casemgmtnotes; Type: TABLE; Schema: dbo; Owner: -
--

CREATE TABLE dbo.casemgmtnotes (
    id character varying(1000) DEFAULT public.uuid_generate_v4() NOT NULL,
    jobseekerid text NOT NULL,
    date timestamp with time zone,
    notetype text NOT NULL,
    notecontent text NOT NULL,
    createdby text NOT NULL,
    createdat timestamp with time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updatedat timestamp with time zone DEFAULT CURRENT_TIMESTAMP NOT NULL
);


--
-- Name: certificates; Type: TABLE; Schema: dbo; Owner: -
--

CREATE TABLE dbo.certificates (
    certification_id text NOT NULL,
    jobseeker_id text NOT NULL,
    name text NOT NULL,
    logo_url text,
    issuing_org text NOT NULL,
    credential_id text,
    credential_url text,
    status text,
    issue_date timestamp with time zone,
    expiration_date timestamp with time zone,
    description text,
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP NOT NULL
);


--
-- Name: cfa_admin; Type: TABLE; Schema: dbo; Owner: -
--

CREATE TABLE dbo.cfa_admin (
    admin_id text NOT NULL,
    user_id text NOT NULL
);


--
-- Name: cip; Type: TABLE; Schema: dbo; Owner: -
--

CREATE TABLE dbo.cip (
    code character varying(1000) NOT NULL,
    title character varying(1000) NOT NULL,
    description character varying(1000) DEFAULT NULL::character varying,
    createdat timestamp with time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updatedat timestamp with time zone DEFAULT CURRENT_TIMESTAMP NOT NULL
);


--
-- Name: cip_to_socc_map; Type: TABLE; Schema: dbo; Owner: -
--

CREATE TABLE dbo.cip_to_socc_map (
    cip_code character varying(1000) NOT NULL,
    socc_id text NOT NULL,
    createdat timestamp with time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updatedat timestamp with time zone DEFAULT CURRENT_TIMESTAMP NOT NULL
);


--
-- Name: companies; Type: TABLE; Schema: dbo; Owner: -
--

CREATE TABLE dbo.companies (
    company_id text NOT NULL,
    industry_sector_id text,
    company_name text NOT NULL,
    company_logo_url text,
    about_us text,
    company_email text,
    year_founded integer,
    company_website_url text,
    company_video_url text,
    company_phone text,
    company_mission text,
    company_vision text,
    size text DEFAULT '1-10'::text,
    estimated_annual_hires integer,
    is_approved boolean DEFAULT false NOT NULL,
    createdby text,
    createdat timestamp with time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updatedat timestamp with time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    contact_name text,
    engagementtype character varying(1000) DEFAULT 'Lead'::character varying
);


--
-- Name: company_addresses; Type: TABLE; Schema: dbo; Owner: -
--

CREATE TABLE dbo.company_addresses (
    company_address_id text NOT NULL,
    company_id text NOT NULL,
    zip_region text NOT NULL,
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP NOT NULL
);


--
-- Name: company_social_links; Type: TABLE; Schema: dbo; Owner: -
--

CREATE TABLE dbo.company_social_links (
    social_media_id text NOT NULL,
    company_id text NOT NULL,
    employer_id text,
    social_platform_id text NOT NULL,
    social_url text NOT NULL
);


--
-- Name: company_testimonials; Type: TABLE; Schema: dbo; Owner: -
--

CREATE TABLE dbo.company_testimonials (
    testimonial_id text NOT NULL,
    company_id text NOT NULL,
    employer_id text,
    text text NOT NULL,
    author text NOT NULL
);


--
-- Name: cybersecurityrating; Type: TABLE; Schema: dbo; Owner: -
--

CREATE TABLE dbo.cybersecurityrating (
    jobseekerid text NOT NULL,
    networking smallint NOT NULL,
    projectmanagement smallint NOT NULL,
    securitytools smallint NOT NULL,
    operatingsystems smallint NOT NULL,
    programming smallint NOT NULL,
    cryptography smallint NOT NULL,
    cloudsecurity smallint NOT NULL,
    incidentresponse smallint NOT NULL,
    datasecurity smallint NOT NULL,
    technicalsupport smallint NOT NULL,
    computationalthinking smallint NOT NULL,
    apiusage smallint NOT NULL,
    updatedat timestamp with time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    overallaverage numeric,
    createdat timestamp with time zone DEFAULT CURRENT_TIMESTAMP NOT NULL
);


--
-- Name: dataanalyticsrating; Type: TABLE; Schema: dbo; Owner: -
--

CREATE TABLE dbo.dataanalyticsrating (
    jobseekerid text NOT NULL,
    dataanalysis smallint NOT NULL,
    sqlprogramming smallint NOT NULL,
    pythonpackages smallint NOT NULL,
    datascience smallint NOT NULL,
    dataengineering smallint NOT NULL,
    tableau smallint NOT NULL,
    machinelearning smallint NOT NULL,
    rprogramming smallint NOT NULL,
    projectmanagement smallint NOT NULL,
    datavisualization smallint NOT NULL,
    datastructures smallint NOT NULL,
    bigocomplexity smallint NOT NULL,
    sortingalgorithms smallint NOT NULL,
    databases smallint NOT NULL,
    computationalthinking smallint NOT NULL,
    updatedat timestamp with time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    overallaverage numeric,
    createdat timestamp with time zone DEFAULT CURRENT_TIMESTAMP NOT NULL
);


--
-- Name: durableskillsrating; Type: TABLE; Schema: dbo; Owner: -
--

CREATE TABLE dbo.durableskillsrating (
    jobseekerid text NOT NULL,
    emotionmanagement smallint NOT NULL,
    empathy smallint NOT NULL,
    goalsetting smallint NOT NULL,
    timemanagement smallint NOT NULL,
    adaptability smallint NOT NULL,
    criticalthinking smallint NOT NULL,
    creativity smallint NOT NULL,
    resilience smallint NOT NULL,
    communication smallint NOT NULL,
    activelistening smallint NOT NULL,
    conflictresolution smallint NOT NULL,
    nonverbalcommunication smallint NOT NULL,
    teamwork smallint NOT NULL,
    trustbuilding smallint NOT NULL,
    leadership smallint NOT NULL,
    perspectivetaking smallint NOT NULL,
    culturalawareness smallint NOT NULL,
    relationshipbuilding smallint NOT NULL,
    documentationskills smallint NOT NULL,
    updatedat timestamp with time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    overallaverage numeric,
    createdat timestamp with time zone DEFAULT CURRENT_TIMESTAMP NOT NULL
);


--
-- Name: edu_addresses; Type: TABLE; Schema: dbo; Owner: -
--

CREATE TABLE dbo.edu_addresses (
    edu_address_id text NOT NULL,
    edu_provider_id text NOT NULL,
    street1 text NOT NULL,
    street2 text,
    zip text NOT NULL,
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP NOT NULL
);


--
-- Name: edu_providers; Type: TABLE; Schema: dbo; Owner: -
--

CREATE TABLE dbo.edu_providers (
    id text DEFAULT public.uuid_generate_v4() NOT NULL,
    edu_type text,
    name text NOT NULL,
    contact text,
    contact_email text,
    edu_url text,
    mission text,
    providerdescription text,
    setsapartstatement text,
    screeningcriteria text,
    recruitingsources text,
    programcount text,
    cost text,
    isadminreviewed boolean DEFAULT false NOT NULL,
    iscoalitionmember boolean DEFAULT false NOT NULL,
    userid text,
    logourl text DEFAULT ''::text,
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP NOT NULL
);


--
-- Name: educators; Type: TABLE; Schema: dbo; Owner: -
--

CREATE TABLE dbo.educators (
    educator_id text NOT NULL,
    user_id text NOT NULL,
    edu_providers_id text NOT NULL,
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP NOT NULL
);


--
-- Name: employerjobrolefeedback; Type: TABLE; Schema: dbo; Owner: -
--

CREATE TABLE dbo.employerjobrolefeedback (
    id text DEFAULT public.uuid_generate_v4() NOT NULL,
    jobroleid text NOT NULL,
    skillid text NOT NULL,
    likertrating integer NOT NULL,
    submiterid text NOT NULL,
    createdat timestamp with time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updatedat timestamp with time zone DEFAULT CURRENT_TIMESTAMP NOT NULL
);


--
-- Name: employers; Type: TABLE; Schema: dbo; Owner: -
--

CREATE TABLE dbo.employers (
    employer_id text NOT NULL,
    user_id text NOT NULL,
    company_id text,
    work_address_id text,
    job_title text,
    linkedin_url text,
    is_verified_employee boolean DEFAULT false NOT NULL,
    createdat timestamp with time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updatedat timestamp with time zone DEFAULT CURRENT_TIMESTAMP NOT NULL
);


--
-- Name: events; Type: TABLE; Schema: dbo; Owner: -
--

CREATE TABLE dbo.events (
    id text DEFAULT public.uuid_generate_v4() NOT NULL,
    name text NOT NULL,
    description text,
    location text DEFAULT 'Remote'::text NOT NULL,
    date timestamp with time zone NOT NULL,
    blurb text,
    eventtype text NOT NULL,
    createdat timestamp with time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updatedat timestamp with time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    createdbyid text,
    duration integer DEFAULT 90 NOT NULL,
    joinmeetinglink text,
    registrationlink text,
    recordinglink text
);


--
-- Name: events_on_users; Type: TABLE; Schema: dbo; Owner: -
--

CREATE TABLE dbo.events_on_users (
    id text DEFAULT public.uuid_generate_v4() NOT NULL,
    eventid text NOT NULL,
    userid text NOT NULL,
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP NOT NULL
);


--
-- Name: industry_sectors; Type: TABLE; Schema: dbo; Owner: -
--

CREATE TABLE dbo.industry_sectors (
    industry_sector_id text NOT NULL,
    sector_title text NOT NULL,
    createdat timestamp with time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updatedat timestamp with time zone DEFAULT CURRENT_TIMESTAMP NOT NULL
);


--
-- Name: itcloudrating; Type: TABLE; Schema: dbo; Owner: -
--

CREATE TABLE dbo.itcloudrating (
    jobseekerid text NOT NULL,
    techsupport smallint NOT NULL,
    activedirectory smallint NOT NULL,
    projectmanagement smallint NOT NULL,
    helpdesksupport smallint NOT NULL,
    windowsservers smallint NOT NULL,
    sqlprogramming smallint NOT NULL,
    computerhardware smallint NOT NULL,
    operatingsystems smallint NOT NULL,
    systemadmin smallint NOT NULL,
    networkadmin smallint NOT NULL,
    virtualization smallint NOT NULL,
    corecloudservices smallint NOT NULL,
    apiusage smallint NOT NULL,
    httpresponsecodes smallint NOT NULL,
    computationalthinking smallint NOT NULL,
    updatedat timestamp with time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    overallaverage numeric,
    createdat timestamp with time zone DEFAULT CURRENT_TIMESTAMP NOT NULL
);


--
-- Name: job_postings; Type: TABLE; Schema: dbo; Owner: -
--

CREATE TABLE dbo.job_postings (
    job_posting_id text NOT NULL,
    company_id text NOT NULL,
    location_id text NOT NULL,
    employer_id text,
    tech_area_id text,
    sector_id text,
    job_title text NOT NULL,
    job_description text NOT NULL,
    is_internship boolean DEFAULT false NOT NULL,
    is_paid boolean DEFAULT true NOT NULL,
    employment_type character varying(255) DEFAULT 'full-time'::character varying NOT NULL,
    location character varying(255) NOT NULL,
    salary_range text NOT NULL,
    county text NOT NULL,
    zip text NOT NULL,
    publish_date timestamp with time zone NOT NULL,
    unpublish_date timestamp with time zone NOT NULL,
    job_post_url text,
    assessment_url text,
    offer_visa_sponsorship boolean DEFAULT false NOT NULL,
    relocation_services_available boolean DEFAULT false NOT NULL,
    is_apprenticeship boolean DEFAULT false NOT NULL,
    earn_and_learn_type text,
    occupation_code text,
    employment_duration text,
    end_date timestamp with time zone,
    start_date timestamp with time zone,
    career_services_offered boolean,
    minimumeducationlevel text,
    requiredcertifications text,
    trainingrequirements text,
    createdat timestamp with time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updatedat timestamp with time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    status character varying(1000) DEFAULT 'open'::character varying,
    source text,
    external_id text,
    ingestion_run_id text,
    ai_relevance_score double precision,
    quality_score double precision,
    is_spam boolean,
    spam_score double precision,
    overall_confidence double precision,
    field_confidence jsonb
);


--
-- Name: jobplacement; Type: TABLE; Schema: dbo; Owner: -
--

CREATE TABLE dbo.jobplacement (
    job_placement_id text DEFAULT public.uuid_generate_v4() NOT NULL,
    companyid text,
    employmentstatus text,
    jobstartdate timestamp with time zone,
    employmenttype text,
    earnlearntype text,
    naicscode text,
    employername text NOT NULL,
    hourlyearnings text NOT NULL,
    createdat timestamp with time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updatedat timestamp with time zone DEFAULT CURRENT_TIMESTAMP NOT NULL
);


--
-- Name: jobrole; Type: TABLE; Schema: dbo; Owner: -
--

CREATE TABLE dbo.jobrole (
    id text DEFAULT public.uuid_generate_v4() NOT NULL,
    pathwayid text,
    title text NOT NULL,
    joblevel text NOT NULL,
    jobdescription text,
    principaltasks text,
    principalskills text,
    aiimpact text,
    keyinsights text,
    aitransformation text,
    onetcode text,
    createdat timestamp with time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updatedat timestamp with time zone DEFAULT CURRENT_TIMESTAMP NOT NULL
);


--
-- Name: jobroleskill; Type: TABLE; Schema: dbo; Owner: -
--

CREATE TABLE dbo.jobroleskill (
    id text DEFAULT public.uuid_generate_v4() NOT NULL,
    jobroleid text NOT NULL,
    skillid text NOT NULL,
    aiimpact text NOT NULL,
    currentproficiency text NOT NULL,
    futurerelevance text NOT NULL,
    trainingrequired boolean DEFAULT false NOT NULL,
    createdat timestamp with time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updatedat timestamp with time zone DEFAULT CURRENT_TIMESTAMP NOT NULL
);


--
-- Name: jobroletraining; Type: TABLE; Schema: dbo; Owner: -
--

CREATE TABLE dbo.jobroletraining (
    id text DEFAULT public.uuid_generate_v4() NOT NULL,
    jobroleid text NOT NULL,
    trainingid text NOT NULL,
    createdat timestamp with time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updatedat timestamp with time zone DEFAULT CURRENT_TIMESTAMP NOT NULL
);


--
-- Name: jobseeker_has_skills; Type: TABLE; Schema: dbo; Owner: -
--

CREATE TABLE dbo.jobseeker_has_skills (
    jobseeker_id text NOT NULL,
    skill_id text NOT NULL,
    createdat timestamp with time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updatedat timestamp with time zone DEFAULT CURRENT_TIMESTAMP NOT NULL
);


--
-- Name: jobseekerjobposting; Type: TABLE; Schema: dbo; Owner: -
--

CREATE TABLE dbo.jobseekerjobposting (
    id text NOT NULL,
    jobpostid text NOT NULL,
    jobseekerid text NOT NULL,
    jobstatus text DEFAULT 'Not Selected'::text NOT NULL,
    savedat timestamp with time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    applieddate timestamp with time zone,
    followupdate timestamp with time zone,
    isbookmarked boolean DEFAULT false,
    feedbackrating smallint,
    feedbacktext text,
    employerclickedconnect boolean DEFAULT false NOT NULL,
    createdat timestamp with time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updatedat timestamp with time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    analysisdate timestamp with time zone,
    elevatorpitch text,
    generatedresume text,
    linkedinprofileupdate text,
    totalmatchscore double precision,
    gapanalysis text
);


--
-- Name: jobseekerjobpostingskillmatch; Type: TABLE; Schema: dbo; Owner: -
--

CREATE TABLE dbo.jobseekerjobpostingskillmatch (
    jobseekerjobpostingid text NOT NULL,
    jobskill text NOT NULL,
    jobseekerskill text NOT NULL,
    matchscore double precision NOT NULL
);


--
-- Name: jobseekers; Type: TABLE; Schema: dbo; Owner: -
--

CREATE TABLE dbo.jobseekers (
    jobseeker_id text NOT NULL,
    user_id text NOT NULL,
    targeted_pathway text,
    is_enrolled_ed_program boolean NOT NULL,
    highest_level_of_study_completed text,
    current_grade_level text,
    current_enrolled_ed_program text,
    intern_hours_required smallint DEFAULT '0'::smallint NOT NULL,
    intro_headline text,
    current_job_title text,
    linkedin_url text,
    years_work_exp smallint DEFAULT '0'::smallint NOT NULL,
    months_internship_exp smallint,
    portfolio_url text,
    portfolio_password character varying(255) DEFAULT NULL::character varying,
    video_url text,
    employment_type_sought character varying(255) DEFAULT NULL::character varying,
    is_marked_deletion timestamp with time zone,
    assignedpool text,
    careerprepcomplete boolean DEFAULT false NOT NULL,
    careerpreptrackrecommendation text,
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at timestamp with time zone,
    prescreened boolean DEFAULT false NOT NULL,
    hasresume boolean DEFAULT false NOT NULL
);


--
-- Name: jobseekers_education; Type: TABLE; Schema: dbo; Owner: -
--

CREATE TABLE dbo.jobseekers_education (
    jobseeker_ed_id text DEFAULT public.uuid_generate_v4() NOT NULL,
    jobseeker_id text NOT NULL,
    edu_provider_id text NOT NULL,
    program_id text,
    ed_program character varying(45) NOT NULL,
    ed_system character varying(255) DEFAULT NULL::character varying,
    is_tech_degree boolean DEFAULT false,
    is_enrolled boolean NOT NULL,
    enrollment_status text DEFAULT 'unknown'::text NOT NULL,
    start_date date NOT NULL,
    graduation_date date NOT NULL,
    degree_type character varying(45) DEFAULT NULL::character varying,
    major character varying(45) DEFAULT NULL::character varying,
    minor character varying(45) DEFAULT NULL::character varying,
    gpa character varying(45) DEFAULT NULL::character varying,
    description text,
    createdat timestamp with time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updatedat timestamp with time zone DEFAULT CURRENT_TIMESTAMP NOT NULL
);


--
-- Name: jobseekers_private_data; Type: TABLE; Schema: dbo; Owner: -
--

CREATE TABLE dbo.jobseekers_private_data (
    jobseeker_private_data_id text NOT NULL,
    jobseeker_id text NOT NULL,
    ssn text,
    is_authorized_to_work_in_usa boolean,
    job_sponsorship_required boolean,
    is_veteran text DEFAULT ''::text NOT NULL,
    disability_status text DEFAULT ''::text NOT NULL,
    disability text,
    gender text DEFAULT ''::text NOT NULL,
    race text DEFAULT ''::text NOT NULL,
    ethnicity text DEFAULT ''::text NOT NULL,
    createdat timestamp with time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updatedat timestamp with time zone DEFAULT CURRENT_TIMESTAMP NOT NULL
);


--
-- Name: meeting; Type: TABLE; Schema: dbo; Owner: -
--

CREATE TABLE dbo.meeting (
    id text DEFAULT public.uuid_generate_v4() NOT NULL,
    jobseekerid text NOT NULL,
    title text NOT NULL,
    meetingagenda text,
    meetingdate timestamp with time zone NOT NULL,
    updatedat timestamp with time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    createdat timestamp with time zone DEFAULT CURRENT_TIMESTAMP NOT NULL
);


--
-- Name: otherprioritypopulations; Type: TABLE; Schema: dbo; Owner: -
--

CREATE TABLE dbo.otherprioritypopulations (
    id text NOT NULL,
    option text NOT NULL,
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP NOT NULL
);


--
-- Name: pathway_has_skills; Type: TABLE; Schema: dbo; Owner: -
--

CREATE TABLE dbo.pathway_has_skills (
    pathway_id text NOT NULL,
    skill_id text NOT NULL,
    createdat timestamp with time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updatedat timestamp with time zone DEFAULT CURRENT_TIMESTAMP NOT NULL
);


--
-- Name: pathway_subcategories; Type: TABLE; Schema: dbo; Owner: -
--

CREATE TABLE dbo.pathway_subcategories (
    pathway_subcategory_id text NOT NULL,
    pathway_id text NOT NULL,
    pw_subcategory_name text NOT NULL,
    subcategory_assessment_url text,
    createdat timestamp with time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updatedat timestamp with time zone DEFAULT CURRENT_TIMESTAMP NOT NULL
);


--
-- Name: pathways; Type: TABLE; Schema: dbo; Owner: -
--

CREATE TABLE dbo.pathways (
    pathway_id text NOT NULL,
    pathway_title text NOT NULL,
    description text,
    tooltip text,
    createdat timestamp with time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updatedat timestamp with time zone DEFAULT CURRENT_TIMESTAMP NOT NULL
);


--
-- Name: pathwaytraining; Type: TABLE; Schema: dbo; Owner: -
--

CREATE TABLE dbo.pathwaytraining (
    id text DEFAULT public.uuid_generate_v4() NOT NULL,
    pathwayid text,
    trainingid text NOT NULL,
    createdat timestamp with time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updatedat timestamp with time zone DEFAULT CURRENT_TIMESTAMP NOT NULL
);


--
-- Name: postal_geo_data; Type: TABLE; Schema: dbo; Owner: -
--

CREATE TABLE dbo.postal_geo_data (
    zip text NOT NULL,
    city character varying(100) NOT NULL,
    county character varying(100) NOT NULL,
    state_code text NOT NULL,
    state character varying(100) NOT NULL,
    lat double precision NOT NULL,
    lng double precision NOT NULL
);


--
-- Name: programs; Type: TABLE; Schema: dbo; Owner: -
--

CREATE TABLE dbo.programs (
    id text NOT NULL,
    title character varying(255) NOT NULL,
    createdat timestamp with time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updatedat timestamp with time zone DEFAULT CURRENT_TIMESTAMP NOT NULL
);


--
-- Name: proj_based_tech_assessments; Type: TABLE; Schema: dbo; Owner: -
--

CREATE TABLE dbo.proj_based_tech_assessments (
    proj_based_tech_assessment_id text NOT NULL,
    pathway_id text NOT NULL,
    url text NOT NULL,
    title text NOT NULL
);


--
-- Name: project_experiences; Type: TABLE; Schema: dbo; Owner: -
--

CREATE TABLE dbo.project_experiences (
    proj_exp_id text DEFAULT public.uuid_generate_v4() NOT NULL,
    jobseeker_id text NOT NULL,
    project_title text NOT NULL,
    jobseeker_role text NOT NULL,
    start_date timestamp with time zone NOT NULL,
    completion_date timestamp with time zone NOT NULL,
    problem_solved_description text NOT NULL,
    team_size smallint NOT NULL,
    repo_url text,
    demo_url text,
    createdat timestamp with time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updatedat timestamp with time zone DEFAULT CURRENT_TIMESTAMP NOT NULL
);


--
-- Name: project_has_skills; Type: TABLE; Schema: dbo; Owner: -
--

CREATE TABLE dbo.project_has_skills (
    proj_exp_id text NOT NULL,
    skill_id text NOT NULL,
    createdat timestamp with time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updatedat timestamp with time zone DEFAULT CURRENT_TIMESTAMP NOT NULL
);


--
-- Name: provider_program_has_skills; Type: TABLE; Schema: dbo; Owner: -
--

CREATE TABLE dbo.provider_program_has_skills (
    training_program_id text NOT NULL,
    skill_id text NOT NULL,
    createdat timestamp with time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updatedat timestamp with time zone DEFAULT CURRENT_TIMESTAMP NOT NULL
);


--
-- Name: provider_programs; Type: TABLE; Schema: dbo; Owner: -
--

CREATE TABLE dbo.provider_programs (
    training_program_id text NOT NULL,
    program_id text NOT NULL,
    edu_provider_id text NOT NULL,
    pathway_id text,
    target_job_roles text,
    description text,
    months text,
    hoursperweek text,
    targetpopulation text,
    servicearea text,
    pathways text,
    programdescription text,
    about text,
    costsummary text,
    edulevel text,
    faq text,
    fees character varying(1000) DEFAULT NULL::character varying,
    getstartedurl text,
    locationtype text,
    locations text,
    programlength text,
    tuition text,
    createdat timestamp with time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updatedat timestamp with time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    cipcode character varying(1000) DEFAULT NULL::character varying,
    awardtype character varying(100) DEFAULT NULL::character varying
);


--
-- Name: providertestimonials; Type: TABLE; Schema: dbo; Owner: -
--

CREATE TABLE dbo.providertestimonials (
    id text DEFAULT public.uuid_generate_v4() NOT NULL,
    eduproviderid text NOT NULL,
    url text,
    author text,
    quote text
);


--
-- Name: ragrecordmanager; Type: TABLE; Schema: dbo; Owner: -
--

CREATE TABLE dbo.ragrecordmanager (
    id text DEFAULT public.uuid_generate_v4() NOT NULL,
    updatedat timestamp with time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    createdat timestamp with time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    fileid text NOT NULL,
    hash text NOT NULL
);


--
-- Name: sa_possible_answers; Type: TABLE; Schema: dbo; Owner: -
--

CREATE TABLE dbo.sa_possible_answers (
    sa_possible_answer_id text NOT NULL,
    sa_question_id text NOT NULL,
    answer_text text,
    is_correct boolean DEFAULT true NOT NULL
);


--
-- Name: sa_questions; Type: TABLE; Schema: dbo; Owner: -
--

CREATE TABLE dbo.sa_questions (
    sa_question_id text NOT NULL,
    self_assessment_id text NOT NULL,
    question_topic character varying(255) NOT NULL,
    question_type character varying(255) NOT NULL,
    text text NOT NULL,
    option_count integer
);


--
-- Name: self_assessments; Type: TABLE; Schema: dbo; Owner: -
--

CREATE TABLE dbo.self_assessments (
    self_assessment_id text NOT NULL,
    pathway_id text NOT NULL
);


--
-- Name: session; Type: TABLE; Schema: dbo; Owner: -
--

CREATE TABLE dbo.session (
    id text NOT NULL,
    sessiontoken character varying(255) NOT NULL,
    userid text NOT NULL,
    expires timestamp with time zone NOT NULL,
    createdat timestamp with time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updatedat timestamp with time zone NOT NULL
);


--
-- Name: skill_subcategories; Type: TABLE; Schema: dbo; Owner: -
--

CREATE TABLE dbo.skill_subcategories (
    skill_subcategory_id text DEFAULT public.uuid_generate_v4() NOT NULL,
    subcategory_name text NOT NULL,
    subcategory_description text NOT NULL,
    createdat timestamp with time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updatedat timestamp with time zone DEFAULT CURRENT_TIMESTAMP NOT NULL
);


--
-- Name: skills; Type: TABLE; Schema: dbo; Owner: -
--

CREATE TABLE dbo.skills (
    skill_id text NOT NULL,
    skill_subcategory_id text NOT NULL,
    skill_name text NOT NULL,
    skill_info_url text DEFAULT ''::text NOT NULL,
    embedding public.vector,
    skill_type text,
    createdat timestamp with time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updatedat timestamp with time zone DEFAULT CURRENT_TIMESTAMP NOT NULL
);


--
-- Name: socc; Type: TABLE; Schema: dbo; Owner: -
--

CREATE TABLE dbo.socc (
    id text DEFAULT public.uuid_generate_v4() NOT NULL,
    code character varying(1000) NOT NULL,
    title character varying(1000) NOT NULL,
    description character varying(1000) DEFAULT NULL::character varying,
    version text NOT NULL,
    createdat timestamp with time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updatedat timestamp with time zone DEFAULT CURRENT_TIMESTAMP NOT NULL
);


--
-- Name: socc2018_to_cip2020_map; Type: TABLE; Schema: dbo; Owner: -
--

CREATE TABLE dbo.socc2018_to_cip2020_map (
    socc_code character varying(1000) NOT NULL,
    cip_code character varying(1000) NOT NULL
);


--
-- Name: socc_2010; Type: TABLE; Schema: dbo; Owner: -
--

CREATE TABLE dbo.socc_2010 (
    socc_code character varying(1000) NOT NULL,
    title character varying(1000) NOT NULL,
    description character varying(1000) DEFAULT NULL::character varying
);


--
-- Name: socc_2018; Type: TABLE; Schema: dbo; Owner: -
--

CREATE TABLE dbo.socc_2018 (
    socc_code character varying(1000) NOT NULL,
    title character varying(1000) NOT NULL,
    description character varying(1000) DEFAULT NULL::character varying
);


--
-- Name: social_media_platforms; Type: TABLE; Schema: dbo; Owner: -
--

CREATE TABLE dbo.social_media_platforms (
    social_platform_id text NOT NULL,
    platform text NOT NULL,
    social_logo_url text NOT NULL,
    createdat timestamp with time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updatedat timestamp with time zone DEFAULT CURRENT_TIMESTAMP NOT NULL
);


--
-- Name: softwaredevrating; Type: TABLE; Schema: dbo; Owner: -
--

CREATE TABLE dbo.softwaredevrating (
    jobseekerid text NOT NULL,
    softwareengineering smallint NOT NULL,
    softwaredevelopmentlifecycle smallint NOT NULL,
    programminglanguages smallint NOT NULL,
    datastructuresandalgorithms smallint NOT NULL,
    softwarearchitecture smallint NOT NULL,
    versioncontrol smallint NOT NULL,
    databasemanagement smallint NOT NULL,
    devops smallint NOT NULL,
    cloudcomputing smallint NOT NULL,
    conceptualsystemsthinking smallint NOT NULL,
    problemsolving smallint NOT NULL,
    fundamentalcodingconcepts smallint NOT NULL,
    debugging smallint NOT NULL,
    computationalthinking smallint NOT NULL,
    softwareoptimization smallint NOT NULL,
    updatedat timestamp with time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    overallaverage numeric,
    createdat timestamp with time zone DEFAULT CURRENT_TIMESTAMP NOT NULL
);


--
-- Name: technology_areas; Type: TABLE; Schema: dbo; Owner: -
--

CREATE TABLE dbo.technology_areas (
    id text NOT NULL,
    title text NOT NULL,
    createdat timestamp with time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updatedat timestamp with time zone DEFAULT CURRENT_TIMESTAMP NOT NULL
);


--
-- Name: traineedetail; Type: TABLE; Schema: dbo; Owner: -
--

CREATE TABLE dbo.traineedetail (
    isverified boolean DEFAULT false NOT NULL,
    firstname text NOT NULL,
    lastname text NOT NULL,
    programtitle text NOT NULL,
    enrollmentstatus text NOT NULL,
    startdate date NOT NULL,
    exitdate date NOT NULL,
    noncompletionreason text,
    jobseekeredid text NOT NULL,
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP NOT NULL
);


--
-- Name: training; Type: TABLE; Schema: dbo; Owner: -
--

CREATE TABLE dbo.training (
    id text DEFAULT public.uuid_generate_v4() NOT NULL,
    title text NOT NULL,
    url text NOT NULL,
    provider text,
    skillsdeveloped text,
    createdat timestamp with time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updatedat timestamp with time zone DEFAULT CURRENT_TIMESTAMP NOT NULL
);


--
-- Name: users; Type: TABLE; Schema: dbo; Owner: -
--

CREATE TABLE dbo.users (
    id text DEFAULT public.uuid_generate_v4() NOT NULL,
    role text NOT NULL,
    first_name text,
    last_name text,
    birthdate timestamp with time zone,
    email text NOT NULL,
    email_verified timestamp with time zone,
    phonecountrycode text,
    phone text,
    zip text,
    photo_url text,
    has_agreed_terms boolean DEFAULT false NOT NULL,
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    is_marked_deletion timestamp with time zone,
    sendcareeropportunities boolean DEFAULT false,
    sendnewjobposts boolean DEFAULT false
);


--
-- Name: verificationtoken; Type: TABLE; Schema: dbo; Owner: -
--

CREATE TABLE dbo.verificationtoken (
    identifier character varying(255) NOT NULL,
    token character varying(255) NOT NULL,
    expires timestamp with time zone NOT NULL
);


--
-- Name: volunteer_has_skills; Type: TABLE; Schema: dbo; Owner: -
--

CREATE TABLE dbo.volunteer_has_skills (
    volunteer_skills_id text NOT NULL,
    volunteer_id text NOT NULL,
    skill_id text NOT NULL,
    createdat timestamp with time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updatedat timestamp with time zone DEFAULT CURRENT_TIMESTAMP NOT NULL
);


--
-- Name: volunteers; Type: TABLE; Schema: dbo; Owner: -
--

CREATE TABLE dbo.volunteers (
    volunteer_id text NOT NULL,
    user_id text NOT NULL,
    volunteer_type character varying(255) NOT NULL,
    createdat timestamp with time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updatedat timestamp with time zone DEFAULT CURRENT_TIMESTAMP NOT NULL
);


--
-- Name: work_experiences; Type: TABLE; Schema: dbo; Owner: -
--

CREATE TABLE dbo.work_experiences (
    work_id text NOT NULL,
    jobseeker_id text NOT NULL,
    tech_area_id text,
    sector_id text,
    company text NOT NULL,
    is_internship boolean DEFAULT false NOT NULL,
    job_title text NOT NULL,
    is_current_job boolean DEFAULT false NOT NULL,
    start_date timestamp with time zone NOT NULL,
    end_date timestamp with time zone,
    responsibilities text NOT NULL,
    createdat timestamp with time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updatedat timestamp with time zone DEFAULT CURRENT_TIMESTAMP NOT NULL
);


--
-- Name: _prisma_migrations idx_16739_pk___prisma___3213e83f70b780de; Type: CONSTRAINT; Schema: dbo; Owner: -
--

ALTER TABLE ONLY dbo._prisma_migrations
    ADD CONSTRAINT idx_16739_pk___prisma___3213e83f70b780de PRIMARY KEY (id);


--
-- Name: account idx_16746_account_pkey; Type: CONSTRAINT; Schema: dbo; Owner: -
--

ALTER TABLE ONLY dbo.account
    ADD CONSTRAINT idx_16746_account_pkey PRIMARY KEY (id);


--
-- Name: authenticator idx_16755_authenticator_pkey; Type: CONSTRAINT; Schema: dbo; Owner: -
--

ALTER TABLE ONLY dbo.authenticator
    ADD CONSTRAINT idx_16755_authenticator_pkey PRIMARY KEY (userid, credentialid);


--
-- Name: bookmarked_jobseekers idx_16761_bookmarked_jobseekers_primary; Type: CONSTRAINT; Schema: dbo; Owner: -
--

ALTER TABLE ONLY dbo.bookmarked_jobseekers
    ADD CONSTRAINT idx_16761_bookmarked_jobseekers_primary PRIMARY KEY (id);


--
-- Name: brandingrating idx_16768_branding_rating_primary; Type: CONSTRAINT; Schema: dbo; Owner: -
--

ALTER TABLE ONLY dbo.brandingrating
    ADD CONSTRAINT idx_16768_branding_rating_primary PRIMARY KEY (jobseekerid);


--
-- Name: careerprepassessment idx_16775_career_prep_app_primary; Type: CONSTRAINT; Schema: dbo; Owner: -
--

ALTER TABLE ONLY dbo.careerprepassessment
    ADD CONSTRAINT idx_16775_career_prep_app_primary PRIMARY KEY (jobseekerid);


--
-- Name: casemgmt idx_16784_case_mgmt_primary; Type: CONSTRAINT; Schema: dbo; Owner: -
--

ALTER TABLE ONLY dbo.casemgmt
    ADD CONSTRAINT idx_16784_case_mgmt_primary PRIMARY KEY (jobseekerid);


--
-- Name: casemgmtnotes idx_16791_case_mgmt_notes_primary; Type: CONSTRAINT; Schema: dbo; Owner: -
--

ALTER TABLE ONLY dbo.casemgmtnotes
    ADD CONSTRAINT idx_16791_case_mgmt_notes_primary PRIMARY KEY (id);


--
-- Name: certificates idx_16799_certificates_primary; Type: CONSTRAINT; Schema: dbo; Owner: -
--

ALTER TABLE ONLY dbo.certificates
    ADD CONSTRAINT idx_16799_certificates_primary PRIMARY KEY (certification_id);


--
-- Name: cfa_admin idx_16806_cfa_admin_primary; Type: CONSTRAINT; Schema: dbo; Owner: -
--

ALTER TABLE ONLY dbo.cfa_admin
    ADD CONSTRAINT idx_16806_cfa_admin_primary PRIMARY KEY (admin_id);


--
-- Name: cip idx_16811_cip_pkey; Type: CONSTRAINT; Schema: dbo; Owner: -
--

ALTER TABLE ONLY dbo.cip
    ADD CONSTRAINT idx_16811_cip_pkey PRIMARY KEY (code);


--
-- Name: cip_to_socc_map idx_16819_cip_to_socc_primary; Type: CONSTRAINT; Schema: dbo; Owner: -
--

ALTER TABLE ONLY dbo.cip_to_socc_map
    ADD CONSTRAINT idx_16819_cip_to_socc_primary PRIMARY KEY (cip_code, socc_id);


--
-- Name: companies idx_16826_companies_primary; Type: CONSTRAINT; Schema: dbo; Owner: -
--

ALTER TABLE ONLY dbo.companies
    ADD CONSTRAINT idx_16826_companies_primary PRIMARY KEY (company_id);


--
-- Name: company_addresses idx_16836_company_addresses_primary; Type: CONSTRAINT; Schema: dbo; Owner: -
--

ALTER TABLE ONLY dbo.company_addresses
    ADD CONSTRAINT idx_16836_company_addresses_primary PRIMARY KEY (company_address_id);


--
-- Name: company_social_links idx_16843_company_social_links_primary; Type: CONSTRAINT; Schema: dbo; Owner: -
--

ALTER TABLE ONLY dbo.company_social_links
    ADD CONSTRAINT idx_16843_company_social_links_primary PRIMARY KEY (social_media_id);


--
-- Name: company_testimonials idx_16848_company_testimonials_primary; Type: CONSTRAINT; Schema: dbo; Owner: -
--

ALTER TABLE ONLY dbo.company_testimonials
    ADD CONSTRAINT idx_16848_company_testimonials_primary PRIMARY KEY (testimonial_id);


--
-- Name: cybersecurityrating idx_16853_cybersecurity_rating_primary; Type: CONSTRAINT; Schema: dbo; Owner: -
--

ALTER TABLE ONLY dbo.cybersecurityrating
    ADD CONSTRAINT idx_16853_cybersecurity_rating_primary PRIMARY KEY (jobseekerid);


--
-- Name: dataanalyticsrating idx_16860_data_analytics_rating_primary; Type: CONSTRAINT; Schema: dbo; Owner: -
--

ALTER TABLE ONLY dbo.dataanalyticsrating
    ADD CONSTRAINT idx_16860_data_analytics_rating_primary PRIMARY KEY (jobseekerid);


--
-- Name: durableskillsrating idx_16867_durable_skills_rating_primary; Type: CONSTRAINT; Schema: dbo; Owner: -
--

ALTER TABLE ONLY dbo.durableskillsrating
    ADD CONSTRAINT idx_16867_durable_skills_rating_primary PRIMARY KEY (jobseekerid);


--
-- Name: edu_addresses idx_16874_edu_addresses_primary; Type: CONSTRAINT; Schema: dbo; Owner: -
--

ALTER TABLE ONLY dbo.edu_addresses
    ADD CONSTRAINT idx_16874_edu_addresses_primary PRIMARY KEY (edu_address_id);


--
-- Name: edu_providers idx_16881_edu_providers_primary; Type: CONSTRAINT; Schema: dbo; Owner: -
--

ALTER TABLE ONLY dbo.edu_providers
    ADD CONSTRAINT idx_16881_edu_providers_primary PRIMARY KEY (id);


--
-- Name: educators idx_16892_educators_primary; Type: CONSTRAINT; Schema: dbo; Owner: -
--

ALTER TABLE ONLY dbo.educators
    ADD CONSTRAINT idx_16892_educators_primary PRIMARY KEY (educator_id);


--
-- Name: employerjobrolefeedback idx_16899_employerjobrolefeedback_pkey; Type: CONSTRAINT; Schema: dbo; Owner: -
--

ALTER TABLE ONLY dbo.employerjobrolefeedback
    ADD CONSTRAINT idx_16899_employerjobrolefeedback_pkey PRIMARY KEY (id);


--
-- Name: employers idx_16907_employers_primary; Type: CONSTRAINT; Schema: dbo; Owner: -
--

ALTER TABLE ONLY dbo.employers
    ADD CONSTRAINT idx_16907_employers_primary PRIMARY KEY (employer_id);


--
-- Name: events idx_16915_events_pkey; Type: CONSTRAINT; Schema: dbo; Owner: -
--

ALTER TABLE ONLY dbo.events
    ADD CONSTRAINT idx_16915_events_pkey PRIMARY KEY (id);


--
-- Name: events_on_users idx_16925_events_on_users_pkey; Type: CONSTRAINT; Schema: dbo; Owner: -
--

ALTER TABLE ONLY dbo.events_on_users
    ADD CONSTRAINT idx_16925_events_on_users_pkey PRIMARY KEY (id);


--
-- Name: industry_sectors idx_16933_industry_sectors_primary; Type: CONSTRAINT; Schema: dbo; Owner: -
--

ALTER TABLE ONLY dbo.industry_sectors
    ADD CONSTRAINT idx_16933_industry_sectors_primary PRIMARY KEY (industry_sector_id);


--
-- Name: itcloudrating idx_16940_it_cloud_rating_primary; Type: CONSTRAINT; Schema: dbo; Owner: -
--

ALTER TABLE ONLY dbo.itcloudrating
    ADD CONSTRAINT idx_16940_it_cloud_rating_primary PRIMARY KEY (jobseekerid);


--
-- Name: job_postings idx_16947_job_postings_primary; Type: CONSTRAINT; Schema: dbo; Owner: -
--

ALTER TABLE ONLY dbo.job_postings
    ADD CONSTRAINT idx_16947_job_postings_primary PRIMARY KEY (job_posting_id);


--
-- Name: jobplacement idx_16961_job_placement_primary; Type: CONSTRAINT; Schema: dbo; Owner: -
--

ALTER TABLE ONLY dbo.jobplacement
    ADD CONSTRAINT idx_16961_job_placement_primary PRIMARY KEY (job_placement_id);


--
-- Name: jobrole idx_16969_jobrole_pkey; Type: CONSTRAINT; Schema: dbo; Owner: -
--

ALTER TABLE ONLY dbo.jobrole
    ADD CONSTRAINT idx_16969_jobrole_pkey PRIMARY KEY (id);


--
-- Name: jobroleskill idx_16977_jobroleskill_pkey; Type: CONSTRAINT; Schema: dbo; Owner: -
--

ALTER TABLE ONLY dbo.jobroleskill
    ADD CONSTRAINT idx_16977_jobroleskill_pkey PRIMARY KEY (id);


--
-- Name: jobroletraining idx_16986_jobroletraining_pkey; Type: CONSTRAINT; Schema: dbo; Owner: -
--

ALTER TABLE ONLY dbo.jobroletraining
    ADD CONSTRAINT idx_16986_jobroletraining_pkey PRIMARY KEY (id);


--
-- Name: jobseeker_has_skills idx_16994_jobseeker_has_skills_primary; Type: CONSTRAINT; Schema: dbo; Owner: -
--

ALTER TABLE ONLY dbo.jobseeker_has_skills
    ADD CONSTRAINT idx_16994_jobseeker_has_skills_primary PRIMARY KEY (jobseeker_id, skill_id);


--
-- Name: jobseekerjobposting idx_17001_jobseeker_job_posting_primary; Type: CONSTRAINT; Schema: dbo; Owner: -
--

ALTER TABLE ONLY dbo.jobseekerjobposting
    ADD CONSTRAINT idx_17001_jobseeker_job_posting_primary PRIMARY KEY (id);


--
-- Name: jobseekerjobpostingskillmatch idx_17012_jobseekerjobpostingskillmatch_pkey; Type: CONSTRAINT; Schema: dbo; Owner: -
--

ALTER TABLE ONLY dbo.jobseekerjobpostingskillmatch
    ADD CONSTRAINT idx_17012_jobseekerjobpostingskillmatch_pkey PRIMARY KEY (jobseekerjobpostingid, jobskill);


--
-- Name: jobseekers idx_17017_jobseekers_primary; Type: CONSTRAINT; Schema: dbo; Owner: -
--

ALTER TABLE ONLY dbo.jobseekers
    ADD CONSTRAINT idx_17017_jobseekers_primary PRIMARY KEY (jobseeker_id);


--
-- Name: jobseekers_education idx_17030_jobseekers_education_pkey; Type: CONSTRAINT; Schema: dbo; Owner: -
--

ALTER TABLE ONLY dbo.jobseekers_education
    ADD CONSTRAINT idx_17030_jobseekers_education_pkey PRIMARY KEY (jobseeker_ed_id);


--
-- Name: jobseekers_private_data idx_17045_jobseekers_private_data_primary; Type: CONSTRAINT; Schema: dbo; Owner: -
--

ALTER TABLE ONLY dbo.jobseekers_private_data
    ADD CONSTRAINT idx_17045_jobseekers_private_data_primary PRIMARY KEY (jobseeker_private_data_id);


--
-- Name: meeting idx_17057_meeting_primary; Type: CONSTRAINT; Schema: dbo; Owner: -
--

ALTER TABLE ONLY dbo.meeting
    ADD CONSTRAINT idx_17057_meeting_primary PRIMARY KEY (id);


--
-- Name: otherprioritypopulations idx_17065_otherprioritypopulations_primary; Type: CONSTRAINT; Schema: dbo; Owner: -
--

ALTER TABLE ONLY dbo.otherprioritypopulations
    ADD CONSTRAINT idx_17065_otherprioritypopulations_primary PRIMARY KEY (id);


--
-- Name: pathway_has_skills idx_17072_pathway_has_skills_primary; Type: CONSTRAINT; Schema: dbo; Owner: -
--

ALTER TABLE ONLY dbo.pathway_has_skills
    ADD CONSTRAINT idx_17072_pathway_has_skills_primary PRIMARY KEY (pathway_id, skill_id);


--
-- Name: pathway_subcategories idx_17079_pathway_subcategories_primary; Type: CONSTRAINT; Schema: dbo; Owner: -
--

ALTER TABLE ONLY dbo.pathway_subcategories
    ADD CONSTRAINT idx_17079_pathway_subcategories_primary PRIMARY KEY (pathway_subcategory_id, pathway_id);


--
-- Name: pathways idx_17086_pathways_primary; Type: CONSTRAINT; Schema: dbo; Owner: -
--

ALTER TABLE ONLY dbo.pathways
    ADD CONSTRAINT idx_17086_pathways_primary PRIMARY KEY (pathway_id);


--
-- Name: pathwaytraining idx_17093_pathwaytraining_pkey; Type: CONSTRAINT; Schema: dbo; Owner: -
--

ALTER TABLE ONLY dbo.pathwaytraining
    ADD CONSTRAINT idx_17093_pathwaytraining_pkey PRIMARY KEY (id);


--
-- Name: postal_geo_data idx_17101_postal_codes_primary; Type: CONSTRAINT; Schema: dbo; Owner: -
--

ALTER TABLE ONLY dbo.postal_geo_data
    ADD CONSTRAINT idx_17101_postal_codes_primary PRIMARY KEY (zip);


--
-- Name: programs idx_17106_programs_pkey; Type: CONSTRAINT; Schema: dbo; Owner: -
--

ALTER TABLE ONLY dbo.programs
    ADD CONSTRAINT idx_17106_programs_pkey PRIMARY KEY (id);


--
-- Name: proj_based_tech_assessments idx_17113_proj_based_tech_assessments_primary; Type: CONSTRAINT; Schema: dbo; Owner: -
--

ALTER TABLE ONLY dbo.proj_based_tech_assessments
    ADD CONSTRAINT idx_17113_proj_based_tech_assessments_primary PRIMARY KEY (proj_based_tech_assessment_id);


--
-- Name: project_experiences idx_17118_project_experiences_primary; Type: CONSTRAINT; Schema: dbo; Owner: -
--

ALTER TABLE ONLY dbo.project_experiences
    ADD CONSTRAINT idx_17118_project_experiences_primary PRIMARY KEY (proj_exp_id);


--
-- Name: project_has_skills idx_17126_project_has_skills_primary; Type: CONSTRAINT; Schema: dbo; Owner: -
--

ALTER TABLE ONLY dbo.project_has_skills
    ADD CONSTRAINT idx_17126_project_has_skills_primary PRIMARY KEY (proj_exp_id, skill_id);


--
-- Name: provider_program_has_skills idx_17133_training_program_has_skills_primary; Type: CONSTRAINT; Schema: dbo; Owner: -
--

ALTER TABLE ONLY dbo.provider_program_has_skills
    ADD CONSTRAINT idx_17133_training_program_has_skills_primary PRIMARY KEY (training_program_id, skill_id);


--
-- Name: provider_programs idx_17140_training_programs_primary; Type: CONSTRAINT; Schema: dbo; Owner: -
--

ALTER TABLE ONLY dbo.provider_programs
    ADD CONSTRAINT idx_17140_training_programs_primary PRIMARY KEY (training_program_id);


--
-- Name: providertestimonials idx_17150_provider_testimonials_primary; Type: CONSTRAINT; Schema: dbo; Owner: -
--

ALTER TABLE ONLY dbo.providertestimonials
    ADD CONSTRAINT idx_17150_provider_testimonials_primary PRIMARY KEY (id);


--
-- Name: ragrecordmanager idx_17156_ragrecordmanager_pkey; Type: CONSTRAINT; Schema: dbo; Owner: -
--

ALTER TABLE ONLY dbo.ragrecordmanager
    ADD CONSTRAINT idx_17156_ragrecordmanager_pkey PRIMARY KEY (id);


--
-- Name: sa_possible_answers idx_17164_sa_possible_answers_primary; Type: CONSTRAINT; Schema: dbo; Owner: -
--

ALTER TABLE ONLY dbo.sa_possible_answers
    ADD CONSTRAINT idx_17164_sa_possible_answers_primary PRIMARY KEY (sa_possible_answer_id);


--
-- Name: sa_questions idx_17170_sa_questions_primary; Type: CONSTRAINT; Schema: dbo; Owner: -
--

ALTER TABLE ONLY dbo.sa_questions
    ADD CONSTRAINT idx_17170_sa_questions_primary PRIMARY KEY (sa_question_id);


--
-- Name: self_assessments idx_17175_self_assessments_primary; Type: CONSTRAINT; Schema: dbo; Owner: -
--

ALTER TABLE ONLY dbo.self_assessments
    ADD CONSTRAINT idx_17175_self_assessments_primary PRIMARY KEY (self_assessment_id);


--
-- Name: session idx_17180_session_pkey; Type: CONSTRAINT; Schema: dbo; Owner: -
--

ALTER TABLE ONLY dbo.session
    ADD CONSTRAINT idx_17180_session_pkey PRIMARY KEY (id);


--
-- Name: skill_subcategories idx_17186_skill_subcategories_primary; Type: CONSTRAINT; Schema: dbo; Owner: -
--

ALTER TABLE ONLY dbo.skill_subcategories
    ADD CONSTRAINT idx_17186_skill_subcategories_primary PRIMARY KEY (skill_subcategory_id);


--
-- Name: skills idx_17194_skills_primary; Type: CONSTRAINT; Schema: dbo; Owner: -
--

ALTER TABLE ONLY dbo.skills
    ADD CONSTRAINT idx_17194_skills_primary PRIMARY KEY (skill_id);


--
-- Name: socc idx_17202_socc_pkey; Type: CONSTRAINT; Schema: dbo; Owner: -
--

ALTER TABLE ONLY dbo.socc
    ADD CONSTRAINT idx_17202_socc_pkey PRIMARY KEY (id);


--
-- Name: socc_2010 idx_17211_socc_2010_pkey; Type: CONSTRAINT; Schema: dbo; Owner: -
--

ALTER TABLE ONLY dbo.socc_2010
    ADD CONSTRAINT idx_17211_socc_2010_pkey PRIMARY KEY (socc_code);


--
-- Name: socc_2018 idx_17217_socc_2018_pkey; Type: CONSTRAINT; Schema: dbo; Owner: -
--

ALTER TABLE ONLY dbo.socc_2018
    ADD CONSTRAINT idx_17217_socc_2018_pkey PRIMARY KEY (socc_code);


--
-- Name: socc2018_to_cip2020_map idx_17223_socc2018_to_cip2020_map_pkey; Type: CONSTRAINT; Schema: dbo; Owner: -
--

ALTER TABLE ONLY dbo.socc2018_to_cip2020_map
    ADD CONSTRAINT idx_17223_socc2018_to_cip2020_map_pkey PRIMARY KEY (socc_code, cip_code);


--
-- Name: social_media_platforms idx_17228_social_media_platforms_primary; Type: CONSTRAINT; Schema: dbo; Owner: -
--

ALTER TABLE ONLY dbo.social_media_platforms
    ADD CONSTRAINT idx_17228_social_media_platforms_primary PRIMARY KEY (social_platform_id);


--
-- Name: softwaredevrating idx_17235_software_dev_rating_primary; Type: CONSTRAINT; Schema: dbo; Owner: -
--

ALTER TABLE ONLY dbo.softwaredevrating
    ADD CONSTRAINT idx_17235_software_dev_rating_primary PRIMARY KEY (jobseekerid);


--
-- Name: technology_areas idx_17242_technology_areas_primary; Type: CONSTRAINT; Schema: dbo; Owner: -
--

ALTER TABLE ONLY dbo.technology_areas
    ADD CONSTRAINT idx_17242_technology_areas_primary PRIMARY KEY (id);


--
-- Name: traineedetail idx_17249_traineedetail_primary; Type: CONSTRAINT; Schema: dbo; Owner: -
--

ALTER TABLE ONLY dbo.traineedetail
    ADD CONSTRAINT idx_17249_traineedetail_primary PRIMARY KEY (jobseekeredid);


--
-- Name: training idx_17257_training_pkey; Type: CONSTRAINT; Schema: dbo; Owner: -
--

ALTER TABLE ONLY dbo.training
    ADD CONSTRAINT idx_17257_training_pkey PRIMARY KEY (id);


--
-- Name: users idx_17265_contacts_primary; Type: CONSTRAINT; Schema: dbo; Owner: -
--

ALTER TABLE ONLY dbo.users
    ADD CONSTRAINT idx_17265_contacts_primary PRIMARY KEY (id);


--
-- Name: volunteer_has_skills idx_17281_volunteer_has_skills_primary; Type: CONSTRAINT; Schema: dbo; Owner: -
--

ALTER TABLE ONLY dbo.volunteer_has_skills
    ADD CONSTRAINT idx_17281_volunteer_has_skills_primary PRIMARY KEY (volunteer_skills_id);


--
-- Name: volunteers idx_17288_volunteers_primary; Type: CONSTRAINT; Schema: dbo; Owner: -
--

ALTER TABLE ONLY dbo.volunteers
    ADD CONSTRAINT idx_17288_volunteers_primary PRIMARY KEY (volunteer_id);


--
-- Name: work_experiences idx_17295_work_experiences_primary; Type: CONSTRAINT; Schema: dbo; Owner: -
--

ALTER TABLE ONLY dbo.work_experiences
    ADD CONSTRAINT idx_17295_work_experiences_primary PRIMARY KEY (work_id);


--
-- Name: idx_16729__jobpostingskills_ab_unique; Type: INDEX; Schema: dbo; Owner: -
--

CREATE UNIQUE INDEX idx_16729__jobpostingskills_ab_unique ON dbo._jobpostingskills USING btree (a, b);


--
-- Name: idx_16729__jobpostingskills_b_index; Type: INDEX; Schema: dbo; Owner: -
--

CREATE INDEX idx_16729__jobpostingskills_b_index ON dbo._jobpostingskills USING btree (b);


--
-- Name: idx_16734__otherprioritypopulations_ab_unique; Type: INDEX; Schema: dbo; Owner: -
--

CREATE UNIQUE INDEX idx_16734__otherprioritypopulations_ab_unique ON dbo._otherprioritypopulations USING btree (a, b);


--
-- Name: idx_16734__otherprioritypopulations_b_index; Type: INDEX; Schema: dbo; Owner: -
--

CREATE INDEX idx_16734__otherprioritypopulations_b_index ON dbo._otherprioritypopulations USING btree (b);


--
-- Name: idx_16746_account_provider_provider_account_id_key; Type: INDEX; Schema: dbo; Owner: -
--

CREATE UNIQUE INDEX idx_16746_account_provider_provider_account_id_key ON dbo.account USING btree (provider, provider_account_id);


--
-- Name: idx_16746_account_user_id_idx; Type: INDEX; Schema: dbo; Owner: -
--

CREATE INDEX idx_16746_account_user_id_idx ON dbo.account USING btree (user_id);


--
-- Name: idx_16755_authenticator_credentialid_key; Type: INDEX; Schema: dbo; Owner: -
--

CREATE UNIQUE INDEX idx_16755_authenticator_credentialid_key ON dbo.authenticator USING btree (credentialid);


--
-- Name: idx_16784_fk_case_mgmt_admin1_idx; Type: INDEX; Schema: dbo; Owner: -
--

CREATE INDEX idx_16784_fk_case_mgmt_admin1_idx ON dbo.casemgmt USING btree (managerid);


--
-- Name: idx_16784_fk_case_mgmt_jobseeker1_idx; Type: INDEX; Schema: dbo; Owner: -
--

CREATE INDEX idx_16784_fk_case_mgmt_jobseeker1_idx ON dbo.casemgmt USING btree (jobseekerid);


--
-- Name: idx_16799_fk_certificates_jobseeker1_idx; Type: INDEX; Schema: dbo; Owner: -
--

CREATE INDEX idx_16799_fk_certificates_jobseeker1_idx ON dbo.certificates USING btree (jobseeker_id);


--
-- Name: idx_16806_cfa_admin_fk_admin_contacts1_idx; Type: INDEX; Schema: dbo; Owner: -
--

CREATE INDEX idx_16806_cfa_admin_fk_admin_contacts1_idx ON dbo.cfa_admin USING btree (user_id);


--
-- Name: idx_16826_companies_company_name_key; Type: INDEX; Schema: dbo; Owner: -
--

CREATE UNIQUE INDEX idx_16826_companies_company_name_key ON dbo.companies USING btree (company_name);


--
-- Name: idx_16826_companies_fk_company_industry_sectors1_idx; Type: INDEX; Schema: dbo; Owner: -
--

CREATE INDEX idx_16826_companies_fk_company_industry_sectors1_idx ON dbo.companies USING btree (industry_sector_id);


--
-- Name: idx_16836_company_addresses_company_id_zip_unique; Type: INDEX; Schema: dbo; Owner: -
--

CREATE UNIQUE INDEX idx_16836_company_addresses_company_id_zip_unique ON dbo.company_addresses USING btree (company_id, zip_region);


--
-- Name: idx_16836_company_addresses_fk_company_address_company1_idx; Type: INDEX; Schema: dbo; Owner: -
--

CREATE INDEX idx_16836_company_addresses_fk_company_address_company1_idx ON dbo.company_addresses USING btree (company_id);


--
-- Name: idx_16843_company_social_links_fk_social_media_company_company1; Type: INDEX; Schema: dbo; Owner: -
--

CREATE INDEX idx_16843_company_social_links_fk_social_media_company_company1 ON dbo.company_social_links USING btree (company_id);


--
-- Name: idx_16843_company_social_links_fk_social_media_company_social_m; Type: INDEX; Schema: dbo; Owner: -
--

CREATE INDEX idx_16843_company_social_links_fk_social_media_company_social_m ON dbo.company_social_links USING btree (social_platform_id);


--
-- Name: idx_16848_fk_company_testimonials_company1_idx; Type: INDEX; Schema: dbo; Owner: -
--

CREATE INDEX idx_16848_fk_company_testimonials_company1_idx ON dbo.company_testimonials USING btree (company_id);


--
-- Name: idx_16874_edu_addresses_fk_edu_address_edu_institution1_idx; Type: INDEX; Schema: dbo; Owner: -
--

CREATE INDEX idx_16874_edu_addresses_fk_edu_address_edu_institution1_idx ON dbo.edu_addresses USING btree (edu_provider_id);


--
-- Name: idx_16881_edu_providers_id_unique; Type: INDEX; Schema: dbo; Owner: -
--

CREATE UNIQUE INDEX idx_16881_edu_providers_id_unique ON dbo.edu_providers USING btree (id);


--
-- Name: idx_16881_edu_providers_name_key; Type: INDEX; Schema: dbo; Owner: -
--

CREATE UNIQUE INDEX idx_16881_edu_providers_name_key ON dbo.edu_providers USING btree (name);


--
-- Name: idx_16892_fk_educators_contacts1_idx; Type: INDEX; Schema: dbo; Owner: -
--

CREATE INDEX idx_16892_fk_educators_contacts1_idx ON dbo.educators USING btree (user_id);


--
-- Name: idx_16892_fk_educators_edu_institution1_idx; Type: INDEX; Schema: dbo; Owner: -
--

CREATE INDEX idx_16892_fk_educators_edu_institution1_idx ON dbo.educators USING btree (edu_providers_id);


--
-- Name: idx_16907_employers_employer_id_unique; Type: INDEX; Schema: dbo; Owner: -
--

CREATE UNIQUE INDEX idx_16907_employers_employer_id_unique ON dbo.employers USING btree (employer_id);


--
-- Name: idx_16907_employers_fk_employer_user1_idx; Type: INDEX; Schema: dbo; Owner: -
--

CREATE INDEX idx_16907_employers_fk_employer_user1_idx ON dbo.employers USING btree (user_id);


--
-- Name: idx_16907_employers_user_id_key; Type: INDEX; Schema: dbo; Owner: -
--

CREATE UNIQUE INDEX idx_16907_employers_user_id_key ON dbo.employers USING btree (user_id);


--
-- Name: idx_16907_fk_employers_company1_idx; Type: INDEX; Schema: dbo; Owner: -
--

CREATE INDEX idx_16907_fk_employers_company1_idx ON dbo.employers USING btree (company_id);


--
-- Name: idx_16925_events_on_users_eventid_userid_key; Type: INDEX; Schema: dbo; Owner: -
--

CREATE UNIQUE INDEX idx_16925_events_on_users_eventid_userid_key ON dbo.events_on_users USING btree (eventid, userid);


--
-- Name: idx_16947_fk_job_postings_companies1_idx; Type: INDEX; Schema: dbo; Owner: -
--

CREATE INDEX idx_16947_fk_job_postings_companies1_idx ON dbo.job_postings USING btree (company_id);


--
-- Name: idx_16947_fk_job_postings_company_addresses1_idx; Type: INDEX; Schema: dbo; Owner: -
--

CREATE INDEX idx_16947_fk_job_postings_company_addresses1_idx ON dbo.job_postings USING btree (location_id);


--
-- Name: idx_16947_fk_job_postings_employers1_idx; Type: INDEX; Schema: dbo; Owner: -
--

CREATE INDEX idx_16947_fk_job_postings_employers1_idx ON dbo.job_postings USING btree (employer_id);


--
-- Name: idx_16947_fk_job_postings_technology_areas1_idx; Type: INDEX; Schema: dbo; Owner: -
--

CREATE INDEX idx_16947_fk_job_postings_technology_areas1_idx ON dbo.job_postings USING btree (tech_area_id);


--
-- Name: idx_16947_job_postings_job_listing_id_unique; Type: INDEX; Schema: dbo; Owner: -
--

CREATE UNIQUE INDEX idx_16947_job_postings_job_listing_id_unique ON dbo.job_postings USING btree (job_posting_id);


--
-- Name: idx_16977_jobroleskill_jobroleid_skillid_key; Type: INDEX; Schema: dbo; Owner: -
--

CREATE UNIQUE INDEX idx_16977_jobroleskill_jobroleid_skillid_key ON dbo.jobroleskill USING btree (jobroleid, skillid);


--
-- Name: idx_16986_jobroletraining_jobroleid_trainingid_key; Type: INDEX; Schema: dbo; Owner: -
--

CREATE UNIQUE INDEX idx_16986_jobroletraining_jobroleid_trainingid_key ON dbo.jobroletraining USING btree (jobroleid, trainingid);


--
-- Name: idx_16994_jobseeker_has_skills_fk_jobseeker_has_skill_jobseeker; Type: INDEX; Schema: dbo; Owner: -
--

CREATE INDEX idx_16994_jobseeker_has_skills_fk_jobseeker_has_skill_jobseeker ON dbo.jobseeker_has_skills USING btree (jobseeker_id);


--
-- Name: idx_16994_jobseeker_has_skills_fk_jobseeker_has_skill_skill1_id; Type: INDEX; Schema: dbo; Owner: -
--

CREATE INDEX idx_16994_jobseeker_has_skills_fk_jobseeker_has_skill_skill1_id ON dbo.jobseeker_has_skills USING btree (skill_id);


--
-- Name: idx_17001_jobseekerjobposting_jobseekerid_jobpostid_key; Type: INDEX; Schema: dbo; Owner: -
--

CREATE UNIQUE INDEX idx_17001_jobseekerjobposting_jobseekerid_jobpostid_key ON dbo.jobseekerjobposting USING btree (jobseekerid, jobpostid);


--
-- Name: idx_17017_jobseekers_fk_jobseeker_pathways1_idx; Type: INDEX; Schema: dbo; Owner: -
--

CREATE INDEX idx_17017_jobseekers_fk_jobseeker_pathways1_idx ON dbo.jobseekers USING btree (targeted_pathway);


--
-- Name: idx_17017_jobseekers_fk_learner_user1_idx; Type: INDEX; Schema: dbo; Owner: -
--

CREATE INDEX idx_17017_jobseekers_fk_learner_user1_idx ON dbo.jobseekers USING btree (user_id);


--
-- Name: idx_17017_jobseekers_learner_id_unique; Type: INDEX; Schema: dbo; Owner: -
--

CREATE UNIQUE INDEX idx_17017_jobseekers_learner_id_unique ON dbo.jobseekers USING btree (jobseeker_id);


--
-- Name: idx_17017_jobseekers_user_id_key; Type: INDEX; Schema: dbo; Owner: -
--

CREATE UNIQUE INDEX idx_17017_jobseekers_user_id_key ON dbo.jobseekers USING btree (user_id);


--
-- Name: idx_17030_fk_jobseeker_education_edu_institution1_idx; Type: INDEX; Schema: dbo; Owner: -
--

CREATE INDEX idx_17030_fk_jobseeker_education_edu_institution1_idx ON dbo.jobseekers_education USING btree (edu_provider_id);


--
-- Name: idx_17030_fk_jobseeker_education_jobseeker1_idx; Type: INDEX; Schema: dbo; Owner: -
--

CREATE INDEX idx_17030_fk_jobseeker_education_jobseeker1_idx ON dbo.jobseekers_education USING btree (jobseeker_id);


--
-- Name: idx_17045_jobseekers_private_data_fk_user_learner_private_data_; Type: INDEX; Schema: dbo; Owner: -
--

CREATE INDEX idx_17045_jobseekers_private_data_fk_user_learner_private_data_ ON dbo.jobseekers_private_data USING btree (jobseeker_id);


--
-- Name: idx_17045_jobseekers_private_data_jobseeker_id_key; Type: INDEX; Schema: dbo; Owner: -
--

CREATE UNIQUE INDEX idx_17045_jobseekers_private_data_jobseeker_id_key ON dbo.jobseekers_private_data USING btree (jobseeker_id);


--
-- Name: idx_17045_jobseekers_private_data_learner_private_data_id_uniqu; Type: INDEX; Schema: dbo; Owner: -
--

CREATE UNIQUE INDEX idx_17045_jobseekers_private_data_learner_private_data_id_uniqu ON dbo.jobseekers_private_data USING btree (jobseeker_private_data_id);


--
-- Name: idx_17072_pathway_has_skills_fk_pathways_has_skill_pathways1_id; Type: INDEX; Schema: dbo; Owner: -
--

CREATE INDEX idx_17072_pathway_has_skills_fk_pathways_has_skill_pathways1_id ON dbo.pathway_has_skills USING btree (pathway_id);


--
-- Name: idx_17072_pathway_has_skills_fk_pathways_has_skill_skill1_idx; Type: INDEX; Schema: dbo; Owner: -
--

CREATE INDEX idx_17072_pathway_has_skills_fk_pathways_has_skill_skill1_idx ON dbo.pathway_has_skills USING btree (skill_id);


--
-- Name: idx_17079_fk_pathway_subcategories_pathways1_idx; Type: INDEX; Schema: dbo; Owner: -
--

CREATE INDEX idx_17079_fk_pathway_subcategories_pathways1_idx ON dbo.pathway_subcategories USING btree (pathway_id);


--
-- Name: idx_17086_pathways_pathway_title_key; Type: INDEX; Schema: dbo; Owner: -
--

CREATE UNIQUE INDEX idx_17086_pathways_pathway_title_key ON dbo.pathways USING btree (pathway_title);


--
-- Name: idx_17093_pathwaytraining_pathwayid_trainingid_key; Type: INDEX; Schema: dbo; Owner: -
--

CREATE UNIQUE INDEX idx_17093_pathwaytraining_pathwayid_trainingid_key ON dbo.pathwaytraining USING btree (pathwayid, trainingid);


--
-- Name: idx_17101_postal_code_lat_lng_idx; Type: INDEX; Schema: dbo; Owner: -
--

CREATE INDEX idx_17101_postal_code_lat_lng_idx ON dbo.postal_geo_data USING btree (lat, lng);


--
-- Name: idx_17106_programs_id_unique; Type: INDEX; Schema: dbo; Owner: -
--

CREATE UNIQUE INDEX idx_17106_programs_id_unique ON dbo.programs USING btree (id);


--
-- Name: idx_17106_programs_title_key; Type: INDEX; Schema: dbo; Owner: -
--

CREATE UNIQUE INDEX idx_17106_programs_title_key ON dbo.programs USING btree (title);


--
-- Name: idx_17113_fk_proj_based_tech_assessments_pathways1_idx; Type: INDEX; Schema: dbo; Owner: -
--

CREATE INDEX idx_17113_fk_proj_based_tech_assessments_pathways1_idx ON dbo.proj_based_tech_assessments USING btree (pathway_id);


--
-- Name: idx_17113_proj_based_tech_assessments_proj_based_tech_assessmen; Type: INDEX; Schema: dbo; Owner: -
--

CREATE UNIQUE INDEX idx_17113_proj_based_tech_assessments_proj_based_tech_assessmen ON dbo.proj_based_tech_assessments USING btree (proj_based_tech_assessment_id);


--
-- Name: idx_17118_project_experiences_fk_project_experience_jobseeker1_; Type: INDEX; Schema: dbo; Owner: -
--

CREATE INDEX idx_17118_project_experiences_fk_project_experience_jobseeker1_ ON dbo.project_experiences USING btree (jobseeker_id);


--
-- Name: idx_17126_project_has_skills_fk_project_experience_has_skill_pr; Type: INDEX; Schema: dbo; Owner: -
--

CREATE INDEX idx_17126_project_has_skills_fk_project_experience_has_skill_pr ON dbo.project_has_skills USING btree (proj_exp_id);


--
-- Name: idx_17126_project_has_skills_fk_project_experience_has_skill_sk; Type: INDEX; Schema: dbo; Owner: -
--

CREATE INDEX idx_17126_project_has_skills_fk_project_experience_has_skill_sk ON dbo.project_has_skills USING btree (skill_id);


--
-- Name: idx_17133_fk_training_program_has_skills_skills1_idx; Type: INDEX; Schema: dbo; Owner: -
--

CREATE INDEX idx_17133_fk_training_program_has_skills_skills1_idx ON dbo.provider_program_has_skills USING btree (skill_id);


--
-- Name: idx_17133_fk_training_program_has_skills_training_program1_idx; Type: INDEX; Schema: dbo; Owner: -
--

CREATE INDEX idx_17133_fk_training_program_has_skills_training_program1_idx ON dbo.provider_program_has_skills USING btree (training_program_id);


--
-- Name: idx_17140_training_programs_fk_training_program_pathways1_idx; Type: INDEX; Schema: dbo; Owner: -
--

CREATE INDEX idx_17140_training_programs_fk_training_program_pathways1_idx ON dbo.provider_programs USING btree (pathway_id);


--
-- Name: idx_17140_training_programs_fk_training_program_training_provid; Type: INDEX; Schema: dbo; Owner: -
--

CREATE INDEX idx_17140_training_programs_fk_training_program_training_provid ON dbo.provider_programs USING btree (edu_provider_id);


--
-- Name: idx_17140_training_programs_training_program_id_unique; Type: INDEX; Schema: dbo; Owner: -
--

CREATE UNIQUE INDEX idx_17140_training_programs_training_program_id_unique ON dbo.provider_programs USING btree (training_program_id);


--
-- Name: idx_17150_provider_testimonials_id_unique; Type: INDEX; Schema: dbo; Owner: -
--

CREATE UNIQUE INDEX idx_17150_provider_testimonials_id_unique ON dbo.providertestimonials USING btree (id);


--
-- Name: idx_17156_ragrecordmanager_fileid_key; Type: INDEX; Schema: dbo; Owner: -
--

CREATE UNIQUE INDEX idx_17156_ragrecordmanager_fileid_key ON dbo.ragrecordmanager USING btree (fileid);


--
-- Name: idx_17164_sa_possible_answers_fk_sa_possible_answer_sa_question; Type: INDEX; Schema: dbo; Owner: -
--

CREATE INDEX idx_17164_sa_possible_answers_fk_sa_possible_answer_sa_question ON dbo.sa_possible_answers USING btree (sa_question_id);


--
-- Name: idx_17164_sa_possible_answers_sa_possible_answer_id_unique; Type: INDEX; Schema: dbo; Owner: -
--

CREATE UNIQUE INDEX idx_17164_sa_possible_answers_sa_possible_answer_id_unique ON dbo.sa_possible_answers USING btree (sa_possible_answer_id);


--
-- Name: idx_17170_sa_questions_fk_sa_question_self_assessment1_idx; Type: INDEX; Schema: dbo; Owner: -
--

CREATE INDEX idx_17170_sa_questions_fk_sa_question_self_assessment1_idx ON dbo.sa_questions USING btree (self_assessment_id);


--
-- Name: idx_17170_sa_questions_sa_question_id_unique; Type: INDEX; Schema: dbo; Owner: -
--

CREATE UNIQUE INDEX idx_17170_sa_questions_sa_question_id_unique ON dbo.sa_questions USING btree (sa_question_id);


--
-- Name: idx_17175_fk_self_assessments_pathways1_idx; Type: INDEX; Schema: dbo; Owner: -
--

CREATE INDEX idx_17175_fk_self_assessments_pathways1_idx ON dbo.self_assessments USING btree (pathway_id);


--
-- Name: idx_17175_self_assessments_self_assessment_id_unique; Type: INDEX; Schema: dbo; Owner: -
--

CREATE UNIQUE INDEX idx_17175_self_assessments_self_assessment_id_unique ON dbo.self_assessments USING btree (self_assessment_id);


--
-- Name: idx_17180_session_sessiontoken_key; Type: INDEX; Schema: dbo; Owner: -
--

CREATE UNIQUE INDEX idx_17180_session_sessiontoken_key ON dbo.session USING btree (sessiontoken);


--
-- Name: idx_17180_session_userid_idx; Type: INDEX; Schema: dbo; Owner: -
--

CREATE INDEX idx_17180_session_userid_idx ON dbo.session USING btree (userid);


--
-- Name: idx_17186_skill_subcategories_skill_category_id_unique; Type: INDEX; Schema: dbo; Owner: -
--

CREATE UNIQUE INDEX idx_17186_skill_subcategories_skill_category_id_unique ON dbo.skill_subcategories USING btree (skill_subcategory_id);


--
-- Name: idx_17194_skills_fk_skill_skill_category_idx; Type: INDEX; Schema: dbo; Owner: -
--

CREATE INDEX idx_17194_skills_fk_skill_skill_category_idx ON dbo.skills USING btree (skill_subcategory_id);


--
-- Name: idx_17194_skills_skill_id_unique; Type: INDEX; Schema: dbo; Owner: -
--

CREATE UNIQUE INDEX idx_17194_skills_skill_id_unique ON dbo.skills USING btree (skill_id);


--
-- Name: idx_17265_users_email_key; Type: INDEX; Schema: dbo; Owner: -
--

CREATE UNIQUE INDEX idx_17265_users_email_key ON dbo.users USING btree (email);


--
-- Name: idx_17265_users_id_key; Type: INDEX; Schema: dbo; Owner: -
--

CREATE UNIQUE INDEX idx_17265_users_id_key ON dbo.users USING btree (id);


--
-- Name: idx_17276_verificationtoken_identifier_token_key; Type: INDEX; Schema: dbo; Owner: -
--

CREATE UNIQUE INDEX idx_17276_verificationtoken_identifier_token_key ON dbo.verificationtoken USING btree (identifier, token);


--
-- Name: idx_17281_volunteer_has_skills_fk_volunteer_has_skill_skill1_id; Type: INDEX; Schema: dbo; Owner: -
--

CREATE INDEX idx_17281_volunteer_has_skills_fk_volunteer_has_skill_skill1_id ON dbo.volunteer_has_skills USING btree (skill_id);


--
-- Name: idx_17281_volunteer_has_skills_fk_volunteer_has_skill_volunteer; Type: INDEX; Schema: dbo; Owner: -
--

CREATE INDEX idx_17281_volunteer_has_skills_fk_volunteer_has_skill_volunteer ON dbo.volunteer_has_skills USING btree (volunteer_id);


--
-- Name: idx_17288_volunteers_fk_mentor_user1_idx; Type: INDEX; Schema: dbo; Owner: -
--

CREATE INDEX idx_17288_volunteers_fk_mentor_user1_idx ON dbo.volunteers USING btree (user_id);


--
-- Name: idx_17288_volunteers_mentor_id_unique; Type: INDEX; Schema: dbo; Owner: -
--

CREATE UNIQUE INDEX idx_17288_volunteers_mentor_id_unique ON dbo.volunteers USING btree (volunteer_id);


--
-- Name: idx_17295_fk_work_experience_jobseeker1_idx; Type: INDEX; Schema: dbo; Owner: -
--

CREATE INDEX idx_17295_fk_work_experience_jobseeker1_idx ON dbo.work_experiences USING btree (sector_id);


--
-- Name: idx_17295_fk_work_experiences_technology_areas1_idx; Type: INDEX; Schema: dbo; Owner: -
--

CREATE INDEX idx_17295_fk_work_experiences_technology_areas1_idx ON dbo.work_experiences USING btree (tech_area_id);


--
-- Name: idx_17295_work_experiences_fk_work_experience_jobseeker1_idx; Type: INDEX; Schema: dbo; Owner: -
--

CREATE INDEX idx_17295_work_experiences_fk_work_experience_jobseeker1_idx ON dbo.work_experiences USING btree (jobseeker_id);


--
-- Name: _jobpostingskills _jobpostingskills_a_fkey; Type: FK CONSTRAINT; Schema: dbo; Owner: -
--

ALTER TABLE ONLY dbo._jobpostingskills
    ADD CONSTRAINT _jobpostingskills_a_fkey FOREIGN KEY (a) REFERENCES dbo.job_postings(job_posting_id) ON UPDATE CASCADE ON DELETE CASCADE;


--
-- Name: _otherprioritypopulations _otherprioritypopulations_a_fkey; Type: FK CONSTRAINT; Schema: dbo; Owner: -
--

ALTER TABLE ONLY dbo._otherprioritypopulations
    ADD CONSTRAINT _otherprioritypopulations_a_fkey FOREIGN KEY (a) REFERENCES dbo.otherprioritypopulations(id) ON UPDATE CASCADE ON DELETE CASCADE;


--
-- Name: _otherprioritypopulations _otherprioritypopulations_b_fkey; Type: FK CONSTRAINT; Schema: dbo; Owner: -
--

ALTER TABLE ONLY dbo._otherprioritypopulations
    ADD CONSTRAINT _otherprioritypopulations_b_fkey FOREIGN KEY (b) REFERENCES dbo.traineedetail(jobseekeredid) ON UPDATE CASCADE ON DELETE CASCADE;


--
-- Name: account account_user_id_fkey; Type: FK CONSTRAINT; Schema: dbo; Owner: -
--

ALTER TABLE ONLY dbo.account
    ADD CONSTRAINT account_user_id_fkey FOREIGN KEY (user_id) REFERENCES dbo.users(id) ON UPDATE CASCADE ON DELETE CASCADE;


--
-- Name: authenticator authenticator_userid_fkey; Type: FK CONSTRAINT; Schema: dbo; Owner: -
--

ALTER TABLE ONLY dbo.authenticator
    ADD CONSTRAINT authenticator_userid_fkey FOREIGN KEY (userid) REFERENCES dbo.users(id) ON UPDATE CASCADE ON DELETE CASCADE;


--
-- Name: casemgmt casemgmt_jobseekerid_fkey; Type: FK CONSTRAINT; Schema: dbo; Owner: -
--

ALTER TABLE ONLY dbo.casemgmt
    ADD CONSTRAINT casemgmt_jobseekerid_fkey FOREIGN KEY (jobseekerid) REFERENCES dbo.careerprepassessment(jobseekerid) ON UPDATE CASCADE ON DELETE CASCADE;


--
-- Name: cip_to_socc_map cip_to_socc_map_cip_code_fkey; Type: FK CONSTRAINT; Schema: dbo; Owner: -
--

ALTER TABLE ONLY dbo.cip_to_socc_map
    ADD CONSTRAINT cip_to_socc_map_cip_code_fkey FOREIGN KEY (cip_code) REFERENCES dbo.cip(code) ON UPDATE CASCADE;


--
-- Name: cip_to_socc_map cip_to_socc_map_socc_id_fkey; Type: FK CONSTRAINT; Schema: dbo; Owner: -
--

ALTER TABLE ONLY dbo.cip_to_socc_map
    ADD CONSTRAINT cip_to_socc_map_socc_id_fkey FOREIGN KEY (socc_id) REFERENCES dbo.socc(id) ON UPDATE CASCADE;


--
-- Name: companies companies_createdby_fkey; Type: FK CONSTRAINT; Schema: dbo; Owner: -
--

ALTER TABLE ONLY dbo.companies
    ADD CONSTRAINT companies_createdby_fkey FOREIGN KEY (createdby) REFERENCES dbo.users(id) ON UPDATE CASCADE;


--
-- Name: edu_providers edu_providers_userid_fkey; Type: FK CONSTRAINT; Schema: dbo; Owner: -
--

ALTER TABLE ONLY dbo.edu_providers
    ADD CONSTRAINT edu_providers_userid_fkey FOREIGN KEY (userid) REFERENCES dbo.users(id) ON UPDATE CASCADE ON DELETE SET NULL;


--
-- Name: employerjobrolefeedback employerjobrolefeedback_jobroleid_fkey; Type: FK CONSTRAINT; Schema: dbo; Owner: -
--

ALTER TABLE ONLY dbo.employerjobrolefeedback
    ADD CONSTRAINT employerjobrolefeedback_jobroleid_fkey FOREIGN KEY (jobroleid) REFERENCES dbo.jobrole(id) ON UPDATE CASCADE;


--
-- Name: employerjobrolefeedback employerjobrolefeedback_skillid_fkey; Type: FK CONSTRAINT; Schema: dbo; Owner: -
--

ALTER TABLE ONLY dbo.employerjobrolefeedback
    ADD CONSTRAINT employerjobrolefeedback_skillid_fkey FOREIGN KEY (skillid) REFERENCES dbo.skills(skill_id) ON UPDATE CASCADE;


--
-- Name: employerjobrolefeedback employerjobrolefeedback_submiterid_fkey; Type: FK CONSTRAINT; Schema: dbo; Owner: -
--

ALTER TABLE ONLY dbo.employerjobrolefeedback
    ADD CONSTRAINT employerjobrolefeedback_submiterid_fkey FOREIGN KEY (submiterid) REFERENCES dbo.users(id) ON UPDATE CASCADE;


--
-- Name: events events_createdbyid_fkey; Type: FK CONSTRAINT; Schema: dbo; Owner: -
--

ALTER TABLE ONLY dbo.events
    ADD CONSTRAINT events_createdbyid_fkey FOREIGN KEY (createdbyid) REFERENCES dbo.users(id) ON UPDATE CASCADE ON DELETE SET NULL;


--
-- Name: events_on_users events_on_users_eventid_fkey; Type: FK CONSTRAINT; Schema: dbo; Owner: -
--

ALTER TABLE ONLY dbo.events_on_users
    ADD CONSTRAINT events_on_users_eventid_fkey FOREIGN KEY (eventid) REFERENCES dbo.events(id);


--
-- Name: events_on_users events_on_users_userid_fkey; Type: FK CONSTRAINT; Schema: dbo; Owner: -
--

ALTER TABLE ONLY dbo.events_on_users
    ADD CONSTRAINT events_on_users_userid_fkey FOREIGN KEY (userid) REFERENCES dbo.users(id) ON UPDATE CASCADE ON DELETE CASCADE;


--
-- Name: cfa_admin fk_admin_contacts1; Type: FK CONSTRAINT; Schema: dbo; Owner: -
--

ALTER TABLE ONLY dbo.cfa_admin
    ADD CONSTRAINT fk_admin_contacts1 FOREIGN KEY (user_id) REFERENCES dbo.users(id);


--
-- Name: brandingrating fk_branding_rating_career_prep_assessment1; Type: FK CONSTRAINT; Schema: dbo; Owner: -
--

ALTER TABLE ONLY dbo.brandingrating
    ADD CONSTRAINT fk_branding_rating_career_prep_assessment1 FOREIGN KEY (jobseekerid) REFERENCES dbo.careerprepassessment(jobseekerid) ON UPDATE CASCADE ON DELETE CASCADE;


--
-- Name: careerprepassessment fk_career_prep_app_jobseeker1; Type: FK CONSTRAINT; Schema: dbo; Owner: -
--

ALTER TABLE ONLY dbo.careerprepassessment
    ADD CONSTRAINT fk_career_prep_app_jobseeker1 FOREIGN KEY (jobseekerid) REFERENCES dbo.jobseekers(jobseeker_id) ON DELETE CASCADE;


--
-- Name: casemgmtnotes fk_case_mgmt_notes_case_mgmt1; Type: FK CONSTRAINT; Schema: dbo; Owner: -
--

ALTER TABLE ONLY dbo.casemgmtnotes
    ADD CONSTRAINT fk_case_mgmt_notes_case_mgmt1 FOREIGN KEY (jobseekerid) REFERENCES dbo.careerprepassessment(jobseekerid) ON DELETE CASCADE;


--
-- Name: casemgmtnotes fk_case_mgmt_notes_user1; Type: FK CONSTRAINT; Schema: dbo; Owner: -
--

ALTER TABLE ONLY dbo.casemgmtnotes
    ADD CONSTRAINT fk_case_mgmt_notes_user1 FOREIGN KEY (createdby) REFERENCES dbo.users(id);


--
-- Name: casemgmt fk_case_mgmt_user1; Type: FK CONSTRAINT; Schema: dbo; Owner: -
--

ALTER TABLE ONLY dbo.casemgmt
    ADD CONSTRAINT fk_case_mgmt_user1 FOREIGN KEY (managerid) REFERENCES dbo.users(id) ON DELETE SET NULL;


--
-- Name: certificates fk_certificates_jobseeker1; Type: FK CONSTRAINT; Schema: dbo; Owner: -
--

ALTER TABLE ONLY dbo.certificates
    ADD CONSTRAINT fk_certificates_jobseeker1 FOREIGN KEY (jobseeker_id) REFERENCES dbo.jobseekers(jobseeker_id) ON DELETE CASCADE;


--
-- Name: bookmarked_jobseekers fk_companies1; Type: FK CONSTRAINT; Schema: dbo; Owner: -
--

ALTER TABLE ONLY dbo.bookmarked_jobseekers
    ADD CONSTRAINT fk_companies1 FOREIGN KEY (company_id) REFERENCES dbo.companies(company_id);


--
-- Name: company_addresses fk_company_address_company1; Type: FK CONSTRAINT; Schema: dbo; Owner: -
--

ALTER TABLE ONLY dbo.company_addresses
    ADD CONSTRAINT fk_company_address_company1 FOREIGN KEY (company_id) REFERENCES dbo.companies(company_id);


--
-- Name: company_addresses fk_company_address_postgeodata1; Type: FK CONSTRAINT; Schema: dbo; Owner: -
--

ALTER TABLE ONLY dbo.company_addresses
    ADD CONSTRAINT fk_company_address_postgeodata1 FOREIGN KEY (zip_region) REFERENCES dbo.postal_geo_data(zip);


--
-- Name: companies fk_company_industry_sectors1; Type: FK CONSTRAINT; Schema: dbo; Owner: -
--

ALTER TABLE ONLY dbo.companies
    ADD CONSTRAINT fk_company_industry_sectors1 FOREIGN KEY (industry_sector_id) REFERENCES dbo.industry_sectors(industry_sector_id) ON DELETE SET NULL;


--
-- Name: company_testimonials fk_company_testimonals_employer1; Type: FK CONSTRAINT; Schema: dbo; Owner: -
--

ALTER TABLE ONLY dbo.company_testimonials
    ADD CONSTRAINT fk_company_testimonals_employer1 FOREIGN KEY (employer_id) REFERENCES dbo.employers(employer_id) ON UPDATE CASCADE ON DELETE SET NULL;


--
-- Name: company_testimonials fk_company_testimonials_company1; Type: FK CONSTRAINT; Schema: dbo; Owner: -
--

ALTER TABLE ONLY dbo.company_testimonials
    ADD CONSTRAINT fk_company_testimonials_company1 FOREIGN KEY (company_id) REFERENCES dbo.companies(company_id);


--
-- Name: cybersecurityrating fk_cybersecurity_rating_career_prep_assessment1; Type: FK CONSTRAINT; Schema: dbo; Owner: -
--

ALTER TABLE ONLY dbo.cybersecurityrating
    ADD CONSTRAINT fk_cybersecurity_rating_career_prep_assessment1 FOREIGN KEY (jobseekerid) REFERENCES dbo.careerprepassessment(jobseekerid) ON UPDATE CASCADE ON DELETE CASCADE;


--
-- Name: dataanalyticsrating fk_data_analytics_rating_career_prep_assessment1; Type: FK CONSTRAINT; Schema: dbo; Owner: -
--

ALTER TABLE ONLY dbo.dataanalyticsrating
    ADD CONSTRAINT fk_data_analytics_rating_career_prep_assessment1 FOREIGN KEY (jobseekerid) REFERENCES dbo.careerprepassessment(jobseekerid) ON UPDATE CASCADE ON DELETE CASCADE;


--
-- Name: durableskillsrating fk_durable_skills_rating_career_prep_assessment1; Type: FK CONSTRAINT; Schema: dbo; Owner: -
--

ALTER TABLE ONLY dbo.durableskillsrating
    ADD CONSTRAINT fk_durable_skills_rating_career_prep_assessment1 FOREIGN KEY (jobseekerid) REFERENCES dbo.careerprepassessment(jobseekerid) ON UPDATE CASCADE ON DELETE CASCADE;


--
-- Name: edu_addresses fk_edu_address_edu_institution1; Type: FK CONSTRAINT; Schema: dbo; Owner: -
--

ALTER TABLE ONLY dbo.edu_addresses
    ADD CONSTRAINT fk_edu_address_edu_institution1 FOREIGN KEY (edu_provider_id) REFERENCES dbo.edu_providers(id);


--
-- Name: edu_addresses fk_edu_address_postgeodata1; Type: FK CONSTRAINT; Schema: dbo; Owner: -
--

ALTER TABLE ONLY dbo.edu_addresses
    ADD CONSTRAINT fk_edu_address_postgeodata1 FOREIGN KEY (zip) REFERENCES dbo.postal_geo_data(zip);


--
-- Name: educators fk_educators_contacts1; Type: FK CONSTRAINT; Schema: dbo; Owner: -
--

ALTER TABLE ONLY dbo.educators
    ADD CONSTRAINT fk_educators_contacts1 FOREIGN KEY (user_id) REFERENCES dbo.users(id);


--
-- Name: educators fk_educators_edu_institution1; Type: FK CONSTRAINT; Schema: dbo; Owner: -
--

ALTER TABLE ONLY dbo.educators
    ADD CONSTRAINT fk_educators_edu_institution1 FOREIGN KEY (edu_providers_id) REFERENCES dbo.edu_providers(id);


--
-- Name: employers fk_employer_user1; Type: FK CONSTRAINT; Schema: dbo; Owner: -
--

ALTER TABLE ONLY dbo.employers
    ADD CONSTRAINT fk_employer_user1 FOREIGN KEY (user_id) REFERENCES dbo.users(id);


--
-- Name: bookmarked_jobseekers fk_employers1; Type: FK CONSTRAINT; Schema: dbo; Owner: -
--

ALTER TABLE ONLY dbo.bookmarked_jobseekers
    ADD CONSTRAINT fk_employers1 FOREIGN KEY (employer_id) REFERENCES dbo.employers(employer_id) ON DELETE SET NULL;


--
-- Name: employers fk_employers_company1; Type: FK CONSTRAINT; Schema: dbo; Owner: -
--

ALTER TABLE ONLY dbo.employers
    ADD CONSTRAINT fk_employers_company1 FOREIGN KEY (company_id) REFERENCES dbo.companies(company_id) ON DELETE SET NULL;


--
-- Name: employers fk_employers_company_addresses; Type: FK CONSTRAINT; Schema: dbo; Owner: -
--

ALTER TABLE ONLY dbo.employers
    ADD CONSTRAINT fk_employers_company_addresses FOREIGN KEY (work_address_id) REFERENCES dbo.company_addresses(company_address_id) ON DELETE SET NULL;


--
-- Name: itcloudrating fk_it_cloud_rating_career_prep_assessment1; Type: FK CONSTRAINT; Schema: dbo; Owner: -
--

ALTER TABLE ONLY dbo.itcloudrating
    ADD CONSTRAINT fk_it_cloud_rating_career_prep_assessment1 FOREIGN KEY (jobseekerid) REFERENCES dbo.careerprepassessment(jobseekerid) ON UPDATE CASCADE ON DELETE CASCADE;


--
-- Name: jobplacement fk_job_placement_companies1; Type: FK CONSTRAINT; Schema: dbo; Owner: -
--

ALTER TABLE ONLY dbo.jobplacement
    ADD CONSTRAINT fk_job_placement_companies1 FOREIGN KEY (companyid) REFERENCES dbo.companies(company_id) ON DELETE SET NULL;


--
-- Name: jobplacement fk_job_placement_jobseeker1; Type: FK CONSTRAINT; Schema: dbo; Owner: -
--

ALTER TABLE ONLY dbo.jobplacement
    ADD CONSTRAINT fk_job_placement_jobseeker1 FOREIGN KEY (job_placement_id) REFERENCES dbo.jobseekers(jobseeker_id);


--
-- Name: job_postings fk_job_postings_companies1; Type: FK CONSTRAINT; Schema: dbo; Owner: -
--

ALTER TABLE ONLY dbo.job_postings
    ADD CONSTRAINT fk_job_postings_companies1 FOREIGN KEY (company_id) REFERENCES dbo.companies(company_id);


--
-- Name: job_postings fk_job_postings_company_addresses1; Type: FK CONSTRAINT; Schema: dbo; Owner: -
--

ALTER TABLE ONLY dbo.job_postings
    ADD CONSTRAINT fk_job_postings_company_addresses1 FOREIGN KEY (location_id) REFERENCES dbo.company_addresses(company_address_id);


--
-- Name: job_postings fk_job_postings_employers1; Type: FK CONSTRAINT; Schema: dbo; Owner: -
--

ALTER TABLE ONLY dbo.job_postings
    ADD CONSTRAINT fk_job_postings_employers1 FOREIGN KEY (employer_id) REFERENCES dbo.employers(employer_id) ON DELETE SET NULL;


--
-- Name: job_postings fk_job_postings_industry_sectors1; Type: FK CONSTRAINT; Schema: dbo; Owner: -
--

ALTER TABLE ONLY dbo.job_postings
    ADD CONSTRAINT fk_job_postings_industry_sectors1 FOREIGN KEY (sector_id) REFERENCES dbo.industry_sectors(industry_sector_id);


--
-- Name: job_postings fk_job_postings_technology_areas1; Type: FK CONSTRAINT; Schema: dbo; Owner: -
--

ALTER TABLE ONLY dbo.job_postings
    ADD CONSTRAINT fk_job_postings_technology_areas1 FOREIGN KEY (tech_area_id) REFERENCES dbo.technology_areas(id) ON DELETE SET NULL;


--
-- Name: jobseekers_education fk_jobseeker_education_edu_institution1; Type: FK CONSTRAINT; Schema: dbo; Owner: -
--

ALTER TABLE ONLY dbo.jobseekers_education
    ADD CONSTRAINT fk_jobseeker_education_edu_institution1 FOREIGN KEY (edu_provider_id) REFERENCES dbo.edu_providers(id) ON UPDATE CASCADE;


--
-- Name: jobseekers_education fk_jobseeker_education_jobseeker1; Type: FK CONSTRAINT; Schema: dbo; Owner: -
--

ALTER TABLE ONLY dbo.jobseekers_education
    ADD CONSTRAINT fk_jobseeker_education_jobseeker1 FOREIGN KEY (jobseeker_id) REFERENCES dbo.jobseekers(jobseeker_id) ON DELETE CASCADE;


--
-- Name: jobseekers_education fk_jobseeker_education_programs1; Type: FK CONSTRAINT; Schema: dbo; Owner: -
--

ALTER TABLE ONLY dbo.jobseekers_education
    ADD CONSTRAINT fk_jobseeker_education_programs1 FOREIGN KEY (program_id) REFERENCES dbo.programs(id) ON DELETE SET NULL;


--
-- Name: jobseeker_has_skills fk_jobseeker_has_skill_jobseeker1; Type: FK CONSTRAINT; Schema: dbo; Owner: -
--

ALTER TABLE ONLY dbo.jobseeker_has_skills
    ADD CONSTRAINT fk_jobseeker_has_skill_jobseeker1 FOREIGN KEY (jobseeker_id) REFERENCES dbo.jobseekers(jobseeker_id) ON DELETE CASCADE;


--
-- Name: jobseekers fk_jobseeker_pathways1; Type: FK CONSTRAINT; Schema: dbo; Owner: -
--

ALTER TABLE ONLY dbo.jobseekers
    ADD CONSTRAINT fk_jobseeker_pathways1 FOREIGN KEY (targeted_pathway) REFERENCES dbo.pathways(pathway_id) ON DELETE SET NULL;


--
-- Name: bookmarked_jobseekers fk_jobseekers1; Type: FK CONSTRAINT; Schema: dbo; Owner: -
--

ALTER TABLE ONLY dbo.bookmarked_jobseekers
    ADD CONSTRAINT fk_jobseekers1 FOREIGN KEY (jobseeker_id) REFERENCES dbo.jobseekers(jobseeker_id);


--
-- Name: jobseekers fk_learner_user1; Type: FK CONSTRAINT; Schema: dbo; Owner: -
--

ALTER TABLE ONLY dbo.jobseekers
    ADD CONSTRAINT fk_learner_user1 FOREIGN KEY (user_id) REFERENCES dbo.users(id);


--
-- Name: meeting fk_meeting_case_mgmt1; Type: FK CONSTRAINT; Schema: dbo; Owner: -
--

ALTER TABLE ONLY dbo.meeting
    ADD CONSTRAINT fk_meeting_case_mgmt1 FOREIGN KEY (jobseekerid) REFERENCES dbo.casemgmt(jobseekerid) ON DELETE CASCADE;


--
-- Name: volunteers fk_mentor_user1; Type: FK CONSTRAINT; Schema: dbo; Owner: -
--

ALTER TABLE ONLY dbo.volunteers
    ADD CONSTRAINT fk_mentor_user1 FOREIGN KEY (user_id) REFERENCES dbo.users(id);


--
-- Name: pathway_subcategories fk_pathway_subcategories_pathways1; Type: FK CONSTRAINT; Schema: dbo; Owner: -
--

ALTER TABLE ONLY dbo.pathway_subcategories
    ADD CONSTRAINT fk_pathway_subcategories_pathways1 FOREIGN KEY (pathway_id) REFERENCES dbo.pathways(pathway_id);


--
-- Name: pathway_has_skills fk_pathways_has_skill_pathways1; Type: FK CONSTRAINT; Schema: dbo; Owner: -
--

ALTER TABLE ONLY dbo.pathway_has_skills
    ADD CONSTRAINT fk_pathways_has_skill_pathways1 FOREIGN KEY (pathway_id) REFERENCES dbo.pathways(pathway_id);


--
-- Name: pathway_has_skills fk_pathways_has_skill_skill1; Type: FK CONSTRAINT; Schema: dbo; Owner: -
--

ALTER TABLE ONLY dbo.pathway_has_skills
    ADD CONSTRAINT fk_pathways_has_skill_skill1 FOREIGN KEY (skill_id) REFERENCES dbo.skills(skill_id);


--
-- Name: proj_based_tech_assessments fk_proj_based_tech_assessments_pathways1; Type: FK CONSTRAINT; Schema: dbo; Owner: -
--

ALTER TABLE ONLY dbo.proj_based_tech_assessments
    ADD CONSTRAINT fk_proj_based_tech_assessments_pathways1 FOREIGN KEY (pathway_id) REFERENCES dbo.pathways(pathway_id);


--
-- Name: project_has_skills fk_project_experience_has_skill_project_experience1; Type: FK CONSTRAINT; Schema: dbo; Owner: -
--

ALTER TABLE ONLY dbo.project_has_skills
    ADD CONSTRAINT fk_project_experience_has_skill_project_experience1 FOREIGN KEY (proj_exp_id) REFERENCES dbo.project_experiences(proj_exp_id) ON DELETE CASCADE;


--
-- Name: project_experiences fk_project_experience_jobseeker1; Type: FK CONSTRAINT; Schema: dbo; Owner: -
--

ALTER TABLE ONLY dbo.project_experiences
    ADD CONSTRAINT fk_project_experience_jobseeker1 FOREIGN KEY (jobseeker_id) REFERENCES dbo.jobseekers(jobseeker_id) ON DELETE CASCADE;


--
-- Name: provider_programs fk_provider_programs_programs1; Type: FK CONSTRAINT; Schema: dbo; Owner: -
--

ALTER TABLE ONLY dbo.provider_programs
    ADD CONSTRAINT fk_provider_programs_programs1 FOREIGN KEY (program_id) REFERENCES dbo.programs(id);


--
-- Name: sa_possible_answers fk_sa_possilbe_answer_sa_question1; Type: FK CONSTRAINT; Schema: dbo; Owner: -
--

ALTER TABLE ONLY dbo.sa_possible_answers
    ADD CONSTRAINT fk_sa_possilbe_answer_sa_question1 FOREIGN KEY (sa_question_id) REFERENCES dbo.sa_questions(sa_question_id);


--
-- Name: sa_questions fk_sa_question_self_assessment; Type: FK CONSTRAINT; Schema: dbo; Owner: -
--

ALTER TABLE ONLY dbo.sa_questions
    ADD CONSTRAINT fk_sa_question_self_assessment FOREIGN KEY (self_assessment_id) REFERENCES dbo.self_assessments(self_assessment_id);


--
-- Name: self_assessments fk_self_assessments_pathways1; Type: FK CONSTRAINT; Schema: dbo; Owner: -
--

ALTER TABLE ONLY dbo.self_assessments
    ADD CONSTRAINT fk_self_assessments_pathways1 FOREIGN KEY (pathway_id) REFERENCES dbo.pathways(pathway_id);


--
-- Name: skills fk_skill_skill_category; Type: FK CONSTRAINT; Schema: dbo; Owner: -
--

ALTER TABLE ONLY dbo.skills
    ADD CONSTRAINT fk_skill_skill_category FOREIGN KEY (skill_subcategory_id) REFERENCES dbo.skill_subcategories(skill_subcategory_id);


--
-- Name: company_social_links fk_social_media_company_company1; Type: FK CONSTRAINT; Schema: dbo; Owner: -
--

ALTER TABLE ONLY dbo.company_social_links
    ADD CONSTRAINT fk_social_media_company_company1 FOREIGN KEY (company_id) REFERENCES dbo.companies(company_id);


--
-- Name: company_social_links fk_social_media_company_social_media_platform1; Type: FK CONSTRAINT; Schema: dbo; Owner: -
--

ALTER TABLE ONLY dbo.company_social_links
    ADD CONSTRAINT fk_social_media_company_social_media_platform1 FOREIGN KEY (social_platform_id) REFERENCES dbo.social_media_platforms(social_platform_id);


--
-- Name: company_social_links fk_social_media_employer_employer1; Type: FK CONSTRAINT; Schema: dbo; Owner: -
--

ALTER TABLE ONLY dbo.company_social_links
    ADD CONSTRAINT fk_social_media_employer_employer1 FOREIGN KEY (employer_id) REFERENCES dbo.employers(employer_id) ON DELETE SET NULL;


--
-- Name: softwaredevrating fk_software_dev_rating_career_prep_assessment1; Type: FK CONSTRAINT; Schema: dbo; Owner: -
--

ALTER TABLE ONLY dbo.softwaredevrating
    ADD CONSTRAINT fk_software_dev_rating_career_prep_assessment1 FOREIGN KEY (jobseekerid) REFERENCES dbo.careerprepassessment(jobseekerid) ON UPDATE CASCADE ON DELETE CASCADE;


--
-- Name: traineedetail fk_traineedetail_jobseekers_education1; Type: FK CONSTRAINT; Schema: dbo; Owner: -
--

ALTER TABLE ONLY dbo.traineedetail
    ADD CONSTRAINT fk_traineedetail_jobseekers_education1 FOREIGN KEY (jobseekeredid) REFERENCES dbo.jobseekers_education(jobseeker_ed_id) ON DELETE CASCADE;


--
-- Name: provider_program_has_skills fk_training_program_has_skills_skills1; Type: FK CONSTRAINT; Schema: dbo; Owner: -
--

ALTER TABLE ONLY dbo.provider_program_has_skills
    ADD CONSTRAINT fk_training_program_has_skills_skills1 FOREIGN KEY (skill_id) REFERENCES dbo.skills(skill_id);


--
-- Name: provider_program_has_skills fk_training_program_has_skills_training_program1; Type: FK CONSTRAINT; Schema: dbo; Owner: -
--

ALTER TABLE ONLY dbo.provider_program_has_skills
    ADD CONSTRAINT fk_training_program_has_skills_training_program1 FOREIGN KEY (training_program_id) REFERENCES dbo.provider_programs(training_program_id) ON DELETE CASCADE;


--
-- Name: provider_programs fk_training_program_training_provider1; Type: FK CONSTRAINT; Schema: dbo; Owner: -
--

ALTER TABLE ONLY dbo.provider_programs
    ADD CONSTRAINT fk_training_program_training_provider1 FOREIGN KEY (edu_provider_id) REFERENCES dbo.edu_providers(id) ON DELETE CASCADE;


--
-- Name: users fk_user_address_postgeodata1; Type: FK CONSTRAINT; Schema: dbo; Owner: -
--

ALTER TABLE ONLY dbo.users
    ADD CONSTRAINT fk_user_address_postgeodata1 FOREIGN KEY (zip) REFERENCES dbo.postal_geo_data(zip) ON DELETE SET NULL;


--
-- Name: jobseekers_private_data fk_user_learner_private_data_user1; Type: FK CONSTRAINT; Schema: dbo; Owner: -
--

ALTER TABLE ONLY dbo.jobseekers_private_data
    ADD CONSTRAINT fk_user_learner_private_data_user1 FOREIGN KEY (jobseeker_id) REFERENCES dbo.jobseekers(jobseeker_id) ON DELETE CASCADE;


--
-- Name: volunteer_has_skills fk_volunteer_has_skill_skill1; Type: FK CONSTRAINT; Schema: dbo; Owner: -
--

ALTER TABLE ONLY dbo.volunteer_has_skills
    ADD CONSTRAINT fk_volunteer_has_skill_skill1 FOREIGN KEY (skill_id) REFERENCES dbo.skills(skill_id);


--
-- Name: volunteer_has_skills fk_volunteer_has_skill_volunteer1; Type: FK CONSTRAINT; Schema: dbo; Owner: -
--

ALTER TABLE ONLY dbo.volunteer_has_skills
    ADD CONSTRAINT fk_volunteer_has_skill_volunteer1 FOREIGN KEY (volunteer_id) REFERENCES dbo.volunteers(volunteer_id);


--
-- Name: work_experiences fk_work_eperiences_industry_sectors1; Type: FK CONSTRAINT; Schema: dbo; Owner: -
--

ALTER TABLE ONLY dbo.work_experiences
    ADD CONSTRAINT fk_work_eperiences_industry_sectors1 FOREIGN KEY (sector_id) REFERENCES dbo.industry_sectors(industry_sector_id) ON DELETE SET NULL;


--
-- Name: work_experiences fk_work_experience_jobseeker1; Type: FK CONSTRAINT; Schema: dbo; Owner: -
--

ALTER TABLE ONLY dbo.work_experiences
    ADD CONSTRAINT fk_work_experience_jobseeker1 FOREIGN KEY (jobseeker_id) REFERENCES dbo.jobseekers(jobseeker_id) ON DELETE CASCADE;


--
-- Name: work_experiences fk_work_experiences_technology_areas1; Type: FK CONSTRAINT; Schema: dbo; Owner: -
--

ALTER TABLE ONLY dbo.work_experiences
    ADD CONSTRAINT fk_work_experiences_technology_areas1 FOREIGN KEY (tech_area_id) REFERENCES dbo.technology_areas(id) ON DELETE SET NULL;


--
-- Name: jobrole jobrole_pathwayid_fkey; Type: FK CONSTRAINT; Schema: dbo; Owner: -
--

ALTER TABLE ONLY dbo.jobrole
    ADD CONSTRAINT jobrole_pathwayid_fkey FOREIGN KEY (pathwayid) REFERENCES dbo.pathways(pathway_id) ON UPDATE CASCADE ON DELETE SET NULL;


--
-- Name: jobroleskill jobroleskill_jobroleid_fkey; Type: FK CONSTRAINT; Schema: dbo; Owner: -
--

ALTER TABLE ONLY dbo.jobroleskill
    ADD CONSTRAINT jobroleskill_jobroleid_fkey FOREIGN KEY (jobroleid) REFERENCES dbo.jobrole(id) ON UPDATE CASCADE;


--
-- Name: jobroletraining jobroletraining_jobroleid_fkey; Type: FK CONSTRAINT; Schema: dbo; Owner: -
--

ALTER TABLE ONLY dbo.jobroletraining
    ADD CONSTRAINT jobroletraining_jobroleid_fkey FOREIGN KEY (jobroleid) REFERENCES dbo.jobrole(id) ON UPDATE CASCADE;


--
-- Name: jobroletraining jobroletraining_trainingid_fkey; Type: FK CONSTRAINT; Schema: dbo; Owner: -
--

ALTER TABLE ONLY dbo.jobroletraining
    ADD CONSTRAINT jobroletraining_trainingid_fkey FOREIGN KEY (trainingid) REFERENCES dbo.training(id) ON UPDATE CASCADE;


--
-- Name: jobseekerjobposting jobseekerjobposting_jobpostid_fkey; Type: FK CONSTRAINT; Schema: dbo; Owner: -
--

ALTER TABLE ONLY dbo.jobseekerjobposting
    ADD CONSTRAINT jobseekerjobposting_jobpostid_fkey FOREIGN KEY (jobpostid) REFERENCES dbo.job_postings(job_posting_id) ON UPDATE CASCADE;


--
-- Name: jobseekerjobposting jobseekerjobposting_jobseekerid_fkey; Type: FK CONSTRAINT; Schema: dbo; Owner: -
--

ALTER TABLE ONLY dbo.jobseekerjobposting
    ADD CONSTRAINT jobseekerjobposting_jobseekerid_fkey FOREIGN KEY (jobseekerid) REFERENCES dbo.jobseekers(jobseeker_id) ON UPDATE CASCADE;


--
-- Name: jobseekerjobpostingskillmatch jobseekerjobpostingskillmatch_jobseekerjobpostingid_fkey; Type: FK CONSTRAINT; Schema: dbo; Owner: -
--

ALTER TABLE ONLY dbo.jobseekerjobpostingskillmatch
    ADD CONSTRAINT jobseekerjobpostingskillmatch_jobseekerjobpostingid_fkey FOREIGN KEY (jobseekerjobpostingid) REFERENCES dbo.jobseekerjobposting(id) ON UPDATE CASCADE;


--
-- Name: pathwaytraining pathwaytraining_pathwayid_fkey; Type: FK CONSTRAINT; Schema: dbo; Owner: -
--

ALTER TABLE ONLY dbo.pathwaytraining
    ADD CONSTRAINT pathwaytraining_pathwayid_fkey FOREIGN KEY (pathwayid) REFERENCES dbo.pathways(pathway_id) ON UPDATE CASCADE ON DELETE SET NULL;


--
-- Name: pathwaytraining pathwaytraining_trainingid_fkey; Type: FK CONSTRAINT; Schema: dbo; Owner: -
--

ALTER TABLE ONLY dbo.pathwaytraining
    ADD CONSTRAINT pathwaytraining_trainingid_fkey FOREIGN KEY (trainingid) REFERENCES dbo.training(id) ON UPDATE CASCADE;


--
-- Name: provider_programs provider_programs_cipcode_fkey; Type: FK CONSTRAINT; Schema: dbo; Owner: -
--

ALTER TABLE ONLY dbo.provider_programs
    ADD CONSTRAINT provider_programs_cipcode_fkey FOREIGN KEY (cipcode) REFERENCES dbo.cip(code) ON UPDATE CASCADE ON DELETE SET NULL;


--
-- Name: providertestimonials providertestimonials_eduproviderid_fkey; Type: FK CONSTRAINT; Schema: dbo; Owner: -
--

ALTER TABLE ONLY dbo.providertestimonials
    ADD CONSTRAINT providertestimonials_eduproviderid_fkey FOREIGN KEY (eduproviderid) REFERENCES dbo.edu_providers(id) ON UPDATE CASCADE;


--
-- Name: session session_userid_fkey; Type: FK CONSTRAINT; Schema: dbo; Owner: -
--

ALTER TABLE ONLY dbo.session
    ADD CONSTRAINT session_userid_fkey FOREIGN KEY (userid) REFERENCES dbo.users(id) ON UPDATE CASCADE ON DELETE CASCADE;


--
-- Name: socc2018_to_cip2020_map socc2018_to_cip2020_map_cip_code_fkey; Type: FK CONSTRAINT; Schema: dbo; Owner: -
--

ALTER TABLE ONLY dbo.socc2018_to_cip2020_map
    ADD CONSTRAINT socc2018_to_cip2020_map_cip_code_fkey FOREIGN KEY (cip_code) REFERENCES dbo.cip(code) ON UPDATE CASCADE;


--
-- Name: socc2018_to_cip2020_map socc2018_to_cip2020_map_socc_code_fkey; Type: FK CONSTRAINT; Schema: dbo; Owner: -
--

ALTER TABLE ONLY dbo.socc2018_to_cip2020_map
    ADD CONSTRAINT socc2018_to_cip2020_map_socc_code_fkey FOREIGN KEY (socc_code) REFERENCES dbo.socc_2018(socc_code) ON UPDATE CASCADE;


--
-- PostgreSQL database dump complete
--
