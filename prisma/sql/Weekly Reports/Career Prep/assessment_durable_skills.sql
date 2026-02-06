SELECT
    j.jobseeker_id,
    u.first_name,
    u.last_name,
    u.email,

    -- Convert each numeric field to the corresponding word
    CASE dsr.emotionManagement
        WHEN 1 THEN 'beginner'
        WHEN 2 THEN 'competent'
        WHEN 3 THEN 'proficient'
        WHEN 4 THEN 'proficient'
        WHEN 5 THEN 'expert'
        ELSE 'N/A'
    END AS [Emotion Management],

    CASE dsr.empathy
        WHEN 1 THEN 'beginner'
        WHEN 2 THEN 'competent'
        WHEN 3 THEN 'proficient'
        WHEN 4 THEN 'proficient'
        WHEN 5 THEN 'expert'
        ELSE 'N/A'
    END AS [Empathy],

    CASE dsr.goalSetting
        WHEN 1 THEN 'beginner'
        WHEN 2 THEN 'competent'
        WHEN 3 THEN 'proficient'
        WHEN 4 THEN 'proficient'
        WHEN 5 THEN 'expert'
        ELSE 'N/A'
    END AS [Goal Setting],

    CASE dsr.timeManagement
        WHEN 1 THEN 'beginner'
        WHEN 2 THEN 'competent'
        WHEN 3 THEN 'proficient'
        WHEN 4 THEN 'proficient'
        WHEN 5 THEN 'expert'
        ELSE 'N/A'
    END AS [Time Management],

    CASE dsr.adaptability
        WHEN 1 THEN 'beginner'
        WHEN 2 THEN 'competent'
        WHEN 3 THEN 'proficient'
        WHEN 4 THEN 'proficient'
        WHEN 5 THEN 'expert'
        ELSE 'N/A'
    END AS [Adaptability],

    CASE dsr.criticalThinking
        WHEN 1 THEN 'beginner'
        WHEN 2 THEN 'competent'
        WHEN 3 THEN 'proficient'
        WHEN 4 THEN 'proficient'
        WHEN 5 THEN 'expert'
        ELSE 'N/A'
    END AS [Critical Thinking],

    CASE dsr.creativity
        WHEN 1 THEN 'beginner'
        WHEN 2 THEN 'competent'
        WHEN 3 THEN 'proficient'
        WHEN 4 THEN 'proficient'
        WHEN 5 THEN 'expert'
        ELSE 'N/A'
    END AS [Creativity],

    CASE dsr.resilience
        WHEN 1 THEN 'beginner'
        WHEN 2 THEN 'competent'
        WHEN 3 THEN 'proficient'
        WHEN 4 THEN 'proficient'
        WHEN 5 THEN 'expert'
        ELSE 'N/A'
    END AS [Resilience],

    CASE dsr.communication
        WHEN 1 THEN 'beginner'
        WHEN 2 THEN 'competent'
        WHEN 3 THEN 'proficient'
        WHEN 4 THEN 'proficient'
        WHEN 5 THEN 'expert'
        ELSE 'N/A'
    END AS [Communication],

    CASE dsr.activeListening
        WHEN 1 THEN 'beginner'
        WHEN 2 THEN 'competent'
        WHEN 3 THEN 'proficient'
        WHEN 4 THEN 'proficient'
        WHEN 5 THEN 'expert'
        ELSE 'N/A'
    END AS [Active Listening],

    CASE dsr.conflictResolution
        WHEN 1 THEN 'beginner'
        WHEN 2 THEN 'competent'
        WHEN 3 THEN 'proficient'
        WHEN 4 THEN 'proficient'
        WHEN 5 THEN 'expert'
        ELSE 'N/A'
    END AS [Conflict Resolution],

    CASE dsr.nonverbalCommunication
        WHEN 1 THEN 'beginner'
        WHEN 2 THEN 'competent'
        WHEN 3 THEN 'proficient'
        WHEN 4 THEN 'proficient'
        WHEN 5 THEN 'expert'
        ELSE 'N/A'
    END AS [Nonverbal Communication],

    CASE dsr.teamwork
        WHEN 1 THEN 'beginner'
        WHEN 2 THEN 'competent'
        WHEN 3 THEN 'proficient'
        WHEN 4 THEN 'proficient'
        WHEN 5 THEN 'expert'
        ELSE 'N/A'
    END AS [Teamwork],

    CASE dsr.trustBuilding
        WHEN 1 THEN 'beginner'
        WHEN 2 THEN 'competent'
        WHEN 3 THEN 'proficient'
        WHEN 4 THEN 'proficient'
        WHEN 5 THEN 'expert'
        ELSE 'N/A'
    END AS [Trust Building],

    CASE dsr.leadership
        WHEN 1 THEN 'beginner'
        WHEN 2 THEN 'competent'
        WHEN 3 THEN 'proficient'
        WHEN 4 THEN 'proficient'
        WHEN 5 THEN 'expert'
        ELSE 'N/A'
    END AS [Leadership],

    CASE dsr.perspectiveTaking
        WHEN 1 THEN 'beginner'
        WHEN 2 THEN 'competent'
        WHEN 3 THEN 'proficient'
        WHEN 4 THEN 'proficient'
        WHEN 5 THEN 'expert'
        ELSE 'N/A'
    END AS [Perspective Taking],

    CASE dsr.culturalAwareness
        WHEN 1 THEN 'beginner'
        WHEN 2 THEN 'competent'
        WHEN 3 THEN 'proficient'
        WHEN 4 THEN 'proficient'
        WHEN 5 THEN 'expert'
        ELSE 'N/A'
    END AS [Cultural Awareness],

    CASE dsr.relationshipBuilding
        WHEN 1 THEN 'beginner'
        WHEN 2 THEN 'competent'
        WHEN 3 THEN 'proficient'
        WHEN 4 THEN 'proficient'
        WHEN 5 THEN 'expert'
        ELSE 'N/A'
    END AS [Relationship Building],

    CASE dsr.documentationSkills
        WHEN 1 THEN 'beginner'
        WHEN 2 THEN 'competent'
        WHEN 3 THEN 'proficient'
        WHEN 4 THEN 'proficient'
        WHEN 5 THEN 'expert'
        ELSE 'N/A'
    END AS [Documentation Skills],

    dsr.overallAverage AS [Overall Average]
    
FROM dbo.DurableSkillsRating AS dsr
JOIN dbo.jobseekers AS j
    ON dsr.jobseekerId = j.jobseeker_id
JOIN dbo.users AS u
    ON j.user_id = u.id
ORDER BY dsr.jobseekerId;
