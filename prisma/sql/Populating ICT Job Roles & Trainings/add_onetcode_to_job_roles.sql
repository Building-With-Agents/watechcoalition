UPDATE JobRole
SET onetCode = CASE title
    WHEN 'Product Manager' THEN '15-1299.09'
    WHEN 'Information Security Specialist' THEN '15-1212.00'
    WHEN 'Senior Software Development Engineer' THEN '15-1252.00'
    WHEN 'Quality Assurance Analyst' THEN '15-1253.00'
    WHEN 'Software Architect' THEN '15-1299.08'
    WHEN 'Java Developer' THEN '15-1252.00'
    WHEN 'Project Manager' THEN '15-1299.09'
    WHEN 'UX Designer' THEN '15-1255.00'
    WHEN 'Data Specialist' THEN '15-2051.00'
    WHEN 'Business Systems Analyst' THEN '15-1211.00'
    WHEN 'Network and IT Automation Engineer' THEN '15-1244.00'
    WHEN 'Customer Service Representative' THEN '43-4051.00'
    WHEN 'Cloud Engineer' THEN '15-1241.00'
    WHEN 'Ethical Hacker' THEN '15-1299.04'
    WHEN 'AI/ML Engineer' THEN '15-2051.00'
    WHEN 'Network Support Technician' THEN '15-1231.00'
    WHEN 'Soc Analyst Level 1' THEN '15-1212.00'
    WHEN 'Digital Marketing Specialist' THEN '13-1161.01'
    WHEN 'Design Engineer' THEN '27-1021.00'
    WHEN 'Back-End Developer' THEN '15-1252.00'
    WHEN 'Front-End Developer' THEN '15-1254.00'
    WHEN 'Senior Product Manager' THEN '11-1021.00'
    WHEN 'Systems Administrator' THEN '15-1244.00'
    WHEN 'Technical Writer' THEN '27-3042.00'
    WHEN 'Data Analyst' THEN '15-2051.00'
    WHEN 'Web Developer' THEN '15-1254.00'
    WHEN 'Help Desk Analyst' THEN '15-1232.00'
    WHEN 'Product Design Engineer' THEN '27-1021.00'
    WHEN 'Senior Software Engineer' THEN '15-1252.00'
    WHEN 'Senior Network Engineer' THEN '15-1241.00'
    WHEN 'Data Scientist' THEN '15-2051.00'
    WHEN 'Systems Analyst' THEN '15-1211.00'
    WHEN 'Application Developer' THEN '15-1251.00'
    WHEN 'Network Administrator' THEN '15-1244.00'
    WHEN 'Software Test and Debug' THEN '15-1253.00'
    WHEN 'AI-Enabled Technical Sales Representative' THEN '41-4011.00'
    WHEN 'Database Administrator' THEN '15-1242.00'
    WHEN 'Cybersecurity Analyst' THEN '15-1212.00'
    WHEN 'Principal Software Engineer' THEN '15-1252.00'
    WHEN 'Software Developer' THEN '15-1252.00'
    WHEN 'Software Engineer' THEN '15-1252.00'
    WHEN 'Full-Stack Developer' THEN '15-1252.00'
    WHEN 'Business Intelligence Analyst' THEN '15-2051.01'
    WHEN 'Business Analyst' THEN '15-1211.00'
    WHEN 'IT Support Technician' THEN '15-1232.00'
    WHEN 'IT Manager' THEN '11-3021.00'
    WHEN 'Python Developer' THEN '15-1252.00'
    WHEN 'Data Engineer' THEN '15-1243.00'
    ELSE onetCode
END
WHERE title IN (
    'Product Manager',
    'Information Security Specialist',
    'Senior Software Development Engineer',
    'Quality Assurance Analyst',
    'Software Architect',
    'Java Developer',
    'Project Manager',
    'UX Designer',
    'Data Specialist',
    'Business Systems Analyst',
    'Network and IT Automation Engineer',
    'Customer Service Representative',
    'Cloud Engineer',
    'Ethical Hacker',
    'AI/ML Engineer',
    'Network Support Technician',
    'Soc Analyst Level 1',
    'Digital Marketing Specialist',
    'Design Engineer',
    'Back-End Developer',
    'Front-End Developer',
    'Senior Product Manager',
    'Systems Administrator',
    'Technical Writer',
    'Data Analyst',
    'Web Developer',
    'Help Desk Analyst',
    'Product Design Engineer',
    'Senior Software Engineer',
    'Senior Network Engineer',
    'Data Scientist',
    'Systems Analyst',
    'Application Developer',
    'Network Administrator',
    'Software Test and Debug',
    'AI-Enabled Technical Sales Representative',
    'Database Administrator',
    'Cybersecurity Analyst',
    'Principal Software Engineer',
    'Software Developer',
    'Software Engineer',
    'Full-Stack Developer',
    'Business Intelligence Analyst',
    'Business Analyst',
    'IT Support Technician',
    'IT Manager',
    'Python Developer',
    'Data Engineer'
);
