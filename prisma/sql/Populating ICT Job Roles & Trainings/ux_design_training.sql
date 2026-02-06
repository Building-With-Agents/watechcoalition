-------------------------------
-- Block 1.1: Add Foundational Trainings for "Design and User Experience"
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
           ('Building Career Agility and Resilience in the Age of AI', 'https://www.linkedin.com/learning/building-career-agility-and-resilience-in-the-age-of-ai/prepare-for-your-ai-enhanced-career?u=104', 'LinkedIn', 'AI technologies skills to develop a “future-proof career mindset”'),
           ('Career Management Essentials', 'https://ibm.biz/BdGpZT', 'IBM', 'Career development, Career management, Communication skills, Generative AI tool use, Networking skills, Presentation skills, Professional interviewing skills, Professional online brand development, Resume writing, Social media presence, Workplace research.'),
           ('Develop Your Prompt Engineering Skills', 'https://www.linkedin.com/learning/paths/develop-your-prompt-engineering-skills?u=104', 'LinkedIn', 'Prompt engineering'),
           ('Digital Literacy', 'https://ibm.biz/BdGhnB', 'IBM', 'AI, Collaboration, Computer literacy, Data analysis, Data presentation, Digital communications, Digital literacy, Employability skills, Internet security, Software engineering, Web navigation'),
           ('Digital Mindset', 'https://ibm.biz/BdGpYc', 'IBM', 'Adaptability and flexibility, Collaboration, Creativity, Data-driven decisions, Decision making, Digital mindset, Employability skills, Entrepreneurial mindset, Growth mindset, Innovation, Lifelong learning, Managing ambiguity and change, Professional networking, Teamwork'),
           ('Engaging Stakeholders for Success', 'https://skillsforall.com/course/engaging-stakeholders', 'Cisco', 'Communication, Stakeholder engagement, Change Management'),
           ('Enterprise Design Thinking Co-Creator', 'https://www.ibm.com/design/thinking/page/courses/Co-Creator/', 'IBM', 'Design Thinking, creativity, innovation'),
           ('Enterprise Design Thinking Practitioner', 'https://www.ibm.com/design/thinking/page/courses/Practitioner', 'IBM', 'Design Thinking, creativity, innovation'),
           ('Explore Emerging Tech', 'https://www.credly.com/org/ibm-skillsbuild/badge/explore-emerging-tech', 'IBM', 'Artificial intelligence, data, blockchain, cloud, cybersecurity, IoT'),
           ('Introduction to Artificial Intelligence', 'https://academy.aiskills.eu/course/1-introduction-to-artificial-intelligence', 'DIGITALEUROPE', 'Machine Learning, Deep Learning, Natural Language Processing, Computer Vision, Data Science Fundamentals, AI Ethics and Governance'),
           ('Introduction to Data Analytics', 'https://www.coursera.org/learn/introduction-to-data-analytics', 'IBM / Coursera', 'Data analysis, data visualization, Microsoft Excel'),
           ('Introduction to Modern AI', 'https://skillsforall.com/course/introduction-to-modern-ai?courseLang=en-US', 'Cisco', 'AI literacy'),
           ('Introduction to Prompt Engineering', 'https://www.edx.org/learn/artificial-intelligence/ibm-introduction-to-prompt-engineering', 'IBM / EDX', 'Prompt engineering'),
           ('Introduction to Responsible AI Skills', 'https://www.netacad.com/modules/introduction-to-responsible-ai-skills?courseLang=en-US', 'Cisco / Intel', 'Ethical and Responsible AI, AI ethics and governance'),
           ('Responsible AI Foundations', 'https://www.linkedin.com/learning/paths/responsible-ai-foundations', 'LinkedIn', 'Ethical and Responsible AI, AI ethics and governance'),
           ('Working in a Digital World: Professional Skills', 'https://www.credly.com/org/ibm-skillsbuild/badge/working-in-a-digital-world-professional-skills', 'IBM', 'Agile methodologies, business acumen, creative thinking, critical thinking, communication, problem solving, solutioning')
) AS source (title, url, provider, skillsDeveloped)
ON target.url = source.url
WHEN NOT MATCHED THEN
    INSERT (id, title, url, provider, skillsDeveloped)
    VALUES (NEWID(), source.title, source.url, source.provider, source.skillsDeveloped);

COMMIT TRAN;

-------------------------------
-- Block 1.2: Link Trainings to "Design and User Experience" Job Group
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
                                              'https://www.linkedin.com/learning/paths/develop-your-prompt-engineering-skills?u=104',
                                              'https://ibm.biz/BdGhnB',
                                              'https://ibm.biz/BdGpYc',
                                              'https://skillsforall.com/course/engaging-stakeholders',
                                              'https://www.ibm.com/design/thinking/page/courses/Co-Creator/',
                                              'https://www.ibm.com/design/thinking/page/courses/Practitioner',
                                              'https://www.credly.com/org/ibm-skillsbuild/badge/explore-emerging-tech',
                                              'https://academy.aiskills.eu/course/1-introduction-to-artificial-intelligence',
                                              'https://www.coursera.org/learn/introduction-to-data-analytics',
                                              'https://skillsforall.com/course/introduction-to-modern-ai?courseLang=en-US',
                                              'https://www.edx.org/learn/artificial-intelligence/ibm-introduction-to-prompt-engineering',
                                              'https://www.netacad.com/modules/introduction-to-responsible-ai-skills?courseLang=en-US',
                                              'https://www.linkedin.com/learning/paths/responsible-ai-foundations',
                                              'https://www.credly.com/org/ibm-skillsbuild/badge/working-in-a-digital-world-professional-skills'
    )
