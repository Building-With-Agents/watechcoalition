
-------------------------------
-- Block 1.1: Foundational Trainings for "Testing and Quality Assurance" Job Group
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
           ('Building AI Literacy', 'https://www.linkedin.com/learning/paths/building-ai-literacy?u=26890602', 'LinkedIn', 'AI literacy'),
           ('Building Career Agility and Resilience in the Age of AI', 'https://www.linkedin.com/learning/building-career-agility-and-resilience-in-the-age-of-ai/prepare-for-your-ai-enhanced-career?u=104', 'LinkedIn', 'AI technologies skills to develop a "future-proof career mindset"'),
           ('Career Management Essentials', 'https://ibm.biz/BdGpZT', 'IBM', 'Career development, Career management, Communication skills, Generative AI tool use, Networking skills, Presentation skills, Professional interviewing skills, Personal online brand development, Resume writing, Social media presence, Workplace research'),
           ('Creating Compelling Reports', 'https://skillsforall.com/course/compelling-reports', 'Cisco', 'Communication, presentation'),
           ('Develop Your Prompt Engineering Skills', 'https://www.linkedin.com/learning/paths/develop-your-prompt-engineering-skills?u=104', 'LinkedIn', 'Prompt engineering'),
           ('Digital Literacy', 'https://ibm.biz/BdGhnB', 'IBM', 'AI, Collaboration, Computer literacy, Data analysis, Data presentation, Digital communications, Digital literacy, Employability skills, Internet security, Software engineering, Web navigation'),
           ('Digital Mindset', 'https://ibm.biz/BdGpYc', 'IBM', 'Adaptability and flexibility, Collaboration, Creativity, Data-driven decisions, Decision making, Digital mindset, Employability skills, Entrepreneurial mindset, Growth mindset, Innovation, Lifelong learning, Managing ambiguity and change, Professional networking, Teamwork'),
           ('Engaging Stakeholders for Success', 'https://skillsforall.com/course/engaging-stakeholders', 'Cisco', 'Communication, Stakeholder engagement, Change management'),
           ('Explore Emerging Tech', 'https://www.credly.com/org/ibm-skillsbuild/badge/explore-emerging-tech', 'IBM', 'Artificial intelligence, data, blockchain, cloud, cybersecurity, IoT'),
           ('Foundations of Project Management', 'https://www.coursera.org/learn/project-management-foundations', 'Google / Coursera', 'Project management'),
           ('Introduction to Artificial Intelligence', 'https://academy.aiskills.eu/course/1-introduction-to-artificial-intelligence', 'DIGITALEUROPE', 'Machine Learning, Deep Learning, Natural Language Processing, Computer Vision, Data Science Fundamentals, AI Ethics and Governance'),
           ('Introduction to Modern AI', 'https://skillsforall.com/course/introduction-to-modern-ai?courseLang=en-US', 'Cisco', 'AI literacy'),
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
-- Block 1.2: Link Foundational Trainings to "Testing and Quality Assurance" Job Group
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
                                              'https://www.linkedin.com/learning/paths/building-ai-literacy?u=26890602',
                                              'https://www.linkedin.com/learning/building-career-agility-and-resilience-in-the-age-of-ai/prepare-for-your-ai-enhanced-career?u=104',
                                              'https://ibm.biz/BdGpZT',
                                              'https://skillsforall.com/course/compelling-reports',
                                              'https://www.linkedin.com/learning/paths/develop-your-prompt-engineering-skills?u=104',
                                              'https://ibm.biz/BdGhnB',
                                              'https://ibm.biz/BdGpYc',
                                              'https://skillsforall.com/course/engaging-stakeholders',
                                              'https://www.credly.com/org/ibm-skillsbuild/badge/explore-emerging-tech',
                                              'https://www.coursera.org/learn/project-management-foundations',
                                              'https://academy.aiskills.eu/course/1-introduction-to-artificial-intelligence',
                                              'https://skillsforall.com/course/introduction-to-modern-ai?courseLang=en-US',
                                              'https://www.edx.org/learn/artificial-intelligence/ibm-introduction-to-prompt-engineering',
                                              'https://www.netacad.com/modules/introduction-to-responsible-ai-skills?courseLang=en-US',
                                              'https://www.linkedin.com/learning/paths/responsible-ai-foundations',
                                              'https://www.credly.com/org/ibm-skillsbuild/badge/working-in-a-digital-world-professional-skills'
    )
