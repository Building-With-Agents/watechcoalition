-------------------------------
-- Block 1.1: Software Developer Foundational Training Records (With URLs)
-------------------------------
BEGIN TRAN;

MERGE [dbo].[Training] AS target
USING (VALUES
           ('Agile Explorer', 'https://ibm.biz/BdGpZ8', 'IBM', 'Agile thinking, Agile methodologies'),
           ('AI Canon', 'https://a16z.com/ai-canon/', 'AI Canon', 'AI literacy'),
           ('AI Ecosystem overview', 'https://academy.aiskills.eu/course/2-ai-ecosystem-overview', 'DIGITALEUROPE', 'AI ecosystem analysis, Understanding AI infrastructure, AI governance and regulation knowledge, Evaluating AI tools and platforms, Ethical AI decision-making'),
           ('AI Essentials Course', 'https://grow.google/ai-essentials/', 'Google', 'AI literacy'),
           ('AI Ethics', 'https://ibm.biz/BdGpZA', 'IBM', 'Ethical and Responsible AI, AI ethics and governance'),
           ('AI for Everyone by Andrew Ng', 'https://www.coursera.org/learn/ai-for-everyone', 'Coursera', 'AI literacy'),
           ('AI Fundamentals', 'https://ibm.biz/BdGpZ9', 'IBM', 'AI Fundamentals'),
           ('Building AI Literacy', 'https://www.linkedin.com/learning/paths/building-ai-literacy?u=26890602', 'LinkedIn', 'AI literacy'),
           ('Building Career Agility and Resilience in the Age of AI', 'https://www.linkedin.com/learning/building-career-agility-and-resilience-in-the-age-of-ai/prepare-for-your-ai-enhanced-career?u=104', 'LinkedIn', 'AI technologies skills to develop a "future-proof career mindset"'),
           ('Career Management Essentials', 'https://ibm.biz/BdGpZT', 'IBM', 'Career development, Career management, Communication skills, Generative AI tool use, Networking skills, Presentation skills, Professional interviewing skills, Professional online brand development, Resume writing, Socialmedia presence, Workplace research'),
           ('Develop Your Prompt Engineering Skills', 'https://www.linkedin.com/learning/paths/develop-your-prompt-engineering-skills?u=104', 'LinkedIn', 'Prompt engineering'),
           ('Digital Literacy', 'https://ibm.biz/BdGhnB', 'IBM', 'AI, Collaboration, Computer literacy, Data analysis, Data presentation, Digital communications, Digital literacy, Employability skills, Internet security, Software engineering, Web navigation'),
           ('Digital Mindset', 'https://ibm.biz/BdGpYc', 'IBM', 'Adaptability and flexibility, Collaboration, Creativity, Data-driven decisions, Decision making, Digital mindset, Employability skills, Entrepreneurial mindset, Growth mindset, Innovation, Lifelong learning, Managing ambiguity and change, Professional networking, Teamwork'),
           ('Engaging Stakeholders for Success', 'https://skillsforall.com/course/engaging-stakeholders', 'Cisco', 'Communication, Stakeholder engagement, Change Management'),
           ('Enterprise Design Thinking Co-Creator', 'https://www.ibm.com/design/thinking/page/courses/Co-Creator/', 'IBM', 'Design Thinking, creativity, innovation'),
           ('Enterprise Design Thinking Practitioner', 'https://www.ibm.com/design/thinking/page/courses/Practitioner', 'IBM', 'Design Thinking, creativity, innovation'),
           ('Explore Emerging Tech', 'https://www.credly.com/org/ibm-skillsbuild/badge/explore-emerging-tech', 'IBM', 'Artificial intelligence, data, blockchain, cloud, cybersecurity, iot'),
           ('Foundations of Project Management', 'https://www.coursera.org/learn/project-management-foundations', 'Google / Coursera', 'Project management'),
           ('Introduction to Artificial Intelligence', 'https://academy.aiskills.eu/course/1-introduction-to-artificial-intelligence', 'DIGITALEUROPE', 'Machine Learning, Deep Learning, Natural Language Processing, Computer Vision, Data Science Fundamentals, AI Ethics and Governance'),
           ('Introduction to modern AI', 'https://skillsforall.com/course/introduction-to-modern-ai?courseLang=en-US', 'Cisco', 'AI literacy'),
           ('Introduction to Prompt Engineering', 'https://www.edx.org/learn/artificial-intelligence/ibm-introduction-to-prompt-engineering', 'IBM / EDX', 'Prompt engineering'),
           ('Introduction to Responsible AI Skills', 'https://www.netacad.com/modules/introduction-to-responsible-ai-skills?courseLang=en-US', 'Cisco / Intel', 'Ethical and Responsible AI, AI ethics and governance'),
           ('Responsible AI Foundations', 'https://www.linkedin.com/learning/paths/responsible-ai-foundations', 'LinkedIn', 'Ethical and Responsible AI, AI ethics and governance'),
           ('Software Development Training Courses', 'https://www.linkedin.com/learning/topics/software-development', 'LinkedIn', 'Object-Oriented Programming, Programming Foundations, Programming Languages, Software Design, Software Design Patterns, Software Development Tools, System architecture, Software Testing, Version Control'),
           ('Working in a Digital World: Professional Skills', 'https://www.credly.com/org/ibm-skillsbuild/badge/working-in-a-digital-world-professional-skills', 'IBM', 'Agile methodologies, business acumen, creative thinking, critical thinking, communication, problem solving, solutioning')
) AS source(title, url, provider, skillsDeveloped)
ON target.url = source.url
WHEN NOT MATCHED THEN
    INSERT (id, title, url, provider, skillsDeveloped)
    VALUES (NEWID(), source.title, source.url, source.provider, source.skillsDeveloped);

COMMIT TRAN;

-------------------------------
-- Block 1.2: Link Foundational Trainings to the "Software Development" Job Group
-------------------------------
BEGIN TRAN;

INSERT INTO [dbo].[PathwayTraining] (id, pathwayId, trainingId)
SELECT NEWID(), p.pathway_id, t.id
FROM [dbo].[pathways] p
         JOIN [dbo].[Training] t ON t.url IN (
                                              'https://ibm.biz/BdGpZ8',
                                              'https://a16z.com/ai-canon/',
                                              'https://academy.aiskills.eu/course/2-ai-ecosystem-overview',
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
                                              'https://www.coursera.org/learn/project-management-foundations',
                                              'https://academy.aiskills.eu/course/1-introduction-to-artificial-intelligence',
                                              'https://skillsforall.com/course/introduction-to-modern-ai?courseLang=en-US',
                                              'https://www.edx.org/learn/artificial-intelligence/ibm-introduction-to-prompt-engineering',
                                              'https://www.netacad.com/modules/introduction-to-responsible-ai-skills?courseLang=en-US',
                                              'https://www.linkedin.com/learning/paths/responsible-ai-foundations',
                                              'https://www.linkedin.com/learning/topics/software-development',
                                              'https://www.credly.com/org/ibm-skillsbuild/badge/working-in-a-digital-world-professional-skills'
    )
