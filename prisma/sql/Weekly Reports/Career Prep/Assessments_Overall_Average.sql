SELECT
   -- j.jobseeker_id,
    u.first_name,
    u.last_name,
	u.email,
   -- j.careerPrepTrackRecommendation,
   -- j.assignedPool,
    j.highest_level_of_study_completed,
   -- j.is_enrolled_ed_program,
   -- j.created_at AS JobseekerCreatedAt,
   -- j.updated_at AS JobseekerUpdatedAt,
   -- p.pathway_title AS targetedPathwayTitle,
    COALESCE(CONVERT(varchar(10), br.overallAverage), 'N/A') AS BrandingRating,
    COALESCE(CONVERT(varchar(10), cr.overallAverage), 'N/A') AS CybersecurityRating,
    COALESCE(CONVERT(varchar(10), dar.overallAverage), 'N/A') AS DataAnalyticsRating,
    COALESCE(CONVERT(varchar(10), durr.overallAverage), 'N/A') AS DurableSkillsRating,
    COALESCE(CONVERT(varchar(10), itr.overallAverage), 'N/A') AS ITCloudRating,
    COALESCE(CONVERT(varchar(10), sdr.overallAverage), 'N/A') AS SoftwareDevRating
FROM dbo.jobseekers AS j
JOIN dbo.users AS u
    ON j.user_id = u.id
LEFT JOIN dbo.pathways AS p
    ON j.targeted_pathway = p.pathway_id
LEFT JOIN dbo.BrandingRating AS br
    ON j.jobseeker_id = br.jobseekerId
LEFT JOIN dbo.CybersecurityRating AS cr
    ON j.jobseeker_id = cr.jobseekerId
LEFT JOIN dbo.DataAnalyticsRating AS dar
    ON j.jobseeker_id = dar.jobseekerId
LEFT JOIN dbo.DurableSkillsRating AS durr
    ON j.jobseeker_id = durr.jobseekerId
LEFT JOIN dbo.ITCloudRating AS itr
    ON j.jobseeker_id = itr.jobseekerId
LEFT JOIN dbo.SoftwareDevRating AS sdr
    ON j.jobseeker_id = sdr.jobseekerId
WHERE j.jobseeker_id IN (
    SELECT cpa.jobseekerId
    FROM dbo.CareerPrepAssessment AS cpa
)
ORDER BY u.first_name;
