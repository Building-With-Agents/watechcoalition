-------------------------------
-- Block 1.1: Insert Foundational Trainings for "Data Science" Job Group
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
           ('Career Management Essentials', 'https://ibm.biz/BdGpZT', 'IBM', 'Career development, Career management, Communication skills, Generative AI tool use, Networking skills, Presentation skills, Professional interviewing skills, Professional online brand development, Resume writing, Social media presence, Workplace research'),
           ('Creating compelling Reports', 'https://skillsforall.com/course/compelling-reports', 'Cisco', 'Communication, presentation'),
           ('Data Analytics Certificate', 'https://www.credly.com/org/ibm/badge/ibm-skillsbuild-data-analytics-certificate', 'IBM', 'Data Classification, Data Usability for Organizations, Inferential and Descriptive Statistics, Data Collection and Analysis, Data Preparation for Analysis, Data Visualization and Presentation'),
           ('Develop Your Prompt Engineering Skills', 'https://www.linkedin.com/learning/paths/develop-your-prompt-engineering-skills?u=104', 'LinkedIn', 'Prompt engineering'),
           ('Digital Literacy', 'https://ibm.biz/BdGhnB', 'IBM', 'AI, Collaboration, Computer literacy, Data analysis, Data presentation, Digital communications, Digital literacy, Employability skills, Internet security, Software engineering, Web navigation'),
           ('Digital Mindset', 'https://ibm.biz/BdGpYc', 'IBM', 'Adaptability and flexibility, Collaboration, Creativity, Data-driven decisions, Decision making, Digital mindset, Employability skills, Entrepreneurial mindset, Growth mindset, Innovation, Lifelong learning, Managing ambiguity and change, Professional networking, Teamwork'),
           ('Engaging Stakeholders for Success', 'https://skillsforall.com/course/engaging-stakeholders', 'Cisco', 'Communication, Stakeholder engagement, Change Management'),
           ('Explore Emerging Tech', 'https://www.credly.com/org/ibm-skillsbuild/badge/explore-emerging-tech', 'IBM', 'Artificial intelligence, data, blockchain, cloud, cybersecurity, iot'),
           ('Introduction to Artificial Intelligence', 'https://academy.aiskills.eu/course/1-introduction-to-artificial-intelligence', 'DIGITALEUROPE', 'Machine Learning, Deep Learning, Natural Language Processing, Computer Vision, Data Science Fundamentals, AI Ethics and Governance'),
           ('Introduction to Data Analytics', 'https://www.coursera.org/learn/introduction-to-data-analytics', 'IBM / Coursera', 'Data analysis, data visualization, Microsoft Excel'),
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
-- Block 1.2: Link Foundational Trainings to "Data Science" Job Group
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
                                              'https://www.credly.com/org/ibm/badge/ibm-skillsbuild-data-analytics-certificate',
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
WHERE p.pathway_title = 'Data Science';

COMMIT TRAN;

-------------------------------
-- Block 2.1: Job-Specific Trainings for "Data Analyst"
-------------------------------
BEGIN TRAN;