WHERE p.pathway_title = 'Design and User Experience';

COMMIT TRAN;

-------------------------------
-- Block 2.1: Job-Specific Trainings for "Design Engineer"
-------------------------------
BEGIN TRAN;

MERGE [dbo].[Training] AS target
USING (VALUES
           ('AI and Machine Learning Tools for After Effects (FEE)', 'https://www.linkedin.com/learning/ai-and-machine-learning-tools-for-after-effects', 'LinkedIn', 'Adobe After Effects enhancements, image generation, footage editing, color correction, motion graphics with AI, creative workflows using AI'),
           ('AI Powered Programming with GitHub Copilot (FEE)', 'https://www.linkedin.com/learning/ai-powered-programming-with-github-copilot-by-microsoft-press/welcome-and-course-overview?u=104', 'LinkedIn', 'GitHub Copilot, AI code suggestions, commit-based generation, Copilot in IDEs, Copilot for unit testing and deployment, Copilot plugins'),
           ('Applying Generative AI as a Creative Professional', 'https://www.linkedin.com/learning/paths/applying-generative-ai-as-a-creative-professional?u=104', 'LinkedIn', 'Generative AI in design, streamlining creative workflows, brainstorming with AI, content generation, creative ethics of AI'),
           ('Azure AI Engineering: Speech, Language, and Vision Solutions', 'https://www.linkedin.com/learning/azure-ai-engineering-speech-language-and-vision-solutions/introduction?u=104', 'LinkedIn', 'Azure AI services, Microsoft Cognitive Services, speech recognition, NLP, computer vision, text-to-speech, classification models, real-time transcription and translation, image tagging, video detection and analysis'),
           ('Generative Design Foundations', 'https://www.linkedin.com/learning/generative-design-foundations', 'LinkedIn', 'Generative design in architecture and manufacturing, simulation and analysis workflows, geometry generation, topology optimization, AI-assisted CAD processes')
) AS source (title, url, provider, skillsDeveloped)
ON target.url = source.url
WHEN NOT MATCHED THEN
    INSERT (id, title, url, provider, skillsDeveloped)
    VALUES (NEWID(), source.title, source.url, source.provider, source.skillsDeveloped);

COMMIT TRAN;

-------------------------------
-- Block 2.2: Link Trainings to "Design Engineer" Job Role
-------------------------------
BEGIN TRAN;

INSERT INTO [dbo].[JobRoleTraining] (id, jobRoleId, trainingId)
SELECT NEWID(), jr.id, t.id
FROM [dbo].[JobRole] jr
         JOIN [dbo].[Training] t ON t.url IN (
                                              'https://www.linkedin.com/learning/ai-and-machine-learning-tools-for-after-effects',
                                              'https://www.linkedin.com/learning/ai-powered-programming-with-github-copilot-by-microsoft-press/welcome-and-course-overview?u=104',
                                              'https://www.linkedin.com/learning/paths/applying-generative-ai-as-a-creative-professional?u=104',
                                              'https://www.linkedin.com/learning/azure-ai-engineering-speech-language-and-vision-solutions/introduction?u=104',
                                              'https://www.linkedin.com/learning/generative-design-foundations'
    )
WHERE jr.title = 'Design Engineer'
  AND jr.pathwayId = (SELECT pathway_id FROM [dbo].[pathways] WHERE pathway_title = 'Design and User Experience');

COMMIT TRAN;

-------------------------------
-- Block 3.1: Job-Specific Trainings for "Product Design Engineer"
-------------------------------
BEGIN TRAN;

