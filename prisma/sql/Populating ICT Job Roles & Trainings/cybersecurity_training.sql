------------------------------------------------------------------
-- Refactored T-SQL Script for Cybersecurity Trainings Using URL Uniqueness
------------------------------------------------------------------

-------------------------------
-- Block 1: Cybersecurity Foundational Training Records (With URLs)
-------------------------------
BEGIN TRAN;

MERGE [dbo].[Training] AS target
USING (VALUES
           ('Agile Explorer', 'https://ibm.biz/BdGpZ8', 'IBM', 'Agile thinking, Agile methodologies'),
           ('AI Canon', 'https://a16z.com/ai-canon/', 'AI Canon', 'AI literacy'),
           ('AI Essentials Course', 'https://grow.google/ai-essentials/', 'Google', 'AI literacy'),
           ('AI Ethics', 'https://ibm.biz/BdGpZA', 'IBM', 'Ethical and Responsible AI, AI ethics and governance'),
           ('AI for Everyone by Andrew Ng', 'https://www.coursera.org/learn/ai-for-everyone', 'Coursera', 'AI literacy'),
           ('AI Fundamentals', 'https://ibm.biz/BdGpZ9', 'IBM', 'AI Fundamentals'),
           ('AI Security Nuggets', 'https://www.netacad.com/modules/ai-security-nuggets?courseLang=en-US', 'Cisco', 'AI regulations, AI threat modeling, AI supply chain, Retrieval Augmented Generation (RAG), LLM stack'),
           ('Building AI Literacy', 'https://www.linkedin.com/learning/paths/building-ai-literacy?u=26890602', 'LinkedIn', 'AI literacy'),
           ('Building Career Agility and Resilience in the Age of AI', 'https://www.linkedin.com/learning/building-career-agility-and-resilience-in-the-age-of-ai/prepare-for-your-ai-enhanced-career?u=104', 'LinkedIn', 'AI technologies skills to develop a "future-proof career mindset"'),
           ('Career Management Essentials', 'https://ibm.biz/BdGpZT', 'IBM', 'Career development, Career management, Communication skills, Generative AI tool use, Networking skills, Presentation skills, Professional interviewing skills, Professional online brand development, Resume writing, Socialmedia presence, Workplace research'),
           ('Creating compelling Reports', 'https://skillsforall.com/course/compelling-reports', 'Cisco', 'Communication, presentation'),
           ('Cybersecurity Essentials', 'https://www.netacad.com/catalogs/learn/cybersecurity', 'Cisco', 'Cybersecurity literacy, Asset protection, Security response, Network protection, Product expertise, Data breach analysis, Data defense, Cybersecurity policies'),
           ('Cybersecurity Fundamentals', 'https://www.credly.com/org/ibm-skillsbuild/badge/cybersecurity-fundamentals', 'IBM', 'Cybersecurity literacy, Cryptography, Cyber Attacks, Cyber threat analysis, Cyber threat analysis intelligence, Cybersecurity risk management'),
           ('Develop Your Prompt Engineering Skills', 'https://www.linkedin.com/learning/paths/develop-your-prompt-engineering-skills?u=104', 'LinkedIn', 'Prompt engineering'),
           ('Digital Literacy', 'https://ibm.biz/BdGhnB', 'IBM', 'AI, Collaboration, Computer literacy, Data analysis, Data presentation, Digital communications, Digital literacy, Employability skills, Internet security, Software engineering, Web navigation'),
           ('Digital Mindset', 'https://ibm.biz/BdGpYc', 'IBM', 'Adaptability and flexibility, Collaboration, Creativity, Data-driven decisions, Decision making, Digital mindset, Employability skills, Entrepreneurial mindset, Growth mindset, Innovation, Lifelong learning, Managing ambiguity and change, Professional networking, Teamwork'),
           ('Engaging Stakeholders for Success', 'https://skillsforall.com/course/engaging-stakeholders', 'Cisco', 'Communication, Stakeholder engagement, Change Management'),
           ('Explore Emerging Tech', 'https://www.credly.com/org/ibm-skillsbuild/badge/explore-emerging-tech', 'IBM', 'Artificial intelligence, data, blockchain, cloud, cybersecurity, iot'),
           ('Introduction to Artificial Intelligence', 'https://academy.aiskills.eu/course/1-introduction-to-artificial-intelligence', 'DIGITALEUROPE', 'Machine Learning, Deep Learning, Natural Language Processing, Computer Vision, Data Science Fundamentals, AI Ethics and Governance'),
           ('Introduction to Data Analytics', 'https://www.coursera.org/learn/introduction-to-data-analytics', 'IBM / Coursera', 'Data analysis, data visualization, Microsoft excel'),
           ('Introduction to modern AI', 'https://skillsforall.com/course/introduction-to-modern-ai?courseLang=en-US', 'Cisco', 'AI literacy'),
           ('Introduction to Prompt Engineering', 'https://www.edx.org/learn/artificial-intelligence/ibm-introduction-to-prompt-engineering', 'IBM / EDX', 'Prompt engineering'),
           ('Introduction to Responsible AI Skills', 'https://www.netacad.com/modules/introduction-to-responsible-ai-skills?courseLang=en-US', 'Cisco / Intel', 'Ethical and Responsible AI, AI ethics and governance'),
           ('Responsible AI Foundations', 'https://www.linkedin.com/learning/paths/responsible-ai-foundations', 'LinkedIn', 'Ethical and Responsible AI, AI ethics and governance'),
           ('Working in a Digital World: Professional Skills', 'https://www.credly.com/org/ibm-skillsbuild/badge/working-in-a-digital-world-professional-skills', 'IBM', 'Agile methodologies, business acumen, creative thinking, critical thinking, communication, problem solving, solutioning')
) AS source(title, url, provider, skillsDeveloped)
ON target.url = source.url
WHEN NOT MATCHED THEN
    INSERT (id, title, url, provider, skillsDeveloped)
    VALUES (NEWID(), source.title, source.url, source.provider, source.skillsDeveloped);