MERGE [dbo].[Training] AS target
USING (VALUES
           ('Advanced Data Analytics Professional Certificate', 'https://www.coursera.org/professional-certificates/google-advanced-data-analytics', 'Google / Coursera', 'Data Science, Data Analysis, Python Programming, Jupyter Notebook, Machine Learning, Statistical Analysis, Tableau Software, Data Visualization, Predictive Modeling, Kaggle'),
           ('Data Analysis with Python', 'https://www.coursera.org/learn/data-analysis-with-python', 'IBM / Coursera', 'Model Selection, Data Analyst, Python Programming, Data Visualization, Predictive Modeling'),
           ('Data Analyst Capstone Project', 'https://www.coursera.org/learn/ibm-data-analyst-capstone-project', 'IBM / Coursera', 'Data Analyst, Python Programming, Dashboard, Data visualization, SQL and RDBMS'),
           ('Data Analyst Professional Certificate', 'https://www.coursera.org/professional-certificates/ibm-data-analyst', 'IBM / Coursera', 'Data science, Spreadsheet, Data Analysis, Python Programming, Microsoft Excel, IBM Cognos Analytics, Dashboard, SQL, Numpy, Pandas, Data Visualization, Pivot Table'),
           ('Data Analytics Certificate', 'https://www.credly.com/org/ibm/badge/ibm-skillsbuild-data-analytics-certificate', 'IBM', 'Data Classification, Data Usability for Organizations, Inferential and Descriptive Statistics, Data Collection and Analysis, Data Preparation for Analysis, Data Visualization and Presentation'),
           ('Data Analytics Essentials', 'https://skillsforall.com/course/data-analytics-essentials?courseLang=en-US', 'Cisco', 'Data analysis, Analytical skills'),
           ('Data Analytics Certificate', 'https://www.coursera.org/professional-certificates/google-data-analytics', 'Google / Coursera', 'Data Analysis, Creating case studies, Data Visualization, Data Cleansing, Developing a portfolio, Data Collection, Spreadsheet, Metadata, SQL, Data Ethics, Data Aggregation, R Markdown'),
           ('Data Visualization and Dashboards with Excel and Cognos', 'https://www.coursera.org/learn/data-visualization-dashboards-excel-cognos', 'IBM / Coursera', 'Data Analyst, Dashboard, Data visualization'),
           ('Databases and SQL for Data Science with Python', 'https://www.coursera.org/learn/sql-data-science', 'IBM / Coursera', 'Python Programming, SQL, Cloud databases'),
           ('Excel Basics for Data Analysis', 'https://www.coursera.org/learn/excel-basics-data-analysis-ibm', 'IBM / Coursera', 'Data analysis, Pivot table'),
           ('Python for Data Science, AI & Development', 'https://www.coursera.org/learn/python-for-applied-data-science-ai', 'IBM / Coursera', 'Python Programming, Panda, Numpy')
) AS source(title, url, provider, skillsDeveloped)
ON target.url = source.url
WHEN NOT MATCHED THEN
    INSERT (id, title, url, provider, skillsDeveloped)
    VALUES (NEWID(), source.title, source.url, source.provider, source.skillsDeveloped);

COMMIT TRAN;

-------------------------------
-- Block 2.2: Link Trainings to "Data Analyst" Job Role
-------------------------------
BEGIN TRAN;

INSERT INTO [dbo].[JobRoleTraining] (id, jobRoleId, trainingId)
SELECT NEWID(), jr.id, t.id
FROM [dbo].[JobRole] jr
         JOIN [dbo].[Training] t ON t.url IN (
                                              'https://www.coursera.org/professional-certificates/google-advanced-data-analytics',
                                              'https://www.coursera.org/learn/data-analysis-with-python',
                                              'https://www.coursera.org/learn/ibm-data-analyst-capstone-project',
                                              'https://www.coursera.org/professional-certificates/ibm-data-analyst',
                                              'https://www.credly.com/org/ibm/badge/ibm-skillsbuild-data-analytics-certificate',
                                              'https://skillsforall.com/course/data-analytics-essentials?courseLang=en-US',
                                              'https://www.coursera.org/professional-certificates/google-data-analytics',
                                              'https://www.coursera.org/learn/data-visualization-dashboards-excel-cognos',
                                              'https://www.coursera.org/learn/sql-data-science',
                                              'https://www.coursera.org/learn/excel-basics-data-analysis-ibm',
                                              'https://www.coursera.org/learn/python-for-applied-data-science-ai'
    )
WHERE jr.title = 'Data Analyst'
  AND pathwayId = (SELECT pathway_id FROM [dbo].[pathways] WHERE pathway_title = 'Data Science');

COMMIT TRAN;

-------------------------------
-- Block 3.1: Job-Specific Trainings for "Data Engineer"
-------------------------------
BEGIN TRAN;

