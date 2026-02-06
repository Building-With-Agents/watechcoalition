SELECT 
--    j.jobseeker_id,
    CONCAT(u.first_name, ' ', u.last_name) AS FullName,
    u.email,
    j.assignedPool,
    j.highest_level_of_study_completed,
    j.careerPrepTrackRecommendation,
    j.is_enrolled_ed_program,
    j.created_at AS JobseekerCreatedAt,
    j.updated_at AS JobseekerUpdatedAt,

    -- Pathway Details
    p.pathway_title AS targetedPathwayTitle,

    -- Career Prep Assessment Status
    CASE 
        WHEN cpa.jobseekerId IS NOT NULL THEN 'Qualified & Assessed'
        ELSE 'Qualified but Not Assessed'
    END AS CareerPrepAssessmentStatus

FROM dbo.jobseekers AS j
JOIN dbo.users AS u
    ON j.user_id = u.id
LEFT JOIN dbo.pathways AS p
    ON j.targeted_pathway = p.pathway_id
LEFT JOIN dbo.CareerPrepAssessment AS cpa
    ON j.jobseeker_id = cpa.jobseekerId

-- Filter only jobseekers who qualify for Career Prep (CareerPrepTrackRecommendation is NOT NULL)
WHERE j.careerPrepTrackRecommendation IS NOT NULL

ORDER BY CareerPrepAssessmentStatus DESC, u.first_name;
