SELECT 
    CASE 
        WHEN GROUPING(YEAR(j.created_at)) = 1 THEN 'All Years'
        ELSE CAST(YEAR(j.created_at) AS VARCHAR(4))
    END AS [Year],
    CASE 
        WHEN GROUPING(DATEPART(WEEK, j.created_at)) = 1 THEN 'All Weeks'
        ELSE CAST(DATEPART(WEEK, j.created_at) AS VARCHAR(2))
    END AS [WeekNumber],
    COUNT(DISTINCT j.jobseeker_id) AS [TotalJobseekers],
    COUNT(DISTINCT CASE WHEN ep.isCoalitionMember = 1 THEN j.jobseeker_id END) AS [PartnerEnrolled],
    CASE 
        WHEN COUNT(DISTINCT j.jobseeker_id) = 0 THEN 0
        ELSE 
            CONVERT(DECIMAL(5,2),
                100.0 * 
                COUNT(DISTINCT CASE WHEN ep.isCoalitionMember = 1 THEN j.jobseeker_id END)
                / COUNT(DISTINCT j.jobseeker_id)
            )
    END AS [PctPartnerEnrolled]
FROM dbo.jobseekers AS j
LEFT JOIN dbo.jobseekers_education AS je
    ON j.jobseeker_id = je.jobseeker_id
LEFT JOIN dbo.edu_providers AS ep
    ON je.edu_provider_id = ep.id

-- 1) Group by Year and Week, with ROLLUP
GROUP BY 
    ROLLUP (
        YEAR(j.created_at),
        DATEPART(WEEK, j.created_at)
    )

-- 2) Order so that regular rows come first, and "All" rows appear last
ORDER BY
    -- Put real years first; the row with 'All Years' has YEAR(...) = NULL
    CASE WHEN GROUPING(YEAR(j.created_at)) = 1 THEN 9999 
         ELSE YEAR(j.created_at) 
    END,
    -- Similarly, real weeks first; the subtotal row for 'All Weeks' has WEEK(...) = NULL
    CASE WHEN GROUPING(DATEPART(WEEK, j.created_at)) = 1 THEN 999 
         ELSE DATEPART(WEEK, j.created_at) 
    END;