WHERE p.pathway_title = 'Software Development';

COMMIT TRAN;

-------------------------------
-- Block 2.1: Job-Specific Trainings for "Application Developer"
-------------------------------
BEGIN TRAN;

MERGE [dbo].[Training] AS target
USING (VALUES
           ('Azure OpenAI: Generative AI Models and How to Use Them', 'https://www.linkedin.com/learning/azure-openai-generative-ai-models-and-how-to-use-them/welcome?u=104', 'LinkedIn', 'Azure OpenAI models, GPT models, embedding models, DALL-E models, combining models, copyright, solution building'),
           ('Building Generative AI Skills for Developers', 'https://www.linkedin.com/learning/paths/building-generative-ai-skills-for-developers?u=104', 'LinkedIn', 'AI tools and frameworks for development, building and releasing apps with AI'),
           ('Machine Learning with Python Foundations', 'https://www.linkedin.com/learning/machine-learning-with-python-foundations/machine-learning-in-our-world-23459526?u=104', 'LinkedIn', 'Python ML, data prep, guided examples, evaluation & interpretation'),
           ('Training Neural Networks in Python', 'https://www.linkedin.com/learning/training-neural-networks-in-python-17058600/creating-a-neural-network-in-python?u=104', 'LinkedIn', 'Neural network internals, algorithms, biological relations, training methods, evaluation')
) AS source(title, url, provider, skillsDeveloped)
ON target.url = source.url
WHEN NOT MATCHED THEN
    INSERT (id, title, url, provider, skillsDeveloped)
    VALUES (NEWID(), source.title, source.url, source.provider, source.skillsDeveloped);

COMMIT TRAN;

-------------------------------
-- Block 2.2: Link Trainings to "Application Developer" Job Role
-------------------------------
BEGIN TRAN;

INSERT INTO [dbo].[JobRoleTraining] (id, jobRoleId, trainingId)
SELECT NEWID(), jr.id, t.id
FROM [dbo].[JobRole] jr
         JOIN [dbo].[Training] t ON t.url IN (
                                              'https://www.linkedin.com/learning/azure-openai-generative-ai-models-and-how-to-use-them/welcome?u=104',
                                              'https://www.linkedin.com/learning/paths/building-generative-ai-skills-for-developers?u=104',
                                              'https://www.linkedin.com/learning/machine-learning-with-python-foundations/machine-learning-in-our-world-23459526?u=104',
                                              'https://www.linkedin.com/learning/training-neural-networks-in-python-17058600/creating-a-neural-network-in-python?u=104'
    )
WHERE jr.title = 'Application Developer'
  AND jr.pathwayId = (SELECT pathway_id FROM [dbo].[pathways] WHERE pathway_title = 'Software Development');

COMMIT TRAN;


-------------------------------
-- Block 3.1: Job-Specific Trainings for "AI/ML Engineer"
-------------------------------
BEGIN TRAN;

MERGE [dbo].[Training] AS target
USING (VALUES
           ('Google LLMOps', 'https://www.deeplearning.ai/short-courses/llmops/', 'Google / DeepLearning.AI', 'Operations, Version Control, Data Pipelines, Big Data'),
           ('IBM AI Engineering Professional Certificate', 'https://www.coursera.org/professional-certificates/ai-engineer', 'IBM / Coursera', 'Machine Learning, Artificial Intelligence, Algorithm, Python, Data Science, Data Visualization, Big Data'),
           ('IBM Python for Applied Data Science and AI', 'https://www.coursera.org/learn/python-for-applied-data-science-ai/', 'IBM / Coursera', 'Python, Data Analysis, Data Science, Numpy, Pandas'),
           ('Machine Learning Specialization', 'https://www.coursera.org/specializations/machine-learning-introduction', 'Stanford / DeepLearning.AI', 'Machine Learning, Artificial Intelligence')
) AS source(title, url, provider, skillsDeveloped)
ON target.url = source.url
WHEN NOT MATCHED THEN
    INSERT (id, title, url, provider, skillsDeveloped)
    VALUES (NEWID(), source.title, source.url, source.provider, source.skillsDeveloped);

COMMIT TRAN;

-------------------------------
-- Block 3.2: Link Job-Specific Trainings to the "AI/ML Engineer" Job Role
-------------------------------
BEGIN TRAN;

INSERT INTO [dbo].[JobRoleTraining] (id, jobRoleId, trainingId)
SELECT NEWID(), jr.id, t.id
FROM [dbo].[JobRole] jr
         JOIN [dbo].[Training] t ON t.url IN (
                                              'https://www.deeplearning.ai/short-courses/llmops/',
                                              'https://www.coursera.org/professional-certificates/ai-engineer',
                                              'https://www.coursera.org/learn/python-for-applied-data-science-ai/',
                                              'https://www.coursera.org/specializations/machine-learning-introduction'
    )
WHERE jr.title = 'AI/ML Engineer'
        AND jr.pathwayId = (SELECT pathway_id FROM [dbo].[pathways] WHERE pathway_title= 'Software Development');

COMMIT TRAN;


-------------------------------
-- Block 4.1: Job-Specific Trainings for "Back-End Developer" (Corrected)
-------------------------------
BEGIN TRAN;

MERGE [dbo].[Training] AS target
USING (VALUES
           ('Building Generative AI Skills for Developers', 'https://www.linkedin.com/learning/paths/building-generative-ai-skills-for-developers?u=104', 'LinkedIn', 'AI tools and frameworks for back-end use, faster and easier development with AI'),
           ('IBM Back-End Development Professional Certificate', 'https://www.coursera.org/professional-certificates/ibm-backend-development', 'IBM / Coursera', 'Django, MongoDB, Docker, Flask, REST, ORM, RDBMS, SQL, Back-End Applications, Observability'),
           ('Machine Learning with Python Foundations', 'https://www.linkedin.com/learning/machine-learning-with-python-foundations/machine-learning-in-our-world-23459526?u=104', 'LinkedIn', 'Python, ML fundamentals, data prep, model building, interpretation'),
           ('SQL Server Machine Learning Services with Python', 'https://www.linkedin.com/learning/sql-server-machine-learning-services-python/analyze-sql-server-data-with-python?u=104', 'LinkedIn', 'Python, SQL Server ML, analysis, plotting, standalone script deployment'),
           ('Training Neural Networks in Python', 'https://www.linkedin.com/learning/training-neural-networks-in-python-17058600/creating-a-neural-network-in-python?u=104', 'LinkedIn', 'Python, neural networks, training methods, architecture selection')
) AS source(title, url, provider, skillsDeveloped)
ON target.url = source.url
WHEN NOT MATCHED THEN
    INSERT (id, title, url, provider, skillsDeveloped)
    VALUES (NEWID(), source.title, source.url, source.provider, source.skillsDeveloped);

