SELECT
	-- Job Posting Details
    jp.job_posting_id,
    jp.job_title,
	jp.publish_date,
	jp.unpublish_date AS 'Application Deadline',

    -- User details
    CONCAT(u.first_name, ' ', u.last_name) AS Applicant,
    u.email,

    -- Job Application Details
	jsjp.jobseekerId,
    jsjp.appliedDate AS JobApplicationDate,
	jsjp.jobStatus

FROM dbo.jobseekers AS j
JOIN dbo.users AS u
    ON j.user_id = u.id
JOIN dbo.JobseekerJobPosting AS jsjp
    ON j.jobseeker_id = jsjp.jobseekerId
JOIN dbo.job_postings as jp
	ON jp.job_posting_id = jsjp.jobPostId

ORDER BY JobApplicationDate DESC;