MERGE [dbo].[Training] AS target
USING (VALUES
           ('Data Engineering Pipeline Management with Apache Airflow (FEE)', 'https://www.linkedin.com/learning/data-engineering-pipeline-management-with-apache-airflow', 'LinkedIn', 'Apache Airflow, role-based access control, DAGs, SLA management, CSV reader plugin, task orchestration, pipeline execution, scheduling DAGs, dataset linking'),
           ('Data Management with Apache NiFi (FEE)', 'https://www.linkedin.com/learning/data-management-with-apache-nifi', 'LinkedIn', 'Apache NiFi, flow file processing, integration with PostgreSQL, Amazon S3, data streaming, processor groups, downloading/installing NiFi, CSV ingestion, configuring back pressure, monitoring, NiFi dashboards'),
           ('Machine Learning with Python Foundations', 'https://www.linkedin.com/learning/machine-learning-with-python-foundations', 'LinkedIn', 'Machine learning foundations, step-by-step Python ML guidance, model building, evaluation, interpretation of ML results, Python programming'),
           ('SQL Server Machine Learning Services with Python', 'https://www.linkedin.com/learning/sql-server-machine-learning-services-python/analyze-sql-server-data-with-python?u=104', 'LinkedIn', 'SQL Server, Python integration, SQL ML Services, Data Science with Python, predictive modeling, bar charts, stored procedures, script execution inside SQL'),
           ('Training Neural Networks in Python', 'https://www.linkedin.com/learning/training-neural-networks-in-python-17058600/creating-a-neural-network-in-python?u=104', 'LinkedIn', 'Neural networks, artificial neurons, deep learning, backpropagation, Python implementation of networks, use of libraries, problem-solving via biologically inspired models, choosing activation functions, training models')
) AS source(title, url, provider, skillsDeveloped)
ON target.url = source.url
WHEN NOT MATCHED THEN
    INSERT (id, title, url, provider, skillsDeveloped)
    VALUES (NEWID(), source.title, source.url, source.provider, source.skillsDeveloped);

COMMIT TRAN;

-------------------------------
-- Block 3.2: Link Trainings to "Data Engineer" Job Role
-------------------------------
BEGIN TRAN;

INSERT INTO [dbo].[JobRoleTraining] (id, jobRoleId, trainingId)
SELECT NEWID(), jr.id, t.id
FROM [dbo].[JobRole] jr
         JOIN [dbo].[Training] t ON t.url IN (
                                              'https://www.linkedin.com/learning/data-engineering-pipeline-management-with-apache-airflow',
                                              'https://www.linkedin.com/learning/data-management-with-apache-nifi',
                                              'https://www.linkedin.com/learning/machine-learning-with-python-foundations',
                                              'https://www.linkedin.com/learning/sql-server-machine-learning-services-python/analyze-sql-server-data-with-python?u=104',
                                              'https://www.linkedin.com/learning/training-neural-networks-in-python-17058600/creating-a-neural-network-in-python?u=104'
    )
WHERE jr.title = 'Data Engineer'
  AND pathwayId = (SELECT pathway_id FROM [dbo].[pathways] WHERE pathway_title = 'Data Science');

COMMIT TRAN;

-------------------------------
-- Block 4.1: Job-Specific Trainings for "Data Scientist"
-------------------------------
BEGIN TRAN;

MERGE [dbo].[Training] AS target
USING (VALUES
           ('IBM Data Science Certificate', 'https://www.coursera.org/professional-certificates/ibm-data-science', 'IBM / Coursera', 'Big Data Technologies, Tools and Techniques, Data Mining, Data Modeling, Statistical Analysis Programming Languages, Machine Learning Frameworks'),
           ('Machine Learning Specialization', 'https://www.coursera.org/specializations/machine-learning-introduction', 'Stanford / DeepLearning.AI', 'Logistic regression, Artificial Neural Network, Linear Regression, Decision Trees'),
           ('Machine Learning with Python Foundations', 'https://www.linkedin.com/learning/machine-learning-with-python-foundations', 'LinkedIn', 'Step-by-step ML in Python, data prep, model building, evaluation and interpretation of machine learning results using Python'),
           ('MIT Statistics and Data Science Certificate (FEE)', 'https://micromasters.mit.edu/ds/', 'EDX', 'Big Data Technologies, Tools and Techniques, Data Mining, Data Modeling, Statistical Analysis Programming Languages, Machine Learning Framework'),
           ('Python for Data Science, AI & Development', 'https://www.coursera.org/learn/python-for-applied-data-science-ai', 'IBM / Coursera', 'Python Programming, Panda, Numpy')
) AS source(title, url, provider, skillsDeveloped)
ON target.url = source.url
WHEN NOT MATCHED THEN
    INSERT (id, title, url, provider, skillsDeveloped)
    VALUES (NEWID(), source.title, source.url, source.provider, source.skillsDeveloped);