COMMIT TRAN;

-------------------------------
-- Block 4.2: Link Trainings to "Back-End Developer" Job Role (Corrected)
-------------------------------
BEGIN TRAN;

INSERT INTO [dbo].[JobRoleTraining] (id, jobRoleId, trainingId)
SELECT NEWID(), jr.id, t.id
FROM [dbo].[JobRole] jr
         JOIN [dbo].[Training] t ON t.url IN (
                                              'https://www.linkedin.com/learning/paths/building-generative-ai-skills-for-developers?u=104',
                                              'https://www.coursera.org/professional-certificates/ibm-backend-development',
                                              'https://www.linkedin.com/learning/machine-learning-with-python-foundations/machine-learning-in-our-world-23459526?u=104',
                                              'https://www.linkedin.com/learning/sql-server-machine-learning-services-python/analyze-sql-server-data-with-python?u=104',
                                              'https://www.linkedin.com/learning/training-neural-networks-in-python-17058600/creating-a-neural-network-in-python?u=104'
    )
WHERE jr.title = 'Back-End Developer'
  AND jr.pathwayId = (SELECT pathway_id FROM [dbo].[pathways] WHERE pathway_title = 'Software Development');

COMMIT TRAN;


-------------------------------
-- Block 5.1: Job-Specific Trainings for "Cloud Engineer"
-------------------------------
BEGIN TRAN;

MERGE [dbo].[Training] AS target
USING (VALUES
           ('AI Powered Programming with GitHub CoPilot', 'https://www.linkedin.com/learning/ai-powered-programming-with-github-copilot-by-microsoft-press/welcome-and-course-overview?u=104', 'LinkedIn', 'Copilot integration, comment-based generation, testing, deployment, productivity'),
           ('Google Cloud Platform for Machine Learning', 'https://www.linkedin.com/learning/google-cloud-platform-for-machine-learning-essential-training-2024-revision/welcome?u=104', 'LinkedIn', 'Google Vertex AI, ML development, hosting, evaluation, generative models, MLOps'),
           ('Prepare for the AWS Certified Machine Learning - Specialty (MLS-C01) Exam', 'https://www.linkedin.com/learning/paths/prepare-for-the-aws-certified-machine-learning-specialty-mls-c01-exam?u=104', 'LinkedIn', 'AWS certification prep, ML training, model deployment, cloud specialization'),
           ('Prepare for the Google Cloud Professional Machine Learning Engineer Certification', 'https://www.linkedin.com/learning/paths/prepare-for-the-google-cloud-professional-machine-learning-engineer-certification?u=104', 'LinkedIn', 'ML model deployment on Google Cloud, business problem solving, certification prep'),
           ('Securing the Use of Generative AI in Your Organization', 'https://www.linkedin.com/learning/securing-the-use-of-generative-ai-in-your-organization/introduction-to-generative-ai?u=104', 'LinkedIn', 'GRC, risk management, LLM cybersecurity, policy, AI security strategy')
) AS source(title, url, provider, skillsDeveloped)
ON target.url = source.url
WHEN NOT MATCHED THEN
    INSERT (id, title, url, provider, skillsDeveloped)
    VALUES (NEWID(), source.title, source.url, source.provider, source.skillsDeveloped);

COMMIT TRAN;

-------------------------------
-- Block 5.2: Link Job-Specific Trainings to the "Cloud Engineer" Job Role
-------------------------------
BEGIN TRAN;

INSERT INTO [dbo].[JobRoleTraining] (id, jobRoleId, trainingId)
SELECT NEWID(), jr.id, t.id
FROM [dbo].[JobRole] jr
         JOIN [dbo].[Training] t ON t.url IN (
                                              'https://www.linkedin.com/learning/ai-powered-programming-with-github-copilot-by-microsoft-press/welcome-and-course-overview?u=104',
                                              'https://www.linkedin.com/learning/google-cloud-platform-for-machine-learning-essential-training-2024-revision/welcome?u=104',
                                              'https://www.linkedin.com/learning/paths/prepare-for-the-aws-certified-machine-learning-specialty-mls-c01-exam?u=104',
                                              'https://www.linkedin.com/learning/paths/prepare-for-the-google-cloud-professional-machine-learning-engineer-certification?u=104',
                                              'https://www.linkedin.com/learning/securing-the-use-of-generative-ai-in-your-organization/introduction-to-generative-ai?u=104'
    )
WHERE jr.title = 'Cloud Engineer'
  AND jr.pathwayId = (SELECT pathway_id FROM [dbo].[pathways] WHERE pathway_title= 'Software Development');

COMMIT TRAN;

-------------------------------
-- Block 6.1: Job-Specific Trainings for "Front-End Developer"
-------------------------------
BEGIN TRAN;

MERGE [dbo].[Training] AS target
USING (VALUES
           ('AI Powered Programming with GitHub CoPilot', 'https://www.linkedin.com/learning/ai-powered-programming-with-github-copilot-by-microsoft-press/welcome-and-course-overview?u=104', 'LinkedIn', 'Copilot integration, testing, deployment, code generation, unit testing, productivity'),
           ('Azure OpenAI: Generative AI Models and How to Use Them', 'https://www.linkedin.com/learning/azure-openai-generative-ai-models-and-how-to-use-them/welcome?u=104', 'LinkedIn', 'GPT/DALL-E models, embedding, combining models, copyright issues'),
           ('Build a JavaScript AI App with React and the OpenAI API', 'https://www.linkedin.com/learning/build-a-javascript-ai-app-with-react-and-the-openai-api/build-a-javascript-ai-app-with-react-and-the-openai-api?u=104', 'LinkedIn', 'React integration, OpenAI API usage, authentication, tokens, prompt engineering'),
           ('Building Generative AI Skills for Developers (13 hrs. 7 languages)', 'https://www.linkedin.com/learning/paths/building-generative-ai-skills-for-developers?u=104', 'LinkedIn', 'Generative AI tools and frameworks, developer productivity, AI-assisted software engineering'),
           ('IBM Front-End Developer Professional Certificate', 'https://www.coursera.org/professional-certificates/ibm-frontend-developer', 'IBM / Coursera', 'Continuous Integration, Continuous Delivery, Mongodb, agile, Devops, Software Development, React (Web Framework), Front-end Development, Front-end design, Web Development, JavaScript, Web')
) AS source(title, url, provider, skillsDeveloped)
ON target.url = source.url
WHEN NOT MATCHED THEN
    INSERT (id, title, url, provider, skillsDeveloped)
    VALUES (NEWID(), source.title, source.url, source.provider, source.skillsDeveloped);