COMMIT TRAN;

-------------------------------
-- Block 1.2: Link Foundational Trainings to the "Cybersecurity" Job Group
-------------------------------
BEGIN TRAN;

INSERT INTO [dbo].[PathwayTraining] (id, pathwayId, trainingId)
SELECT NEWID(), p.pathway_id, t.id
FROM [dbo].[pathways] p
         JOIN [dbo].[Training] t ON t.url IN (
                                              'https://ibm.biz/BdGpZ8',
                                              'https://a16z.com/ai-canon/',
                                              'https://grow.google/ai-essentials/',
                                              'https://ibm.biz/BdGpZA',
                                              'https://www.coursera.org/learn/ai-for-everyone',
                                              'https://ibm.biz/BdGpZ9',
                                              'https://www.netacad.com/catalogs/learn/cybersecurity',
                                              'https://www.linkedin.com/learning/paths/building-ai-literacy?u=26890602',
                                              'https://www.linkedin.com/learning/building-career-agility-and-resilience-in-the-age-of-ai/prepare-for-your-ai-enhanced-career?u=104',
                                              'https://ibm.biz/BdGpZT',
                                              'https://skillsforall.com/course/compelling-reports',
                                              'https://www.credly.com/org/ibm-skillsbuild/badge/cybersecurity-fundamentals',
                                              'https://www.linkedin.com/learning/paths/develop-your-prompt-engineering-skills?u=104',
                                              'https://ibm.biz/BdGhnB',
                                              'https://ibm.biz/BdGpYc',
                                              'https://skillsforall.com/course/engaging-stakeholders',
                                              'https://www.credly.com/org/ibm-skillsbuild/badge/explore-emerging-tech',
                                              'https://academy.aiskills.eu/course/1-introduction-to-artificial-intelligence',
                                              'https://www.coursera.org/learn/introduction-to-data-analytics',
                                              'https://skillsforall.com/course/introduction-to-modern-ai?courseLang=en-US',
                                              'https://www.edx.org/learn/artificial-intelligence/ibm-introduction-to-prompt-engineering',
                                              'https://www.netacad.com/modules/introduction-to-responsible-ai-skills?courseLang=en-US',
                                              'https://www.linkedin.com/learning/paths/responsible-ai-foundations',
                                              'https://www.credly.com/org/ibm-skillsbuild/badge/working-in-a-digital-world-professional-skills'
    )
WHERE p.pathway_title = 'Cybersecurity';

COMMIT TRAN;

-------------------------------
-- Block 2: Job-Specific Trainings for "Cybersecurity Analyst"
-------------------------------
BEGIN TRAN;

