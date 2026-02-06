SELECT

    j.jobseeker_id,
    j.user_id ,
    u.first_name,
    u.last_name,
	u.email,
    j.careerPrepTrackRecommendation,
	cm.prepEnrollmentStatus AS 'CP Enrollment Status',
	j.highest_level_of_study_completed AS HighestEdLevel,
	j.assignedPool                AS 'Pool Type',
    p.pathway_title AS 'Pathway Title',
    j.created_at                  AS JobseekerCreatedAt,
    j.updated_at                  AS JobseekerUpdatedAt,
    cm.createdAt                  AS EnrollmentDate,
    cpa.assessmentDate            AS careerPrepAssessmentDate


   
    
    -- Pathway name

FROM dbo.jobseekers AS j
JOIN dbo.users AS u
    ON j.user_id = u.id

LEFT JOIN dbo.pathways AS p
    ON j.targeted_pathway = p.pathway_id
LEFT JOIN dbo.CareerPrepAssessment AS cpa
    ON j.jobseeker_id = cpa.jobseekerId
LEFT JOIN dbo.CaseMgmt AS cm
    ON j.jobseeker_id = cm.jobseekerId

-- Filter for those who qualify for Career Prep
WHERE j.careerPrepTrackRecommendation IS NOT NULL

ORDER BY 
    j.jobseeker_id;  -- or u.last_name, etc.