COMMIT TRAN;

-------------------------------
-- Block 4.2: Link Trainings to "Data Scientist" Job Role
-------------------------------
BEGIN TRAN;

INSERT INTO [dbo].[JobRoleTraining] (id, jobRoleId, trainingId)
SELECT NEWID(), jr.id, t.id
FROM [dbo].[JobRole] jr
         JOIN [dbo].[Training] t ON t.url IN (
                                              'https://www.coursera.org/professional-certificates/ibm-data-science',
                                              'https://www.coursera.org/specializations/machine-learning-introduction',
                                              'https://www.linkedin.com/learning/machine-learning-with-python-foundations',
                                              'https://micromasters.mit.edu/ds/',
                                              'https://www.coursera.org/learn/python-for-applied-data-science-ai'
    )
WHERE jr.title = 'Data Scientist'
  AND pathwayId = (SELECT pathway_id FROM [dbo].[pathways] WHERE pathway_title = 'Data Science');

COMMIT TRAN;

-------------------------------
-- Block 5.1: Job-Specific Trainings for "Data Specialist"
-------------------------------
BEGIN TRAN;

MERGE [dbo].[Training] AS target
USING (VALUES
           ('Data Management with Apache NiFi (FEE)', 'https://www.linkedin.com/learning/data-management-with-apache-nifi', 'LinkedIn', 'Apache NiFi, flow file processing, NiFi processors, PostgreSQL integration, processor groups, CSV ingestion, configuring back pressure, monitoring, Amazon S3, dashboards'),
           ('Machine Learning with Python Foundations', 'https://www.linkedin.com/learning/machine-learning-with-python-foundations', 'LinkedIn', 'Machine learning in Python, model building, evaluation, interpretation, understanding ML techniques and workflows'),
           ('Power BI: Integrating AI and Machine Learning (FEE)', 'https://www.linkedin.com/learning/power-bi-integrating-ai-and-machine-learning', 'LinkedIn', 'Power BI, data modeling, single variable analysis, time series, visualizations, asking questions from visuals, relationship measurement, sharing results, AI/ML integration'),
           ('SQL Server Machine Learning Services with Python', 'https://www.linkedin.com/learning/sql-server-machine-learning-services-python/analyze-sql-server-data-with-python?u=104', 'LinkedIn', 'SQL Server ML Services, Python integration, predictive analytics, data preparation, charting, storing procedures, executing ML scripts without performance hits'),
           ('Training Neural Networks in Python', 'https://www.linkedin.com/learning/training-neural-networks-in-python-17058600/creating-a-neural-network-in-python?u=104', 'LinkedIn', 'Neural networks in Python, training models, activation functions, biologically inspired modeling, model evaluation and selection')
) AS source(title, url, provider, skillsDeveloped)
ON target.url = source.url
WHEN NOT MATCHED THEN
    INSERT (id, title, url, provider, skillsDeveloped)
    VALUES (NEWID(), source.title, source.url, source.provider, source.skillsDeveloped);

COMMIT TRAN;

-------------------------------
-- Block 5.2: Link Trainings to "Data Specialist" Job Role
-------------------------------
BEGIN TRAN;

INSERT INTO [dbo].[JobRoleTraining] (id, jobRoleId, trainingId)
SELECT NEWID(), jr.id, t.id
FROM [dbo].[JobRole] jr
         JOIN [dbo].[Training] t ON t.url IN (
                                              'https://www.linkedin.com/learning/data-management-with-apache-nifi',
                                              'https://www.linkedin.com/learning/machine-learning-with-python-foundations',
                                              'https://www.linkedin.com/learning/power-bi-integrating-ai-and-machine-learning',
                                              'https://www.linkedin.com/learning/sql-server-machine-learning-services-python/analyze-sql-server-data-with-python?u=104',
                                              'https://www.linkedin.com/learning/training-neural-networks-in-python-17058600/creating-a-neural-network-in-python?u=104'
    )
WHERE jr.title = 'Data Specialist'
  AND pathwayId = (SELECT pathway_id FROM [dbo].[pathways] WHERE pathway_title = 'Data Science');

COMMIT TRAN;