COMMIT TRAN;

-------------------------------
-- Block 6.2: Link Trainings to "Front-End Developer" Job Role
-------------------------------
BEGIN TRAN;

INSERT INTO [dbo].[JobRoleTraining] (id, jobRoleId, trainingId)
SELECT NEWID(), jr.id, t.id
FROM [dbo].[JobRole] jr
         JOIN [dbo].[Training] t ON t.url IN (
                                              'https://www.linkedin.com/learning/ai-powered-programming-with-github-copilot-by-microsoft-press/welcome-and-course-overview?u=104',
                                              'https://www.linkedin.com/learning/azure-openai-generative-ai-models-and-how-to-use-them/welcome?u=104',
                                              'https://www.linkedin.com/learning/build-a-javascript-ai-app-with-react-and-the-openai-api/build-a-javascript-ai-app-with-react-and-the-openai-api?u=104',
                                              'https://www.linkedin.com/learning/paths/building-generative-ai-skills-for-developers?u=104',
                                              'https://www.coursera.org/professional-certificates/ibm-frontend-developer'
    )
WHERE jr.title = 'Front-End Developer'
  AND jr.pathwayId = (SELECT pathway_id FROM [dbo].[pathways] WHERE pathway_title= 'Software Development');


COMMIT TRAN;

-------------------------------
-- Block 7.1: Job-Specific Trainings for "Full-Stack Developer"
-------------------------------
BEGIN TRAN;

MERGE [dbo].[Training] AS target
USING (VALUES
           ('Azure OpenAI: Generative AI Models and How to Use Them', 'https://www.linkedin.com/learning/azure-openai-generative-ai-models-and-how-to-use-them/welcome?u=104', 'LinkedIn', 'GPT models, DALL-E, AI model usage, copyright, building solutions'),
           ('Building Generative AI Skills for Developers', 'https://www.linkedin.com/learning/paths/building-generative-ai-skills-for-developers?u=104', 'LinkedIn', 'Generative AI tools and frameworks for full-stack productivity'),
           ('Machine Learning with Python Foundations', 'https://www.linkedin.com/learning/machine-learning-with-python-foundations', 'LinkedIn', 'Machine learning intro, guided ML process, practical ML with Python'),
           ('SQL Server Machine Learning Services with Python', 'https://www.linkedin.com/learning/sql-server-machine-learning-services-python/analyze-sql-server-data-with-python?u=104', 'LinkedIn', 'SQL + Python for ML, charts, data prep, scripting in ML pipelines'),
           ('Training Neural Networks in Python', 'https://www.linkedin.com/learning/training-neural-networks-in-python-17058600/creating-a-neural-network-in-python?u=104', 'LinkedIn', 'Build & train networks, model selection, Python for neural networks')
) AS source(title, url, provider, skillsDeveloped)
ON target.url = source.url
WHEN NOT MATCHED THEN
    INSERT (id, title, url, provider, skillsDeveloped)
    VALUES (NEWID(), source.title, source.url, source.provider, source.skillsDeveloped);

COMMIT TRAN;

-------------------------------
-- Block 7.2: Link Trainings to "Full-Stack Developer" Job Role
-------------------------------
BEGIN TRAN;

INSERT INTO [dbo].[JobRoleTraining] (id, jobRoleId, trainingId)
SELECT NEWID(), jr.id, t.id
FROM [dbo].[JobRole] jr
         JOIN [dbo].[Training] t ON t.url IN (
                                              'https://www.linkedin.com/learning/azure-openai-generative-ai-models-and-how-to-use-them/welcome?u=104',
                                              'https://www.linkedin.com/learning/paths/building-generative-ai-skills-for-developers?u=104',
                                              'https://www.linkedin.com/learning/machine-learning-with-python-foundations',
                                              'https://www.linkedin.com/learning/sql-server-machine-learning-services-python/analyze-sql-server-data-with-python?u=104',
                                              'https://www.linkedin.com/learning/training-neural-networks-in-python-17058600/creating-a-neural-network-in-python?u=104'
    )
WHERE jr.title = 'Full-Stack Developer'
  AND jr.pathwayId = (SELECT pathway_id FROM [dbo].[pathways] WHERE pathway_title= 'Software Development');


COMMIT TRAN;

-------------------------------
-- Block 8.1: Job-Specific Trainings for "Java Developer"
-------------------------------
BEGIN TRAN;

MERGE [dbo].[Training] AS target
USING (VALUES
           ('Azure OpenAI: Generative AI Models and How to Use Them', 'https://www.linkedin.com/learning/azure-openai-generative-ai-models-and-how-to-use-them/welcome?u=104', 'LinkedIn', 'GPT models, DALL-E, copyright, combining models, building AI'),
           ('Building Generative AI Skills for Developers', 'https://www.linkedin.com/learning/paths/building-generative-ai-skills-for-developers?u=104', 'LinkedIn', 'New AI tools and frameworks, AI for developer productivity'),
           ('Java Cloud Certification', 'https://education.oracle.com/software/java/pFamily_48', 'Oracle University', 'Java'),
           ('Java Explorer', 'https://learn.oracle.com/ols/learning-path/java-explorer/88323/79726', 'Oracle University', 'Java arrays, loops, classes, exception handling, interfaces'),
           ('Machine Learning with Python Foundations', 'https://www.linkedin.com/learning/machine-learning-with-python-foundations', 'LinkedIn', 'ML concepts, Python, data prep, model training'),
           ('Web Development', 'https://skillsbuild.org/adult-learners/explore-learning/web-developer', 'IBM', 'HTML/CSS/JS, API integration, frameworks, agile collaboration')
) AS source(title, url, provider, skillsDeveloped)
ON target.url = source.url
WHEN NOT MATCHED THEN
    INSERT (id, title, url, provider, skillsDeveloped)
    VALUES (NEWID(), source.title, source.url, source.provider, source.skillsDeveloped);

