WITH Counts AS (
    -------------------------------------------------------------------------
    -- 1) Jobseekers with NO education history
    -------------------------------------------------------------------------
    SELECT
        'No Entered Education History' AS Category,
        COUNT(DISTINCT jNoEdu.jobseeker_id) AS total
    FROM dbo.jobseekers AS jNoEdu
    LEFT JOIN dbo.jobseekers_education AS jeNoEdu
        ON jNoEdu.jobseeker_id = jeNoEdu.jobseeker_id
    WHERE jeNoEdu.jobseeker_id IS NULL

    UNION ALL

    -------------------------------------------------------------------------
    -- 2) Jobseekers WITH any education history (regardless of provider)
    -------------------------------------------------------------------------
    SELECT
        'Has Entered Education History' AS Category,
        COUNT(DISTINCT jEdu.jobseeker_id) AS total
    FROM dbo.jobseekers AS jEdu
    INNER JOIN dbo.jobseekers_education AS jeEdu
        ON jEdu.jobseeker_id = jeEdu.jobseeker_id

    UNION ALL

    -------------------------------------------------------------------------
    -- 3) Jobseekers WITH education history from a Coalition Member provider
    -------------------------------------------------------------------------
    SELECT
        'Has Entered Coalition Partner in Education History' AS Category,
        COUNT(DISTINCT jCoal.jobseeker_id) AS total
    FROM dbo.jobseekers AS jCoal
    INNER JOIN dbo.jobseekers_education AS jeCoal
        ON jCoal.jobseeker_id = jeCoal.jobseeker_id
    INNER JOIN dbo.edu_providers AS ep
        ON jeCoal.edu_provider_id = ep.id
    WHERE ep.isCoalitionMember = 1
)
SELECT
    Category as 'Jobseeker Profile Education History',
    total
FROM Counts

UNION ALL

---------------------------------------------------------------------
-- 4) A final row that sums up all three totals
---------------------------------------------------------------------
SELECT
    'Sum of All 3' AS Category,
    SUM(total) AS total
FROM Counts;