WHERE p.pathway_title = 'Testing and Quality Assurance';

COMMIT TRAN;

-------------------------------
-- Block 2.1: Job-Specific Trainings for "Quality Assurance Analyst"
-------------------------------
BEGIN TRAN;

MERGE [dbo].[Training] AS target
USING (VALUES
           ('AI and Developer Productivity', 'https://www.linkedin.com/learning/ai-and-developer-productivity/ai-and-developer-productivity?u=104', 'LinkedIn', 'Role of AI in development, prompts, code optimization, automated testing, quality assurance, intelligent debugging, issue resolution strategies, collaboration, documentation techniques, interview preparation'),
           ('AI Powered Programming with GitHub Copilot', 'https://www.linkedin.com/learning/ai-powered-programming-with-github-copilot-by-microsoft-press/welcome-and-course-overview?u=104', 'LinkedIn', 'Copilot basics, Copilot integration with IDE, code generation, testing, AI-assisted debugging and deployment'),
           ('Azure OpenAI: Generative AI Models and How to Use Them (1 hr, 7 languages)', 'https://www.linkedin.com/learning/azure-openai-generative-ai-models-and-how-to-use-them/welcome?u=104', 'LinkedIn', 'GPT, embedding, code, DALL-E models; how models work; combining models; copyright awareness'),
           ('ChatGPT Prompt Engineering for Developers', 'https://www.deeplearning.ai/short-courses/chatgpt-prompt-engineering-for-developers/', 'DeepLearning.AI', 'Prompt engineering, code review, software debugging'),
           ('Project Management Certificate', 'https://www.coursera.org/professional-certificates/google-project-management', 'Google / Coursera', 'Agile management, project planning and development, problem solving, project risk management, strategic thinking'),
           ('Securing the Use of Generative AI in Your Organization', 'https://www.linkedin.com/learning/securing-the-use-of-generative-ai-in-your-organization/introduction-to-generative-ai?u=104', 'LinkedIn', 'Generative AI security, risk mitigation, data privacy, cyber risks, compliance (GRC), LLM fundamentals, governance'),
           ('Software Testing and Automation Specialization', 'https://www.coursera.org/specializations/software-testing-automation', 'University of Minnesota / Coursera', 'Test automation, unit testing, static analysis, white-box testing, black-box testing')
) AS source(title, url, provider, skillsDeveloped)
ON target.url = source.url
WHEN NOT MATCHED THEN
    INSERT (id, title, url, provider, skillsDeveloped)
    VALUES (NEWID(), source.title, source.url, source.provider, source.skillsDeveloped);

COMMIT TRAN;

-------------------------------
-- Block 2.2: Link Trainings to "Quality Assurance Analyst" Job Role
-------------------------------
BEGIN TRAN;

INSERT INTO [dbo].[JobRoleTraining] (id, jobRoleId, trainingId)
SELECT NEWID(), jr.id, t.id
FROM [dbo].[JobRole] jr
         JOIN [dbo].[Training] t ON t.url IN (
                                              'https://www.linkedin.com/learning/ai-and-developer-productivity/ai-and-developer-productivity?u=104',
                                              'https://www.linkedin.com/learning/ai-powered-programming-with-github-copilot-by-microsoft-press/welcome-and-course-overview?u=104',
                                              'https://www.linkedin.com/learning/azure-openai-generative-ai-models-and-how-to-use-them/welcome?u=104',
                                              'https://www.deeplearning.ai/short-courses/chatgpt-prompt-engineering-for-developers/',
                                              'https://www.coursera.org/professional-certificates/google-project-management',
                                              'https://www.linkedin.com/learning/securing-the-use-of-generative-ai-in-your-organization/introduction-to-generative-ai?u=104',
                                              'https://www.coursera.org/specializations/software-testing-automation'
    )
WHERE jr.title = 'Quality Assurance Analyst'
  AND jr.pathwayId = (SELECT pathway_id FROM [dbo].[pathways] WHERE pathway_title = 'Testing and Quality Assurance');

COMMIT TRAN;

BEGIN TRAN;