COMMIT TRAN;

-------------------------------
-- Block 8.2: Link Trainings to "Java Developer" Job Role
-------------------------------
BEGIN TRAN;

INSERT INTO [dbo].[JobRoleTraining] (id, jobRoleId, trainingId)
SELECT NEWID(), jr.id, t.id
FROM [dbo].[JobRole] jr
         JOIN [dbo].[Training] t ON t.url IN (
                                              'https://www.linkedin.com/learning/azure-openai-generative-ai-models-and-how-to-use-them/welcome?u=104',
                                              'https://www.linkedin.com/learning/paths/building-generative-ai-skills-for-developers?u=104',
                                              'https://education.oracle.com/software/java/pFamily_48',
                                              'https://learn.oracle.com/ols/learning-path/java-explorer/88323/79726',
                                              'https://www.linkedin.com/learning/machine-learning-with-python-foundations',
                                              'https://skillsbuild.org/adult-learners/explore-learning/web-developer'
    )
WHERE jr.title = 'Java Developer'
  AND jr.pathwayId = (SELECT pathway_id FROM [dbo].[pathways] WHERE pathway_title= 'Software Development');


COMMIT TRAN;

-------------------------------
-- Block 9.1: Job-Specific Trainings for "Principal Software Engineer"
-------------------------------
BEGIN TRAN;

MERGE [dbo].[Training] AS target
USING (VALUES
           ('AI Security Nuggets', 'https://www.netacad.com/modules/ai-security-nuggets?courseLang=en-US', 'Cisco', 'AI regulations, AI threat modeling, AI supply chain, RAG, LLM stack'),
           ('CPA: Programming Essentials in C++ (*)', 'https://www.netacad.com/courses/programming/essentials-programming-c-plus-plus', 'Cisco', 'C++'),
           ('IBM DevOps and Software Engineering Professional Certificate', 'https://www.coursera.org/professional-certificates/devops-and-software-engineering', 'IBM / Coursera', 'Python, Web App Dev, AI, CI/CD, Flask, Kubernetes, Test-Driven Dev'),
           ('Project Management Certificate', 'https://www.coursera.org/professional-certificates/google-project-management', 'Google / Coursera', 'Agile, change mgmt, project planning, strategic thinking'),
           ('Securing the Use of Generative AI in Your Organization', 'https://www.linkedin.com/learning/securing-the-use-of-generative-ai-in-your-organization/introduction-to-generative-ai?u=104', 'LinkedIn', 'Generative AI security, compliance, ethical AI, GRC, risk mitigation'),
           ('Software Testing and Automation Specialization', 'https://www.coursera.org/specializations/software-testing-automation', 'University of Minnesota / Coursera', 'Test automation, unit testing, static/dynamic analysis, black-box/white-box techniques')
) AS source(title, url, provider, skillsDeveloped)
ON target.url = source.url
WHEN NOT MATCHED THEN
    INSERT (id, title, url, provider, skillsDeveloped)
    VALUES (NEWID(), source.title, source.url, source.provider, source.skillsDeveloped);

COMMIT TRAN;

-------------------------------
-- Block 9.2: Link Trainings to "Principal Software Engineer" Job Role
-------------------------------
BEGIN TRAN;

INSERT INTO [dbo].[JobRoleTraining] (id, jobRoleId, trainingId)
SELECT NEWID(), jr.id, t.id
FROM [dbo].[JobRole] jr
         JOIN [dbo].[Training] t ON t.url IN (
                                              'https://www.netacad.com/modules/ai-security-nuggets?courseLang=en-US',
                                              'https://www.netacad.com/courses/programming/essentials-programming-c-plus-plus',
                                              'https://www.coursera.org/professional-certificates/devops-and-software-engineering',
                                              'https://www.coursera.org/professional-certificates/google-project-management',
                                              'https://www.linkedin.com/learning/securing-the-use-of-generative-ai-in-your-organization/introduction-to-generative-ai?u=104',
                                              'https://www.coursera.org/specializations/software-testing-automation'
    )
WHERE jr.title = 'Principal Software Engineer'
  AND jr.pathwayId = (SELECT pathway_id FROM [dbo].[pathways] WHERE pathway_title= 'Software Development');

COMMIT TRAN;

-------------------------------
-- Block 10.1: Job-Specific Trainings for "Python Developer"
-------------------------------
BEGIN TRAN;

MERGE [dbo].[Training] AS target
USING (VALUES
           ('AI Powered Programming with GitHub CoPilot (FEE)', 'https://www.linkedin.com/learning/ai-powered-programming-with-github-copilot-by-microsoft-press/welcome-and-course-overview?u=104', 'LinkedIn', 'GitHub Copilot, IDE integration, comment-based generation, unit testing, automation'),
           ('IT Automation with Python', 'https://www.coursera.org/professional-certificates/google-it-automation', 'Google / Coursera', 'Python Programming, Configuration Mgmt, Version Control, Troubleshooting, Automation'),
           ('Python Essentials 1', 'https://skillsforall.com/course/python-essentials-1', 'OpenEDG / Cisco', 'Algorithmic & Analytical Thinking, Basic Python Programming, Debugging, Scripting, Procedural Programming'),
           ('Python Essentials 2', 'https://skillsforall.com/course/python-essentials-2', 'OpenEDG / Cisco', 'Classes, Objects, Inheritance, Iterators, OOP, Modules, Properties, Packages, Polymorphism')
) AS source(title, url, provider, skillsDeveloped)
ON target.url = source.url
WHEN NOT MATCHED THEN
    INSERT (id, title, url, provider, skillsDeveloped)
    VALUES (NEWID(), source.title, source.url, source.provider, source.skillsDeveloped);

COMMIT TRAN;

-------------------------------
-- Block 10.2: Link Trainings to "Python Developer" Job Role
-------------------------------
BEGIN TRAN;

INSERT INTO [dbo].[JobRoleTraining] (id, jobRoleId, trainingId)
SELECT NEWID(), jr.id, t.id
FROM [dbo].[JobRole] jr
         JOIN [dbo].[Training] t ON t.url IN (
                                              'https://www.linkedin.com/learning/ai-powered-programming-with-github-copilot-by-microsoft-press/welcome-and-course-overview?u=104',
                                              'https://www.coursera.org/professional-certificates/google-it-automation',
                                              'https://skillsforall.com/course/python-essentials-1',
                                              'https://skillsforall.com/course/python-essentials-2'
    )