MERGE [dbo].[Training] AS target
USING (VALUES
           ('AI and Machine Learning Tools for After Effects (FEE)', 'https://www.linkedin.com/learning/ai-and-machine-learning-tools-for-after-effects', 'LinkedIn', 'Adobe After Effects enhancements, image generation, footage editing, color correction, motion graphics with AI, creative workflows using AI'),
           ('AI Powered Programming with GitHub Copilot (FEE)', 'https://www.linkedin.com/learning/ai-powered-programming-with-github-copilot-by-microsoft-press/welcome-and-course-overview?u=104', 'LinkedIn', 'GitHub Copilot, AI code suggestions, commit-based generation, Copilot in IDEs, Copilot for unit testing and deployment, Copilot plugins'),
           ('Applying Generative AI as a Creative Professional', 'https://www.linkedin.com/learning/paths/applying-generative-ai-as-a-creative-professional?u=104', 'LinkedIn', 'Generative AI in design, streamlining creative workflows, brainstorming with AI, content generation, creative ethics of AI'),
           ('Azure AI Engineering: Speech, Language, and Vision Solutions', 'https://www.linkedin.com/learning/azure-ai-engineering-speech-language-and-vision-solutions/introduction?u=104', 'LinkedIn', 'Azure AI services, Microsoft Cognitive Services, speech recognition, NLP, computer vision, text-to-speech, classification models, real-time transcription and translation, image tagging, video detection and analysis'),
           ('Generative Design Foundations', 'https://www.linkedin.com/learning/generative-design-foundations', 'LinkedIn', 'Generative design in architecture and manufacturing, simulation and analysis workflows, geometry generation, topology optimization, AI-assisted CAD processes')
) AS source (title, url, provider, skillsDeveloped)
ON target.url = source.url
WHEN NOT MATCHED THEN
    INSERT (id, title, url, provider, skillsDeveloped)
    VALUES (NEWID(), source.title, source.url, source.provider, source.skillsDeveloped);

COMMIT TRAN;

-------------------------------
-- Block 3.2: Link Trainings to "Product Design Engineer" Job Role
-------------------------------
BEGIN TRAN;

INSERT INTO [dbo].[JobRoleTraining] (id, jobRoleId, trainingId)
SELECT NEWID(), jr.id, t.id
FROM [dbo].[JobRole] jr
         JOIN [dbo].[Training] t ON t.url IN (
                                              'https://www.linkedin.com/learning/ai-and-machine-learning-tools-for-after-effects',
                                              'https://www.linkedin.com/learning/ai-powered-programming-with-github-copilot-by-microsoft-press/welcome-and-course-overview?u=104',
                                              'https://www.linkedin.com/learning/paths/applying-generative-ai-as-a-creative-professional?u=104',
                                              'https://www.linkedin.com/learning/azure-ai-engineering-speech-language-and-vision-solutions/introduction?u=104',
                                              'https://www.linkedin.com/learning/generative-design-foundations'
    )
WHERE jr.title = 'Product Design Engineer'
  AND jr.pathwayId = (SELECT pathway_id FROM [dbo].[pathways] WHERE pathway_title = 'Design and User Experience');

COMMIT TRAN;

-------------------------------
-- Block 4.1: Job-Specific Trainings for "UX Designer"
-------------------------------
BEGIN TRAN;

MERGE [dbo].[Training] AS target
USING (VALUES
           ('User Experience Design', 'https://skillsbuild.org/adult-learners/explore-learning/user-experience-design', 'IBM', 'UX Design'),
           ('UX Design Certificate', 'https://www.coursera.org/professional-certificates/google-ux-design', 'Google / Coursera', 'User Experience (UX), Prototype, Wireframe, User Experience Design (UXD), UX Research, mockup, Figma, Usability Testing, UX design jobs'),
           ('Applying Generative AI as a Creative Professional', 'https://www.linkedin.com/learning/paths/applying-generative-ai-as-a-creative-professional?u=104', 'LinkedIn', 'Generative AI, creative workflows, streamlining ideation, AI-enhanced design output, brainstorming with AI, ethical use of AI in design'),
           ('AI and Machine Learning Tools for After Effects', 'https://www.linkedin.com/learning/ai-and-machine-learning-tools-for-after-effects', 'LinkedIn', 'Adobe After Effects, AI for creative media production, image generation, motion graphics enhancement, plugin use, automation of tedious tasks'),
           ('Generative Design Foundations', 'https://www.linkedin.com/learning/generative-design-foundations', 'LinkedIn', 'Generative design in UX and product development, parametric workflows, design simulation and evaluation, AI-assisted design exploration and decision-making')
) AS source (title, url, provider, skillsDeveloped)
ON target.url = source.url
WHEN NOT MATCHED THEN
    INSERT (id, title, url, provider, skillsDeveloped)
    VALUES (NEWID(), source.title, source.url, source.provider, source.skillsDeveloped);

COMMIT TRAN;

-------------------------------
-- Block 4.2: Link Trainings to "UX Designer" Job Role
-------------------------------
BEGIN TRAN;

INSERT INTO [dbo].[JobRoleTraining] (id, jobRoleId, trainingId)
SELECT NEWID(), jr.id, t.id
FROM [dbo].[JobRole] jr
         JOIN [dbo].[Training] t ON t.url IN (
                                              'https://skillsbuild.org/adult-learners/explore-learning/user-experience-design',
                                              'https://www.coursera.org/professional-certificates/google-ux-design',
                                              'https://www.linkedin.com/learning/paths/applying-generative-ai-as-a-creative-professional?u=104',
                                              'https://www.linkedin.com/learning/ai-and-machine-learning-tools-for-after-effects',
                                              'https://www.linkedin.com/learning/generative-design-foundations'
    )
WHERE jr.title = 'UX Designer'
  AND jr.pathwayId = (SELECT pathway_id FROM [dbo].[pathways] WHERE pathway_title = 'Design and User Experience');

COMMIT TRAN;
