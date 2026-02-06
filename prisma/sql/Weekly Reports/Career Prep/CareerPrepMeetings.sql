SELECT
    -- Jobseeker fields
   j.jobseeker_id,

    -- CaseMgmt
    cm.prepEnrollmentStatus,

    -- User fields
    u.first_name,
    u.last_name,

    -- Meeting fields
    m.id           AS MeetingId,
    m.title        AS MeetingTitle,
    m.meetingAgenda,
    m.meetingDate,
    m.updatedAt    AS MeetingUpdatedAt

FROM dbo.Meeting AS m
JOIN dbo.jobseekers AS j
    ON m.jobseekerId = j.jobseeker_id
JOIN dbo.users AS u
    ON j.user_id = u.id
LEFT JOIN dbo.pathways AS p
    ON j.targeted_pathway = p.pathway_id
LEFT JOIN dbo.CareerPrepAssessment AS cpa
    ON j.jobseeker_id = cpa.jobseekerId
LEFT JOIN dbo.CaseMgmt AS cm
    ON j.jobseeker_id = cm.jobseekerId

-- Only jobseekers who qualify for Career Prep
WHERE j.careerPrepTrackRecommendation IS NOT NULL

ORDER BY
    m.meetingDate;