WHERE jr.title = 'Python Developer'
  AND jr.pathwayId = (SELECT pathway_id FROM [dbo].[pathways] WHERE pathway_title= 'Software Development');

COMMIT TRAN;

-------------------------------
-- Block 11.1: Job-Specific Trainings for "Software Architect"
-------------------------------
BEGIN TRAN;

MERGE [dbo].[Training] AS target
USING (VALUES
           ('AI and Developer Productivity (FEE)', 'https://www.linkedin.com/learning/ai-and-developer-productivity/ai-and-developer-productivity?u=104', 'LinkedIn', 'AI for developers, prompts, code optimization, testing, debugging, issue resolution, documentation, remote teamwork'),
           ('ChatGPT Prompt Engineering for Developers', 'https://www.deeplearning.ai/short-courses/chatgpt-prompt-engineering-for-developers/', 'DeepLearning.AI', 'Prompt Engineering, Code Review, Software Debug'),
           ('Machine Learning Specialization', 'https://www.coursera.org/specializations/machine-learning-introduction', 'Stanford / DeepLearning.AI', 'Logistic regression, Artificial Neural Network, Linear Regression, Decision Trees')
) AS source(title, url, provider, skillsDeveloped)
ON target.url = source.url
WHEN NOT MATCHED THEN
    INSERT (id, title, url, provider, skillsDeveloped)
    VALUES (NEWID(), source.title, source.url, source.provider, source.skillsDeveloped);

COMMIT TRAN;

-------------------------------
-- Block 11.2: Link Trainings to "Software Architect" Job Role
-------------------------------
BEGIN TRAN;

INSERT INTO [dbo].[JobRoleTraining] (id, jobRoleId, trainingId)
SELECT NEWID(), jr.id, t.id
FROM [dbo].[JobRole] jr
         JOIN [dbo].[Training] t ON t.url IN (
                                              'https://www.linkedin.com/learning/ai-and-developer-productivity/ai-and-developer-productivity?u=104',
                                              'https://www.deeplearning.ai/short-courses/chatgpt-prompt-engineering-for-developers/',
                                              'https://www.coursera.org/specializations/machine-learning-introduction'
    )
WHERE jr.title = 'Software Architect'
  AND jr.pathwayId = (SELECT pathway_id FROM [dbo].[pathways] WHERE pathway_title= 'Software Development');

COMMIT TRAN;

-------------------------------
-- Block 12.1: Job-Specific Trainings for "Software Developer"
-------------------------------
BEGIN TRAN;

MERGE [dbo].[Training] AS target
USING (VALUES
           ('AI and Developer Productivity (FEE)', 'https://www.linkedin.com/learning/ai-and-developer-productivity/ai-and-developer-productivity?u=104', 'LinkedIn', 'AI for developers, prompts, code optimization, debugging, quality assurance, remote collaboration'),
           ('AI Powered Programming with GitHub CoPilot (FEE)', 'https://www.linkedin.com/learning/ai-powered-programming-with-github-copilot-by-microsoft-press/welcome-and-course-overview?u=104', 'LinkedIn', 'GitHub Copilot, comment-based generation, testing, deployment'),
           ('ChatGPT Prompt Engineering for Developers', 'https://www.deeplearning.ai/short-courses/chatgpt-prompt-engineering-for-developers/', 'DeepLearning.AI', 'Prompt Engineering, Code Review, Software Debug'),
           ('IBM DevOps and Software Engineering Professional Certificate', 'https://www.coursera.org/professional-certificates/devops-and-software-engineering', 'IBM / Coursera', 'Python, App Dev, Web Dev, AI, CI/CD, Microservices, Cloud, DevOps, Testing'),
           ('Machine Learning Specialization', 'https://www.coursera.org/specializations/machine-learning-introduction', 'Stanford / DeepLearning.AI', 'Logistic Regression, Neural Networks, Decision Trees'),
           ('Securing the Use of Generative AI in Your Organization', 'https://www.linkedin.com/learning/securing-the-use-of-generative-ai-in-your-organization/introduction-to-generative-ai?u=104', 'LinkedIn', 'AI Security, GRC, Risk Mitigation, Compliance, Governance')
) AS source(title, url, provider, skillsDeveloped)
ON target.url = source.url
WHEN NOT MATCHED THEN
    INSERT (id, title, url, provider, skillsDeveloped)
    VALUES (NEWID(), source.title, source.url, source.provider, source.skillsDeveloped);

COMMIT TRAN;

-------------------------------
-- Block 12.2: Link Trainings to "Software Developer" Job Role
-------------------------------
BEGIN TRAN;

INSERT INTO [dbo].[JobRoleTraining] (id, jobRoleId, trainingId)
SELECT NEWID(), jr.id, t.id
FROM [dbo].[JobRole] jr
         JOIN [dbo].[Training] t ON t.url IN (
                                              'https://www.linkedin.com/learning/ai-and-developer-productivity/ai-and-developer-productivity?u=104',
                                              'https://www.linkedin.com/learning/ai-powered-programming-with-github-copilot-by-microsoft-press/welcome-and-course-overview?u=104',
                                              'https://www.deeplearning.ai/short-courses/chatgpt-prompt-engineering-for-developers/',
                                              'https://www.coursera.org/professional-certificates/devops-and-software-engineering',
                                              'https://www.coursera.org/specializations/machine-learning-introduction',
                                              'https://www.linkedin.com/learning/securing-the-use-of-generative-ai-in-your-organization/introduction-to-generative-ai?u=104'
    )
WHERE jr.title = 'Software Developer'
  AND jr.pathwayId = (SELECT pathway_id FROM [dbo].[pathways] WHERE pathway_title= 'Software Development');

COMMIT TRAN;

-------------------------------
-- Block 13.1: Job-Specific Trainings for "Senior Software Development Engineer"
-------------------------------
BEGIN TRAN;