MERGE [dbo].[Training] AS target
USING (VALUES
           ('AI and Developer Productivity', 'https://www.linkedin.com/learning/ai-and-developer-productivity/ai-and-developer-productivity?u=104', 'LinkedIn', 'Prompts, code optimization, testing, debugging, remote teamwork'),
           ('AI Powered Programming with GitHub Copilot', 'https://www.linkedin.com/learning/ai-powered-programming-with-github-copilot-by-microsoft-press/welcome-and-course-overview?u=104', 'LinkedIn', 'GitHub Copilot, IDE integration, unit testing, deployment'),
           ('AI Security Nuggets', 'https://www.netacad.com/modules/ai-security-nuggets?courseLang=en-US', 'Cisco', 'AI regulations, AI threat modeling, AI supply chain, RAG, LLM stack'),
           ('ChatGPT Prompt Engineering for Developers', 'https://www.deeplearning.ai/short-courses/chatgpt-prompt-engineering-for-developers/', 'DeepLearning.AI', 'Prompt Engineering, Code Review, Software Debug'),
           ('Machine Learning Specialization', 'https://www.coursera.org/specializations/machine-learning-introduction', 'Stanford / DeepLearning.AI', 'Logistic regression, Neural Networks, Decision Trees'),
           ('Securing the Use of Generative AI in Your Organization', 'https://www.linkedin.com/learning/securing-the-use-of-generative-ai-in-your-organization/introduction-to-generative-ai?u=104', 'LinkedIn', 'AI Security, GRC, Risk Mitigation, Compliance, Governance'),
           ('Software Testing and Automation Specialization', 'https://www.coursera.org/specializations/software-testing-automation', 'University of Minnesota / Coursera', 'Unit testing, automation, static analysis, white/black box testing')
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
                                              'https://www.linkedin.com/learning/ai-and-developer-productivity/ai-and-developer-productivity?u=104',
                                              'https://www.linkedin.com/learning/ai-powered-programming-with-github-copilot-by-microsoft-press/welcome-and-course-overview?u=104',
                                              'https://www.netacad.com/modules/ai-security-nuggets?courseLang=en-US',
                                              'https://www.deeplearning.ai/short-courses/chatgpt-prompt-engineering-for-developers/',
                                              'https://www.coursera.org/specializations/machine-learning-introduction',
                                              'https://www.linkedin.com/learning/securing-the-use-of-generative-ai-in-your-organization/introduction-to-generative-ai?u=104',
                                              'https://www.coursera.org/specializations/software-testing-automation'
    )
WHERE jr.title = 'Software Test and Debug'
  AND jr.pathwayId = (SELECT pathway_id FROM [dbo].[pathways] WHERE pathway_title = 'Testing and Quality Assurance');

COMMIT TRAN;

BEGIN TRAN;

MERGE [dbo].[Training] AS target
USING (VALUES
           ('AI and Developer Productivity', 'https://www.linkedin.com/learning/ai-and-developer-productivity/ai-and-developer-productivity?u=104', 'LinkedIn', 'Role of AI in development, using prompts, code optimization, automated testing, quality assurance, debugging, issue resolution, collaboration for remote teams, documentation techniques, interview preparation'),
           ('ChatGPT Prompt Engineering for Developers', 'https://www.deeplearning.ai/short-courses/chatgpt-prompt-engineering-for-developers/', 'DeepLearning.AI', 'Prompt engineering, code review, software debugging'),
           ('Microsoft Office Online Training Courses', 'https://www.linkedin.com/learning/topics/microsoft-office', 'LinkedIn', 'Microsoft Office'),
           ('Project Manager', 'https://skillsbuild.org/adult-learners/explore-learning/project-manager', 'IBM', 'Project management, project planning and development, problem solving, project risk management')
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
                                              'https://www.linkedin.com/learning/ai-and-developer-productivity/ai-and-developer-productivity?u=104',
                                              'https://www.deeplearning.ai/short-courses/chatgpt-prompt-engineering-for-developers/',
                                              'https://www.linkedin.com/learning/topics/microsoft-office',
                                              'https://skillsbuild.org/adult-learners/explore-learning/project-manager'
    )
WHERE jr.title = 'Technical Writer'
  AND jr.pathwayId = (SELECT pathway_id FROM [dbo].[pathways] WHERE pathway_title = 'Testing and Quality Assurance');

COMMIT TRAN;