MERGE [dbo].[Training] AS target
USING (VALUES
           ('Cybersecurity Analyst Professional Certificate', 'https://www.coursera.org/professional-certificates/ibm-cybersecurity-analyst', 'IBM / Coursera', 'Information security analyst, Junior cybersecurity analyst, IT security analyst, security analyst'),
           ('Cybersecurity Certificate', 'https://www.credly.com/org/ibm-skillsbuild/badge/ibm-skillsbuild-cybersecurity-certificate', 'IBM', 'Governance, Risk, Compliance and Data Privacy; Vulnerability Management; System and Network Security; Cloud Security; Security Operations Management; Incident Response and System Forensics'),
           ('Cybersecurity Certificate', 'https://www.coursera.org/professional-certificates/google-cybersecurity', 'Google / Coursera', NULL), -- No Skills Developed listed
           ('Junior Cybersecurity Analyst Career path', 'https://skillsforall.com/career-path/cybersecurity?courseLang=en-US', 'Cisco', 'Vulnerability management, risk analysis, security policies, risk management, firewall, security information and event management (SIEM), information systems security, governance, vulnerability assessments, penetration testing, access controls, malware analysis')
) AS source(title, url, provider, skillsDeveloped)
ON target.url = source.url
WHEN NOT MATCHED THEN
    INSERT (id, title, url, provider, skillsDeveloped)
    VALUES (NEWID(), source.title, source.url, source.provider, source.skillsDeveloped);

COMMIT TRAN;

BEGIN TRAN;

INSERT INTO [dbo].[JobRoleTraining] (id, jobRoleId, trainingId)
SELECT NEWID(), jr.id, t.id
FROM [dbo].[JobRole] jr
         JOIN [dbo].[Training] t ON t.url IN (
                                              'https://www.coursera.org/professional-certificates/ibm-cybersecurity-analyst',
                                              'https://www.credly.com/org/ibm-skillsbuild/badge/ibm-skillsbuild-cybersecurity-certificate',
                                              'https://www.coursera.org/professional-certificates/google-cybersecurity',
                                              'https://skillsforall.com/career-path/cybersecurity?courseLang=en-US'
    )
WHERE jr.title = 'Cybersecurity Analyst'
  AND jr.pathwayId = (SELECT pathway_id FROM [dbo].[pathways] WHERE pathway_title = 'Cybersecurity');

COMMIT TRAN;

-------------------------------
-- Block 3: Job-Specific Trainings for "Ethical Hacker"
-------------------------------
BEGIN TRAN;

MERGE [dbo].[Training] AS target
USING (VALUES
           ('Cyber Threat Intelligence', 'https://www.coursera.org/learn/ibm-cyber-threat-intelligence', 'IBM / Coursera', 'Cybersecurity, network defensive tactics, threat intelligence, Application Security, security analyst'),
           ('Cybersecurity Analyst Professional Certificate', 'https://www.coursera.org/professional-certificates/ibm-cybersecurity-analyst', 'IBM / Coursera', 'Information security analyst, Junior cybersecurity analyst, IT security analyst, security analyst'),
           ('Cybersecurity Capstone: Breach Response Case Studies', 'https://www.coursera.org/learn/ibm-cybersecurity-breach-case-studies', 'IBM / Coursera', 'Computer Security Incident Management, Cybersecurity, Breach (Security Exploit), security analyst, cyber attack'),
           ('Cybersecurity Certificate', 'https://www.credly.com/org/ibm-skillsbuild/badge/ibm-skillsbuild-cybersecurity-certificate', 'IBM', 'Governance, Risk, Compliance, and Data Privacy; Vulnerability Management; System and Network Security; Cloud Security; Security Operations Management; and Incident Response and System Forensics'),
           ('Cybersecurity Compliance Framework, Standards & Regulations', 'https://www.coursera.org/learn/cybersecurity-compliance-framework-standards-regulations', 'IBM / Coursera', 'Risk Management, Laws and Regulations, Cybersecurity Compliance, Cybersecurity Framework, Cybersecurity Standards'),
           ('Cybersecurity Certificate', 'https://www.coursera.org/professional-certificates/google-cybersecurity', 'Google / Coursera', 'Python Programming, SQL, Linux, IDS, Security Information and Event Management (SIEM) tools'),
           ('Junior Cybersecurity Analyst Career path', 'https://skillsforall.com/career-path/cybersecurity?courseLang=en-US', 'Cisco', 'Vulnerability management, risk analysis, security policies, risk management, firewall, security information and event management (SIEM), information systems security, governance, vulnerability assessments, penetration testing, access controls, malware analysis'),
           ('Network Security & Database Vulnerabilities', 'https://www.coursera.org/learn/network-security-database-vulnerabilities', 'IBM / Coursera', 'Networking basics, Cybersecurity, Network Security, database vulnerabilities, Sql injection'),
           ('Operating Systems: Overview, Administration, and Security', 'https://www.coursera.org/learn/operating-systems-overview-administration-security', 'IBM / Coursera', 'Operating Systems, Directory and File Management, User (Computing), Virtualization, Linux, Windows, MacOS, User Accounts'),
           ('Penetration Testing, Incident Response and Forensics', 'https://www.coursera.org/learn/ibm-penetration-testing-incident-response-forensics', 'IBM / Coursera', 'Computer Security Incident Management, scripting, Cybersecurity, forensics, Penetration Test')
) AS source(title, url, provider, skillsDeveloped)
ON target.url = source.url
WHEN NOT MATCHED THEN
    INSERT (id, title, url, provider, skillsDeveloped)
    VALUES (NEWID(), source.title, source.url, source.provider, source.skillsDeveloped);