MERGE [dbo].[Training] AS target
USING (VALUES
           ('AI and Developer Productivity (FEE)', 'https://www.linkedin.com/learning/ai-and-developer-productivity/ai-and-developer-productivity?u=104', 'LinkedIn', 'AI in development, prompts, optimization, testing, documentation, team collaboration'),
           ('ChatGPT Prompt Engineering for Developers (FEE)', 'https://www.deeplearning.ai/short-courses/chatgpt-prompt-engineering-for-developers/', 'DeepLearning.AI', 'Prompt Engineering, Code Review, Software Debug'),
           ('CPA: Programming Essentials in C++ (*)', 'https://www.netacad.com/courses/programming/essentials-programming-c-plus-plus', 'Cisco', 'C++'),
           ('IBM DevOps and Software Engineering Professional Certificate', 'https://www.coursera.org/professional-certificates/devops-and-software-engineering', 'IBM / Coursera', 'Python, AI, CI/CD, Cloud, Microservices, Kubernetes, Testing'),
           ('Machine Learning Specialization', 'https://www.coursera.org/specializations/machine-learning-introduction', 'Stanford / DeepLearning.AI', 'Logistic Regression, Neural Networks, Decision Trees'),
           ('Preparing for Google Cloud Certification: Cloud DevOps Engineer Professional Certificate (FEE)', 'https://www.coursera.org/professional-certificates/sre-devops-engineer-google-cloud', 'Google / Coursera', 'SRE, Cloud, Google App Engine, Jenkins, Continuous Delivery'),
           ('Project Management Certificate', 'https://www.coursera.org/professional-certificates/google-project-management', 'Google / Coursera', 'Agile, Strategic thinking, Data Analysis, Change Management'),
           ('Software Testing and Automation Specialization', 'https://www.coursera.org/specializations/software-testing-automation', 'University of Minnesota / Coursera', 'Unit Testing, Static/Black-box/White-box Testing, Automation')
) AS source(title, url, provider, skillsDeveloped)
ON target.url = source.url
WHEN NOT MATCHED THEN
    INSERT (id, title, url, provider, skillsDeveloped)
    VALUES (NEWID(), source.title, source.url, source.provider, source.skillsDeveloped);

COMMIT TRAN;

-------------------------------
-- Block 13.2: Link Trainings to "Senior Software Development Engineer" Job Role
-------------------------------
BEGIN TRAN;

INSERT INTO [dbo].[JobRoleTraining] (id, jobRoleId, trainingId)
SELECT NEWID(), jr.id, t.id
FROM [dbo].[JobRole] jr
         JOIN [dbo].[Training] t ON t.url IN (
                                              'https://www.linkedin.com/learning/ai-and-developer-productivity/ai-and-developer-productivity?u=104',
                                              'https://www.deeplearning.ai/short-courses/chatgpt-prompt-engineering-for-developers/',
                                              'https://www.netacad.com/courses/programming/essentials-programming-c-plus-plus',
                                              'https://www.coursera.org/professional-certificates/devops-and-software-engineering',
                                              'https://www.coursera.org/specializations/machine-learning-introduction',
                                              'https://www.coursera.org/professional-certificates/sre-devops-engineer-google-cloud',
                                              'https://www.coursera.org/professional-certificates/google-project-management',
                                              'https://www.coursera.org/specializations/software-testing-automation'
    )
WHERE jr.title = 'Senior Software Development Engineer'
  AND jr.pathwayId = (SELECT pathway_id FROM [dbo].[pathways] WHERE pathway_title= 'Software Development');

COMMIT TRAN;

-------------------------------
-- Block 14.1: Job-Specific Trainings for "Software Engineer"
-------------------------------
BEGIN TRAN;

MERGE [dbo].[Training] AS target
USING (VALUES
           ('AI Powered Programming with GitHub CoPilot (FEE)', 'https://www.linkedin.com/learning/ai-powered-programming-with-github-copilot-by-microsoft-press/welcome-and-course-overview?u=104', 'LinkedIn', 'GitHub Copilot, AI in coding, comment-based generation, IDE integration'),
           ('Back-End Development Professional Certificate', 'https://www.coursera.org/professional-certificates/ibm-backend-development', 'IBM / Coursera', 'Django, MongoDB, Docker, Flask, REST, ORM, SQL, RDBMS, Observability'),
           ('ChatGPT Prompt Engineering for Developers', 'https://www.deeplearning.ai/short-courses/chatgpt-prompt-engineering-for-developers/', 'DeepLearning.AI', 'Prompt Engineering, Code Review, Software Debug'),
           ('Front-End Developer Professional Certificate', 'https://www.coursera.org/professional-certificates/ibm-frontend-developer', 'IBM / Coursera', 'HTML, CSS, JavaScript, Web development'),
           ('IBM DevOps and Software Engineering Professional Certificate', 'https://www.coursera.org/professional-certificates/devops-and-software-engineering', 'IBM / Coursera', 'Python, CI/CD, DevOps, Testing, Flask, Microservices, Cloud, Kubernetes'),
           ('Web Development', 'https://skillsbuild.org/adult-learners/explore-learning/web-developer', 'IBM', 'Full-stack development, HTML/CSS/JS, backend integration, requirement refinement')
) AS source(title, url, provider, skillsDeveloped)
ON target.url = source.url
WHEN NOT MATCHED THEN
    INSERT (id, title, url, provider, skillsDeveloped)
    VALUES (NEWID(), source.title, source.url, source.provider, source.skillsDeveloped);

COMMIT TRAN;

-------------------------------
-- Block 14.2: Link Trainings to "Software Engineer" Job Role
-------------------------------
BEGIN TRAN;

INSERT INTO [dbo].[JobRoleTraining] (id, jobRoleId, trainingId)
SELECT NEWID(), jr.id, t.id
FROM [dbo].[JobRole] jr
         JOIN [dbo].[Training] t ON t.url IN (
                                              'https://www.linkedin.com/learning/ai-powered-programming-with-github-copilot-by-microsoft-press/welcome-and-course-overview?u=104',
                                              'https://www.coursera.org/professional-certificates/ibm-backend-development',
                                              'https://www.deeplearning.ai/short-courses/chatgpt-prompt-engineering-for-developers/',
                                              'https://www.coursera.org/professional-certificates/ibm-frontend-developer',
                                              'https://www.coursera.org/professional-certificates/devops-and-software-engineering',
                                              'https://skillsbuild.org/adult-learners/explore-learning/web-developer'
    )
WHERE jr.title = 'Software Engineer'
  AND jr.pathwayId = (SELECT pathway_id FROM [dbo].[pathways] WHERE pathway_title= 'Software Development');

COMMIT TRAN;

-------------------------------
-- Block 15.1: Job-Specific Trainings for "Senior Software Engineer"
-------------------------------
BEGIN TRAN;

