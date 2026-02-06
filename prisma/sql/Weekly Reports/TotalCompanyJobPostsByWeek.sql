SELECT 
    CASE 
        WHEN GROUPING(YEAR(jp.publish_date)) = 1 THEN 'All Years'
        ELSE CAST(YEAR(jp.publish_date) AS VARCHAR(4))
    END AS [Year],
    CASE 
        WHEN GROUPING(DATEPART(WEEK, jp.publish_date)) = 1 THEN 'All Weeks'
        ELSE CAST(DATEPART(WEEK, jp.publish_date) AS VARCHAR(2))
    END AS [WeekNumber],
    COUNT(DISTINCT c.company_id) AS [TotalCompanies],
    COUNT(DISTINCT jp.job_posting_id) AS [TotalJobPosts],
    -- Count only those job_posting_ids whose unpublish_date hasn't passed
    COUNT(
        DISTINCT CASE 
            WHEN jp.unpublish_date IS NULL OR jp.unpublish_date > GETDATE() 
            THEN jp.job_posting_id 
        END
    ) AS [ActiveJobPosts]
FROM dbo.companies AS c
LEFT JOIN dbo.job_postings AS jp
    ON c.company_id = jp.company_id
GROUP BY 
    ROLLUP (
        YEAR(jp.publish_date),
        DATEPART(WEEK, jp.publish_date)
    )
ORDER BY
    CASE WHEN GROUPING(YEAR(jp.publish_date)) = 1 THEN 9999 
         ELSE YEAR(jp.publish_date) 
    END,
    CASE WHEN GROUPING(DATEPART(WEEK, jp.publish_date)) = 1 THEN 999
         ELSE DATEPART(WEEK, jp.publish_date)
    END;