COMMIT TRAN;

BEGIN TRAN;

INSERT INTO [dbo].[JobRoleTraining] (id, jobRoleId, trainingId)
SELECT NEWID(), jr.id, t.id
FROM [dbo].[JobRole] jr
         JOIN [dbo].[Training] t ON t.url IN (
                                              'https://www.coursera.org/learn/ibm-cyber-threat-intelligence',
                                              'https://www.coursera.org/professional-certificates/ibm-cybersecurity-analyst',
                                              'https://www.coursera.org/learn/ibm-cybersecurity-breach-case-studies',
                                              'https://www.credly.com/org/ibm-skillsbuild/badge/ibm-skillsbuild-cybersecurity-certificate',
                                              'https://www.coursera.org/learn/cybersecurity-compliance-framework-standards-regulations',
                                              'https://www.coursera.org/professional-certificates/google-cybersecurity',
                                              'https://skillsforall.com/career-path/cybersecurity?courseLang=en-US',
                                              'https://www.coursera.org/learn/network-security-database-vulnerabilities',
                                              'https://www.coursera.org/learn/operating-systems-overview-administration-security',
                                              'https://www.coursera.org/learn/ibm-penetration-testing-incident-response-forensics'
    )
WHERE jr.title = 'Ethical Hacker'
  AND jr.pathwayId = (SELECT pathway_id FROM [dbo].[pathways] WHERE pathway_title = 'Cybersecurity');

COMMIT TRAN;

-------------------------------
-- Block 4: Job-Specific Trainings for "Information Security Specialist"
-------------------------------
BEGIN TRAN;

MERGE [dbo].[Training] AS target
USING (VALUES
           ('Cyber Threat Intelligence', 'https://www.coursera.org/learn/ibm-cyber-threat-intelligence', 'IBM / Coursera', 'Cybersecurity, network defensive tactics, threat intelligence, Application Security, security analyst'),
           ('Cybersecurity Analyst Professional Certificate', 'https://www.coursera.org/professional-certificates/ibm-cybersecurity-analyst', 'IBM / Coursera', 'Information security analyst, Junior cybersecurity analyst, IT security analyst, security analyst'),
           ('Cybersecurity Capstone: Breach Response Case Studies', 'https://www.coursera.org/learn/ibm-cybersecurity-breach-case-studies', 'IBM / Coursera', 'Computer Security Incident Management, Cybersecurity, Breach (Security Exploit), security analyst, cyber attack'),
           ('Cybersecurity Certificate', 'https://www.credly.com/org/ibm-skillsbuild/badge/ibm-skillsbuild-cybersecurity-certificate', 'IBM', 'Governance, Risk, Compliance, and Data Privacy; Vulnerability Management; System and Network Security; Cloud Security; Security Operations Management; and Incident Response and System Forensics'),
           ('Cybersecurity Compliance Framework, Standards & Regulations', 'https://www.coursera.org/learn/cybersecurity-compliance-framework-standards-regulations', 'IBM / Coursera', 'Risk Management, Laws and Regulations, Cybersecurity Compliance, Cybersecurity Framework, Cybersecurity Standards'),
           ('Cybersecurity Certificate', 'https://www.coursera.org/professional-certificates/google-cybersecurity', 'Google / Coursera', 'Python Programming, SQL, Linux, IDS, Security Information and Event Management (SIEM) tools'),
           ('Junior Cybersecurity Analyst Career path', 'https://skillsforall.com/career-path/cybersecurity?courseLang=en-US', 'Cisco', 'Vulnerability management, risk analysis, security policies, risk management, firewall, security information and event management (SIEM), information systems security, governance, vulnerability assessments, penetration testing, access controls, malware analysis'),
           ('Network Security & Database Vulnerabilities', 'https://www.coursera.org/learn/network-security-database-vulnerabilities', 'IBM / Coursera', 'Networking basics, Cybersecurity, Network Security, database vulnerabilities, Sql Injection'),
           ('Operating Systems: Overview, Administration, and Security', 'https://www.coursera.org/learn/operating-systems-overview-administration-security', 'IBM / Coursera', 'Operating Systems, Directory and File Management, User (Computing), Virtualization, Linux, Windows, MacOS, User Accounts'),
           ('Penetration Testing, Incident Response and Forensics', 'https://www.coursera.org/learn/ibm-penetration-testing-incident-response-forensics', 'IBM / Coursera', 'Computer Security Incident Management, scripting, Cybersecurity, forensics, Penetration Test')
) AS source(title, url, provider, skillsDeveloped)
ON target.url = source.url
WHEN NOT MATCHED THEN
    INSERT (id, title, url, provider, skillsDeveloped)
    VALUES (NEWID(), source.title, source.url, source.provider, source.skillsDeveloped);

