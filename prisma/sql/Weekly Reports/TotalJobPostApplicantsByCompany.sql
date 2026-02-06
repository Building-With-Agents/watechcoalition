SELECT
    c.company_name,
    COUNT(DISTINCT jp.job_posting_id) AS total_job_posts,
    COUNT(DISTINCT jjp.jobseekerId)    AS total_applicants
FROM dbo.companies c
LEFT JOIN dbo.job_postings jp
    ON c.company_id = jp.company_id
LEFT JOIN dbo.JobseekerJobPosting jjp
    ON jp.job_posting_id = jjp.jobPostId
GROUP BY 
    c.company_name
ORDER BY 
    c.company_name;