MERGE [dbo].[Training] AS target
USING (VALUES
           ('AI and Developer Productivity (FEE)', 'https://www.linkedin.com/learning/ai-and-developer-productivity/ai-and-developer-productivity?u=104', 'LinkedIn', 'AI for devs, prompts, testing, collaboration, debugging'),
           ('AI Powered Programming with GitHub CoPilot (FEE)', 'https://www.linkedin.com/learning/ai-powered-programming-with-github-copilot-by-microsoft-press/welcome-and-course-overview?u=104', 'LinkedIn', 'GitHub Copilot, IDE integration, unit testing, deployment'),
           ('ChatGPT Prompt Engineering for Developers', 'https://www.deeplearning.ai/short-courses/chatgpt-prompt-engineering-for-developers/', 'DeepLearning.AI', 'Prompt engineering, code review, software debugging'),
           ('CPA: Programming Essentials in C++ (*)', 'https://www.netacad.com/courses/programming/essentials-programming-c-plus-plus', 'Cisco', 'C++'),
           ('IBM Back-End Development Professional Certificate (FEE)', 'https://www.coursera.org/professional-certificates/ibm-backend-development', 'IBM / Coursera', 'Django, MongoDB, Flask, Docker, REST, ORM, SQL, RDBMS'),
           ('IBM Front-End Developer Professional Certificate', 'https://www.coursera.org/professional-certificates/ibm-frontend-developer', 'IBM / Coursera', 'HTML, CSS, JS, React, Front-End, Web Dev'),
           ('Machine Learning Specialization', 'https://www.coursera.org/specializations/machine-learning-introduction', 'Stanford / DeepLearning.AI', 'Logistic Regression, Neural Networks, Decision Trees'),
           ('Preparing for Google Cloud Certification: Cloud DevOps Engineer Professional Certificate (FEE)', 'https://www.coursera.org/professional-certificates/sre-devops-engineer-google-cloud', 'Google / Coursera', 'SRE, CI/CD, Google Cloud, Kubernetes, Jenkins'),
           ('Project Management Certificate', 'https://www.coursera.org/professional-certificates/google-project-management', 'Google / Coursera', 'Agile PM, change/data management, strategic planning'),
           ('Software Testing and Automation Specialization', 'https://www.coursera.org/specializations/software-testing-automation', 'University of Minnesota / Coursera', 'Unit testing, automation, static analysis, white/black box testing')
) AS source(title, url, provider, skillsDeveloped)
ON target.url = source.url
WHEN NOT MATCHED THEN
    INSERT (id, title, url, provider, skillsDeveloped)
    VALUES (NEWID(), source.title, source.url, source.provider, source.skillsDeveloped);

COMMIT TRAN;

-------------------------------
-- Block 15.2: Link Trainings to "Senior Software Engineer" Job Role
-------------------------------
BEGIN TRAN;

INSERT INTO [dbo].[JobRoleTraining] (id, jobRoleId, trainingId)
SELECT NEWID(), jr.id, t.id
FROM [dbo].[JobRole] jr
         JOIN [dbo].[Training] t ON t.url IN (
                                              'https://www.linkedin.com/learning/ai-and-developer-productivity/ai-and-developer-productivity?u=104',
                                              'https://www.linkedin.com/learning/ai-powered-programming-with-github-copilot-by-microsoft-press/welcome-and-course-overview?u=104',
                                              'https://www.deeplearning.ai/short-courses/chatgpt-prompt-engineering-for-developers/',
                                              'https://www.netacad.com/courses/programming/essentials-programming-c-plus-plus',
                                              'https://www.coursera.org/professional-certificates/ibm-backend-development',
                                              'https://www.coursera.org/professional-certificates/ibm-frontend-developer',
                                              'https://www.coursera.org/specializations/machine-learning-introduction',
                                              'https://www.coursera.org/professional-certificates/sre-devops-engineer-google-cloud',
                                              'https://www.coursera.org/professional-certificates/google-project-management',
                                              'https://www.coursera.org/specializations/software-testing-automation'
    )
WHERE jr.title = 'Senior Software Engineer'
  AND jr.pathwayId = (SELECT pathway_id FROM [dbo].[pathways] WHERE pathway_title= 'Software Development');

COMMIT TRAN;

-------------------------------
-- Block 16.1: Job-Specific Trainings for "Web Developer"
-------------------------------
BEGIN TRAN;

MERGE [dbo].[Training] AS target
USING (VALUES
           ('AI and Developer Productivity (FEE)', 'https://www.linkedin.com/learning/ai-and-developer-productivity/ai-and-developer-productivity?u=104', 'LinkedIn', 'Prompts, code optimization, testing, debugging, remote teamwork'),
           ('AI Powered Programming with GitHub CoPilot (FEE)', 'https://www.linkedin.com/learning/ai-powered-programming-with-github-copilot-by-microsoft-press/welcome-and-course-overview?u=104', 'LinkedIn', 'GitHub Copilot, IDE integration, unit testing, deployment'),
           ('Building Generative AI Skills for Developers', 'https://www.linkedin.com/learning/paths/building-generative-ai-skills-for-developers?u=104', 'LinkedIn', 'AI tools, developer productivity, faster prototyping'),
           ('ChatGPT for Web Developers', 'https://www.linkedin.com/learning/chatgpt-for-web-developers/accelerate-your-web-development-process?u=104', 'LinkedIn', 'ChatGPT UI, CSS, JavaScript, React, AI page generation'),
           ('Web Development', 'https://skillsbuild.org/adult-learners/explore-learning/web-developer', 'IBM', 'HTML, CSS, JavaScript, APIs, databases, stakeholder alignment')
) AS source(title, url, provider, skillsDeveloped)
ON target.url = source.url
WHEN NOT MATCHED THEN
    INSERT (id, title, url, provider, skillsDeveloped)
    VALUES (NEWID(), source.title, source.url, source.provider, source.skillsDeveloped);

COMMIT TRAN;

-------------------------------
-- Block 16.2: Link Trainings to "Web Developer" Job Role
-------------------------------
BEGIN TRAN;

INSERT INTO [dbo].[JobRoleTraining] (id, jobRoleId, trainingId)
SELECT NEWID(), jr.id, t.id
FROM [dbo].[JobRole] jr
         JOIN [dbo].[Training] t ON t.url IN (
                                              'https://www.linkedin.com/learning/ai-and-developer-productivity/ai-and-developer-productivity?u=104',
                                              'https://www.linkedin.com/learning/ai-powered-programming-with-github-copilot-by-microsoft-press/welcome-and-course-overview?u=104',
                                              'https://www.linkedin.com/learning/paths/building-generative-ai-skills-for-developers?u=104',
                                              'https://www.linkedin.com/learning/chatgpt-for-web-developers/accelerate-your-web-development-process?u=104',
                                              'https://skillsbuild.org/adult-learners/explore-learning/web-developer'
    )
WHERE jr.title = 'Web Developer'
  AND jr.pathwayId = (SELECT pathway_id FROM [dbo].[pathways] WHERE pathway_title= 'Software Development');

COMMIT TRAN;