COMMIT TRAN;

BEGIN TRAN;

INSERT INTO [dbo].[JobRoleTraining] (id, jobRoleId, trainingId)
SELECT NEWID(), jr.id, t.id
FROM [dbo].[JobRole] jr
         JOIN [dbo].[Training] t ON t.url IN (
                                              'https://www.coursera.org/learn/ibm-cyber-threat-intelligence',
                                              'https://www.coursera.org/professional-certificates/ibm-cybersecurity-analyst',
                                              'https://www.coursera.org/learn/ibm-cybersecurity-breach-case-studies',
                                              'https://www.credly.com/org/ibm-skillsbuild/badge/ibm-skillsbuild-cybersecurity-certificate',
                                              'https://www.coursera.org/learn/cybersecurity-compliance-framework-standards-regulations',
                                              'https://www.coursera.org/professional-certificates/google-cybersecurity',
                                              'https://skillsforall.com/career-path/cybersecurity?courseLang=en-US',
                                              'https://www.coursera.org/learn/network-security-database-vulnerabilities',
                                              'https://www.coursera.org/learn/operating-systems-overview-administration-security',
                                              'https://www.coursera.org/learn/ibm-penetration-testing-incident-response-forensics'
    )
WHERE jr.title = 'Information Security Specialist'
  AND jr.pathwayId = (SELECT pathway_id FROM [dbo].[pathways] WHERE pathway_title = 'Cybersecurity');

COMMIT TRAN;

-------------------------------
-- Block 5: Job-Specific Trainings for "SOC Analyst Level 1"
-------------------------------
BEGIN TRAN;

MERGE [dbo].[Training] AS target
USING (VALUES
           ('Cisco - CyberOps Associate (*)', 'https://www.netacad.com/courses/cybersecurity/cyberops-associate', 'Cisco', 'Attack methods, computer forensics, cryptography, cybersecurity, data and event analysis, endpoint threat analysis, host-based analysis, incident response, malware analysis, network attacks, network intrusion analysis secops, security concepts, security monitoring, security policy, security procedures, SOC metrics, threat detection'),
           ('Machine Learning Specialization', 'https://www.coursera.org/specializations/machine-learning-introduction', 'Stanford / DeepLearning.AI', 'Logistic regression, Artificial Neural Network, Linear Regression, Decision Trees')
) AS source(title, url, provider, skillsDeveloped)
ON target.url = source.url
WHEN NOT MATCHED THEN
    INSERT (id, title, url, provider, skillsDeveloped)
    VALUES (NEWID(), source.title, source.url, source.provider, source.skillsDeveloped);

COMMIT TRAN;

BEGIN TRAN;

INSERT INTO [dbo].[JobRoleTraining] (id, jobRoleId, trainingId)
SELECT NEWID(), jr.id, t.id
FROM [dbo].[JobRole] jr
         JOIN [dbo].[Training] t ON t.url IN (
                                              'https://www.netacad.com/courses/cybersecurity/cyberops-associate',
                                              'https://www.coursera.org/specializations/machine-learning-introduction'
    )
WHERE jr.title = 'SOC Analyst Level 1'
  AND jr.pathwayId = (SELECT pathway_id FROM [dbo].[pathways] WHERE pathway_title = 'Cybersecurity');

COMMIT TRAN;
