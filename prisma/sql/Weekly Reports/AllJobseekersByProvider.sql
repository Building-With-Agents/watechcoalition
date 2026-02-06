SELECT 
	-- ep.id as eduProviderId,
    ep.name                         AS provider_name,
    CASE WHEN ep.isCoalitionMember = 1 THEN 'Yes' ELSE 'No' END AS isCoalitionMember,
    COUNT(DISTINCT je.jobseeker_id) AS total_enrolled_jobseekers
FROM dbo.edu_providers       AS ep
JOIN dbo.jobseekers_education AS je
    ON ep.id = je.edu_provider_id
GROUP BY 
    ep.id,
    ep.name,
    ep.isCoalitionMember
ORDER BY 
    ep.name;
