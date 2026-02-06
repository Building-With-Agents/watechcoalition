SELECT
    -- Jobseeker field
    j.jobseeker_id,
	j.created_at AS JobseekerCreatedAt,
    j.updated_at AS JobseekerUpdatedAt,

	-- User fields
    u.first_name,
    u.last_name,
    u.email,

	-- Jobseeker field
    j.assignedPool,
    j.highest_level_of_study_completed,
    j.careerPrepTrackRecommendation,
    j.is_enrolled_ed_program,
   

    -- Derived columns for Education:
    CASE
        WHEN EXISTS (
            SELECT 1
            FROM dbo.jobseekers_education je
            WHERE je.jobseeker_id = j.jobseeker_id
        )
        THEN 'Yes'
        ELSE 'No'
    END AS HasEducationHistory,

      -- Coalition Education Provider Name (If Exists)
    (
        SELECT TOP 1 ep.name
        FROM dbo.jobseekers_education je
        JOIN dbo.edu_providers ep
            ON je.edu_provider_id = ep.id
        WHERE je.jobseeker_id = j.jobseeker_id
          AND ep.isCoalitionMember = 1
    ) AS HasCoalitionEducation,

    -- Derived column for any Work Experience:
    CASE
        WHEN EXISTS (
            SELECT 1
            FROM dbo.work_experiences we
            WHERE we.jobseeker_id = j.jobseeker_id
        )
        THEN 'Yes'
        ELSE 'No'
    END AS HasWorkExperience,

    -- Derived column for *technical* Work Experience:
    CASE
        WHEN EXISTS (
            SELECT 1
            FROM dbo.work_experiences we
            JOIN dbo.technology_areas ta
                ON we.tech_area_id = ta.id
            WHERE we.jobseeker_id = j.jobseeker_id
              AND ta.title <> 'N/A Not an IT role'
        )
        THEN 'Yes'
        ELSE 'No'
    END AS HasTechnicalWorkExperience,


    -- Pathway fields
    p.pathway_title AS targetedPathwayTitle

FROM dbo.jobseekers AS j
JOIN dbo.users AS u
    ON j.user_id = u.id
LEFT JOIN dbo.pathways AS p
    ON j.targeted_pathway = p.pathway_id
ORDER BY
    u.last_name;
