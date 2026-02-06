SELECT
    CASE 
        WHEN cpa.jobseekerId IS NOT NULL THEN 'Completed CP Assessment'
        ELSE 'Not taken Assessment'
    END AS [Assessment Status],

    CASE 
        WHEN je.jobseeker_id IS NULL THEN 'No Education'
        WHEN ep.isCoalitionMember = 1 THEN 'Partner Education'
        ELSE 'Has Education'
    END AS [Education Category],

    COUNT(DISTINCT j.jobseeker_id) AS [Count of Jobseekers]
FROM dbo.jobseekers AS j
    -- Link to jobseekers_education (may be NULL if no education)
    LEFT JOIN dbo.jobseekers_education AS je
        ON j.jobseeker_id = je.jobseeker_id
    -- Link to edu_providers (may be NULL if no education or no provider)
    LEFT JOIN dbo.edu_providers AS ep
        ON je.edu_provider_id = ep.id
    -- Link to CareerPrepAssessment (may be NULL if no assessment taken)
    LEFT JOIN dbo.CareerPrepAssessment AS cpa
        ON j.jobseeker_id = cpa.jobseekerId
GROUP BY
    CASE 
        WHEN cpa.jobseekerId IS NOT NULL THEN 'Completed CP Assessment'
        ELSE 'Not taken Assessment'
    END,
    CASE 
        WHEN je.jobseeker_id IS NULL THEN 'No Education'
        WHEN ep.isCoalitionMember = 1 THEN 'Partner Education'
        ELSE 'Has Education'
    END
ORDER BY
    [Assessment Status],
    [Education Category];
