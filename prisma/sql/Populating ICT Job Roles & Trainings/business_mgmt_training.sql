------------------------------------------------------------------
-- Refactored T-SQL Script using MERGE for Upsert Based on URL Uniqueness
------------------------------------------------------------------

-------------------------------
-- Block 1: Foundational Training Records for "Business and Management"
-------------------------------
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
           ('Career Management Essentials', 'https://ibm.biz/BdGpZT', 'IBM', 'Career development, Career management, Communication skills, Generative AI tool use, Networking skills, Presentation skills, Professional interviewing skills, Professional online brand development, Resume writing, Socialmedia presence, Workplace research'),
           ('Develop Your Prompt Engineering Skills', 'https://www.linkedin.com/learning/paths/develop-your-prompt-engineering-skills?u=104', 'LinkedIn', 'Prompt engineering'),
           ('Digital Literacy', 'https://ibm.biz/BdGhnB', 'IBM', 'AI, Collaboration, Computer literacy, Data analysis, Data presentation, Digital communications, Digital literacy, Employability skills, Internet security, Software engineering, Web navigation'),
           ('Digital Mindset', 'https://ibm.biz/BdGpYc', 'IBM', 'Adaptability and flexibility, Collaboration, Creativity, Data-driven decisions, Decision making, Digital mindset, Employability skills, Entrepreneurial mindset, Growth mindset, Innovation, Lifelong learning, Managing ambiguity and change, Professional networking, Teamwork'),
           ('Engaging Stakeholders for Success', 'https://skillsforall.com/course/engaging-stakeholders', 'Cisco', 'Communication, Stakeholder engagement, Change Management'),
           ('Explore Emerging Tech', 'https://www.credly.com/org/ibm-skillsbuild/badge/explore-emerging-tech', 'IBM', 'Artificial intelligence, data, blockchain, cloud, cybersecurity, iot'),
           ('Foundations of Project Management', 'https://www.coursera.org/learn/project-management-foundations', 'Google / Coursera', 'Project management'),
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

BEGIN TRAN;

COMMIT TRAN;

-------------------------------
-- Block 1.2: Associate These Trainings with the "Business and Management" Job Group
-------------------------------
BEGIN TRAN;

INSERT INTO [dbo].[PathwayTraining] (id, pathwayId, trainingId)
SELECT NEWID(), p.pathway_id, t.id
FROM [dbo].[pathways] p
         JOIN [dbo].[Training] t ON t.url IN (
                                              'https://ibm.biz/BdGpZ8',
                                              'https://a16z.com/ai-canon/',
                                              'https://grow.google/ai-essentials/',
                                              'https://ibm.biz/BdGpZ9',
                                              'https://www.coursera.org/learn/ai-for-everyone',
                                              'https://ibm.biz/BdGpZT',
                                              'https://www.linkedin.com/learning/paths/building-ai-literacy?u=26890602',
                                              'https://www.linkedin.com/learning/building-career-agility-and-resilience-in-the-age-of-ai/prepare-for-your-ai-enhanced-career?u=104',
                                              'https://www.linkedin.com/learning/paths/develop-your-prompt-engineering-skills?u=104',
                                              'https://ibm.biz/BdGhnB',
                                              'https://ibm.biz/BdGpYc',
                                              'https://skillsforall.com/course/engaging-stakeholders',
                                              'https://www.coursera.org/learn/enterprise-design-thinking-co-creator',
                                              'https://www.ibm.com/design/thinking/page/courses/Practitioner',
                                              'https://www.credly.com/org/ibm-skillsbuild/badge/explore-emerging-tech',
                                              'https://www.coursera.org/learn/project-management-foundations',
                                              'https://academy.aiskills.eu/course/1-introduction-to-artificial-intelligence',
                                              'https://www.coursera.org/learn/introduction-to-data-analytics',
                                              'https://skillsforall.com/course/introduction-to-modern-ai?courseLang=en-US',
                                              'https://www.edx.org/learn/artificial-intelligence/ibm-introduction-to-prompt-engineering',
                                              'https://www.netacad.com/modules/introduction-to-responsible-ai-skills?courseLang=en-US',
                                              'https://www.linkedin.com/learning/paths/responsible-ai-foundations',
                                              'https://www.credly.com/org/ibm-skillsbuild/badge/working-in-a-digital-world-professional-skills'
    )
WHERE p.pathway_title = 'Business and Management';

COMMIT TRAN;

-------------------------------
-- Block 2: Job-Specific Training Records for "Business Analyst"
-------------------------------
BEGIN TRAN;

MERGE [dbo].[Training] AS target
USING (VALUES
           ('Advanced Data Analytics Professional Certificate', 'https://www.coursera.org/professional-certificates/google-advanced-data-analytics', 'Google / Coursera', 'Data Science, Data Analysis, Python Programming, Jupyter Notebook, Machine Learning, Statistical Analysis, Tableau Software, Data Visualization, Predictive Modelling, Kaggle'),
           ('Business Intelligence Certificate', 'https://www.coursera.org/professional-certificates/google-business-intelligence', 'Google / Coursera', 'Business Intelligence, Extraction, Transformation And Loading (ETL), Bigquery, Dashboarding and Reporting, Data Analysis, Data Modeling, Business Analysis, SQL, Tableau Software, Business Process'),
           ('Data Analysis with Python', 'https://www.coursera.org/learn/data-analysis-with-python', 'IBM / Coursera', 'Model Selection, Data Analyst, Python Programming, Data Visualization, Predictive Modelling'),
           ('Data Analyst Capstone Project', 'https://www.coursera.org/learn/ibm-data-analyst-capstone-project', 'IBM / Coursera', 'Data Analyst, Python Programming, Dashboard, Data visualization, SQL and RDBMS'),
           ('Data Analyst Certificate', 'https://www.coursera.org/professional-certificates/google-data-analytics', 'Google / Coursera', 'Data analysis, data visualization, Data driven decision making, Data-driven insights, Responsible AI'),
           ('Data Analyst Professional Certificate', 'https://www.coursera.org/professional-certificates/ibm-data-analyst', 'IBM / Coursera', 'Data science, Spreadsheet, Data Analysis, Python Programming, Microsoft Excel, Ibm Cognos Analytics, Dashboard, SQL, Numpy, Pandas, Data Visualization, Pivot Table'),
           ('Data Analytics Certificate', 'https://www.credly.com/org/ibm/badge/ibm-skillsbuild-data-analytics-certificate', 'IBM', 'Data Classification; Data Usability for Organizations; Inferential and Descriptive Statistics; Data Collection and Analysis; Data Preparation for Analysis; Data Visualization and Presentation'),
           ('Data Analytics Essentials', 'https://skillsforall.com/course/data-analytics-essentials?courseLang=en-US', 'Cisco', 'Data analysis, Analytical skills'),
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

BEGIN TRAN;

INSERT INTO [dbo].[JobRoleTraining] (id, jobRoleId, trainingId)
SELECT NEWID(), jr.id, t.id
FROM [dbo].[JobRole] jr
         JOIN [dbo].[Training] t ON t.url IN (
                                              'https://www.coursera.org/professional-certificates/google-advanced-data-analytics',
                                              'https://www.coursera.org/professional-certificates/google-business-intelligence',
                                              'https://www.coursera.org/learn/data-analysis-with-python',
                                              'https://www.coursera.org/learn/ibm-data-analyst-capstone-project',
                                              'https://www.coursera.org/professional-certificates/google-data-analytics',
                                              'https://www.coursera.org/professional-certificates/ibm-data-analyst',
                                              'https://www.credly.com/org/ibm/badge/ibm-skillsbuild-data-analytics-certificate',
                                              'https://skillsforall.com/course/data-analytics-essentials?courseLang=en-US',
                                              'https://www.coursera.org/learn/data-visualization-dashboards-excel-cognos',
                                              'https://www.coursera.org/learn/sql-data-science',
                                              'https://www.coursera.org/learn/excel-basics-data-analysis-ibm',
                                              'https://www.coursera.org/learn/python-for-applied-data-science-ai'
    )
WHERE jr.title = 'Business Analyst'
  AND jr.pathwayId = (SELECT pathway_id FROM [dbo].[pathways] WHERE pathway_title = 'Business and Management');

COMMIT TRAN;

-------------------------------
-- Block 3: Job-Specific Training Records for "Business Intelligence Analyst"
-------------------------------
BEGIN TRAN;

MERGE [dbo].[Training] AS target
USING (VALUES
           ('Advanced Data Analytics Professional Certificate', 'https://www.coursera.org/professional-certificates/google-advanced-data-analytics', 'Google / Coursera', 'Data Science, Data Analysis, Python Programming, Jupyter Notebook, Machine Learning, Statistical Analysis, Tableau Software, Data Visualization, Predictive Modelling, Kaggle'),
           ('Business Intelligence Certificate', 'https://www.coursera.org/professional-certificates/google-business-intelligence', 'Google / Coursera', 'Business Intelligence, Extraction, Transformation And Loading (ETL), Bigquery, Dashboarding and Reporting, Data Analysis, Data Modeling, Business Analysis, SQL, Tableau Software, Business Process'),
           ('Data Analysis with Python', 'https://www.coursera.org/learn/data-analysis-with-python', 'IBM / Coursera', 'Model Selection, Data Analyst, Python Programming, Data Visualization, Predictive Modelling'),
           ('Data Analyst Capstone Project', 'https://www.coursera.org/learn/ibm-data-analyst-capstone-project', 'IBM / Coursera', 'Data Analyst, Python Programming, Dashboard, Data visualization, SQL and RDBMS'),
           ('Data Analyst Certificate', 'https://www.coursera.org/professional-certificates/google-data-analytics', 'Google / Coursera', 'Data analysis, data visualization, Data driven decision making, Data-driven insights, Responsible AI'),
           ('Data Analyst Professional Certificate', 'https://www.coursera.org/professional-certificates/ibm-data-analyst', 'IBM / Coursera', 'Data science, Spreadsheet, Data Analysis, Python Programming, Microsoft Excel, Ibm Cognos Analytics, Dashboard, SQL, Numpy, Pandas, Data Visualization, Pivot Table'),
           ('Data Visualization and Dashboards with Excel and Cognos', 'https://www.coursera.org/learn/data-visualization-dashboards-excel-cognos', 'IBM / Coursera', 'Data Analyst, Dashboard, Data visualization'),
           ('Databases and SQL for Data Science with Python', 'https://www.coursera.org/learn/sql-data-science', 'IBM / Coursera', 'Python Programming, SQL, Cloud databases'),
           ('Excel Basics for Data Analysis', 'https://www.coursera.org/learn/excel-basics-data-analysis-ibm', 'IBM / Coursera', 'Data analysis, Pivot table'),
           ('Getting Started with R for Data Science', 'https://www.linkedin.com/learning/paths/getting-started-with-r-for-data-science', 'LinkedIn', 'Data analysis, R Programming'),
           ('Machine Learning Specialization', 'https://www.coursera.org/specializations/machine-learning-introduction', 'Stanford / DeepLearning.AI', 'Logistic regression, Artificial Neural Network, Linear Regression, Decision Trees'),
           ('Machine Learning with Python Foundations', 'https://www.linkedin.com/learning/machine-learning-with-python-foundations', 'LinkedIn', 'Step-by-step guidance for machine learning using Python'),
           ('Power BI: Integrating AI and Machine Learning (FEE)', 'https://www.linkedin.com/learning/power-bi-integrating-ai-and-machine-learning', 'LinkedIn', 'Overview of Power BI, including AI and machine learning integration'),
           ('Python for Data Science, AI & Development', 'https://www.coursera.org/learn/python-for-applied-data-science-ai', 'IBM / Coursera', 'Python Programming, Panda, Numpy'),
           ('SAP analytics', 'https://training.sap.com/content/sap-analytics-training', 'SAP', 'Crystal Reports, SAP BI Platform Administration, SAP Lumira')
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
                                              'https://www.coursera.org/professional-certificates/google-advanced-data-analytics',
                                              'https://www.coursera.org/professional-certificates/google-business-intelligence',
                                              'https://www.coursera.org/learn/data-analysis-with-python',
                                              'https://www.coursera.org/learn/ibm-data-analyst-capstone-project',
                                              'https://www.coursera.org/professional-certificates/google-data-analytics',
                                              'https://www.coursera.org/professional-certificates/ibm-data-analyst',
                                              'https://www.coursera.org/learn/data-visualization-dashboards-excel-cognos',
                                              'https://www.coursera.org/learn/sql-data-science',
                                              'https://www.coursera.org/learn/excel-basics-data-analysis-ibm',
                                              'https://www.linkedin.com/learning/paths/getting-started-with-r-for-data-science',
                                              'https://www.coursera.org/specializations/machine-learning-introduction',
                                              'https://www.linkedin.com/learning/machine-learning-with-python-foundations',
                                              'https://www.linkedin.com/learning/power-bi-integrating-ai-and-machine-learning',
                                              'https://www.coursera.org/learn/python-for-applied-data-science-ai',
                                              'https://training.sap.com/content/sap-analytics-training'
    )
WHERE jr.title = 'Business Intelligence Analyst'
  AND jr.pathwayId = (SELECT pathway_id FROM [dbo].[pathways] WHERE pathway_title = 'Business and Management');

COMMIT TRAN;

-------------------------------
-- Block 4: Job-Specific Training Records for "Business Systems Analyst"
-------------------------------
BEGIN TRAN;

MERGE [dbo].[Training] AS target
USING (VALUES
           ('Data Analysis with Python', 'https://www.coursera.org/learn/data-analysis-with-python', 'IBM / Coursera', 'Model Selection, Data Analyst, Python Programming, Data Visualization, Predictive Modelling'),
           ('Data Analyst Capstone Project', 'https://www.coursera.org/learn/ibm-data-analyst-capstone-project', 'IBM / Coursera', 'Data Analyst, Python Programming, Dashboard, Data visualization, SQL and RDBMS'),
           ('Data Analyst Professional Certificate', 'https://www.coursera.org/professional-certificates/ibm-data-analyst', 'IBM / Coursera', 'Data science, Spreadsheet, Data Analysis, Python Programming, Microsoft Excel, Ibm Cognos Analytics, Dashboard, SQL, Numpy, Pandas, Data Visualization, Pivot Table'),
           ('Data Visualization and Dashboards with Excel and Cognos', 'https://www.coursera.org/learn/data-visualization-dashboards-excel-cognos', 'IBM / Coursera', 'Data Analyst, Dashboard, Data visualization'),
           ('Databases and SQL for Data Science with Python', 'https://www.coursera.org/learn/sql-data-science', 'IBM / Coursera', 'Python Programming, SQL, Cloud databases'),
           ('Excel Basics for Data Analysis', 'https://www.coursera.org/learn/excel-basics-data-analysis-ibm', 'IBM / Coursera', 'Data analysis, Pivot table'),
           ('Information Systems Specialization', 'https://www.coursera.org/specializations/information-systems', 'Coursera / University of Minnesota', 'Analysis for Business Systems, Enterprise Systems, IT Infrastructure, IS/IT Governance'),
           ('Machine Learning Specialization', 'https://www.coursera.org/specializations/machine-learning-introduction', 'Stanford / DeepLearning.AI', 'Logistic regression, Artificial Neural Network, Linear Regression, Decision Trees'),
           ('Machine Learning with Python Foundations', 'https://www.linkedin.com/learning/machine-learning-with-python-foundations', 'LinkedIn', 'Step-by-step guidance for machine learning using Python'),
           ('Python for Data Science, AI & Development', 'https://www.coursera.org/learn/python-for-applied-data-science-ai', 'IBM / Coursera', 'Python Programming, Panda, Numpy')
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
                                              'https://www.coursera.org/learn/data-analysis-with-python',
                                              'https://www.coursera.org/learn/ibm-data-analyst-capstone-project',
                                              'https://www.coursera.org/professional-certificates/ibm-data-analyst',
                                              'https://www.coursera.org/learn/data-visualization-dashboards-excel-cognos',
                                              'https://www.coursera.org/learn/sql-data-science',
                                              'https://www.coursera.org/learn/excel-basics-data-analysis-ibm',
                                              'https://www.coursera.org/specializations/information-systems',
                                              'https://www.coursera.org/specializations/machine-learning-introduction',
                                              'https://www.linkedin.com/learning/machine-learning-with-python-foundations',
                                              'https://www.coursera.org/learn/python-for-applied-data-science-ai'
    )
WHERE jr.title = 'Business Systems Analyst'
  AND jr.pathwayId = (SELECT pathway_id FROM [dbo].[pathways] WHERE pathway_title = 'Business and Management');

COMMIT TRAN;

-------------------------------
-- Block 5: Job-Specific Training Records for "Customer Service Representative"
-------------------------------
BEGIN TRAN;

MERGE [dbo].[Training] AS target
USING (VALUES
           ('Advance Your Data Privacy Skills', 'https://www.linkedin.com/learning/paths/advance-your-data-privacy-skills', 'LinkedIn', 'Data Privacy'),
           ('AI in Customer Service (FEE)', 'https://www.udemy.com/course/ai-in-customer-service/', 'Udemy', 'Customer Service, integrating AI solutions'),
           ('Customer Service', 'https://skillsbuild.org/adult-learners/explore-learning/customer-service-representative', 'IBM', 'Customer engagement, problem solving and process controls'),
           ('Data Analyst Capstone Project', 'https://www.coursera.org/learn/ibm-data-analyst-capstone-project', 'IBM / Coursera', 'Data Analyst, Python Programming, Dashboard, Data visualization, SQL and RDBMS'),
           ('Data Analyst Certificate', 'https://www.coursera.org/professional-certificates/google-data-analytics', 'Google / Coursera', 'Data analysis, data visualization, Data driven decision making, Data-driven insights Responsible AI'),
           ('Introduction to Cybersecurity', 'https://skillsforall.com/course/introduction-to-cybersecurity', 'Cisco', 'Cybersecurity'),
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
                                              'https://www.linkedin.com/learning/paths/advance-your-data-privacy-skills',
                                              'https://www.udemy.com/course/ai-in-customer-service/',
                                              'https://skillsbuild.org/adult-learners/explore-learning/customer-service-representative',
                                              'https://www.coursera.org/learn/ibm-data-analyst-capstone-project',
                                              'https://www.coursera.org/professional-certificates/google-data-analytics',
                                              'https://skillsforall.com/course/introduction-to-cybersecurity',
                                              'https://www.coursera.org/specializations/machine-learning-introduction'
    )
WHERE jr.title = 'Customer Service Representative'
  AND jr.jobLevel = 'Entry level'
  AND jr.pathwayId = (SELECT pathway_id FROM [dbo].[pathways] WHERE pathway_title = 'Business and Management');

COMMIT TRAN;

-------------------------------
-- Block 6: Job-Specific Training Records for "Digital Marketing Specialist"
-------------------------------
BEGIN TRAN;

MERGE [dbo].[Training] AS target
USING (VALUES
           ('Customer Service', 'https://skillsbuild.org/adult-learners/explore-learning/customer-service-representative', 'IBM', 'Customer engagement, problem solving and process controls'),
           ('Digital Marketing and Ecommerce Certificate', 'https://www.coursera.org/professional-certificates/google-digital-marketing-ecommerce', 'Google / Coursera', 'SEO, e-commerce, email marketing, Marketing')
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
                                              'https://skillsbuild.org/adult-learners/explore-learning/customer-service-representative',
                                              'https://www.coursera.org/professional-certificates/google-digital-marketing-ecommerce'
    )
WHERE jr.title = 'Digital Marketing Specialist'
  AND jr.jobLevel = 'Mid-level'
  AND jr.pathwayId = (SELECT pathway_id FROM [dbo].[pathways] WHERE pathway_title = 'Business and Management');

COMMIT TRAN;

-------------------------------
-- Block 7: Job-Specific Training Records for "Product Manager"
-------------------------------
BEGIN TRAN;

MERGE [dbo].[Training] AS target
USING (VALUES
           ('AI Product Manager Professional Certificate', 'https://www.coursera.org/professional-certificates/ibm-ai-product-manager', 'IBM / Coursera', 'Artificial intelligence, Product management, AI product manager, Prompt engineering'),
           ('Data Analyst Certificate', 'https://www.coursera.org/professional-certificates/google-data-analytics', 'Google / Coursera', 'Data analysis, data visualization, Data driven decision making, Data-driven insights Responsible AI'),
           ('Data Analyst Professional Certificate', 'https://www.coursera.org/professional-certificates/ibm-data-analyst', 'IBM / Coursera', 'Data Analyst, Python Programming, Dashboard, Data visualization, SQL and RDBMS'),
           ('User Experience Design', 'https://skillsbuild.org/adult-learners/explore-learning/user-experience-design', 'IBM', 'User-centered digital products, Product Design, User engagement')
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
                                              'https://www.coursera.org/professional-certificates/ibm-ai-product-manager',
                                              'https://www.coursera.org/professional-certificates/google-data-analytics',
                                              'https://www.coursera.org/professional-certificates/ibm-data-analyst',
                                              'https://skillsbuild.org/adult-learners/explore-learning/user-experience-design'
    )
WHERE jr.title = 'Product Manager'
  AND jr.pathwayId = (SELECT pathway_id FROM [dbo].[pathways] WHERE pathway_title = 'Business and Management');

COMMIT TRAN;

-------------------------------
-- Block 8: Job-Specific Training Records for "Project Manager"
-------------------------------
BEGIN TRAN;

MERGE [dbo].[Training] AS target
USING (VALUES
           ('Artificial Intelligence Online Community (Resource)', 'https://www.projectmanagement.com/topics/artificial-intelligence/', 'Project Management Institute', 'Artificial intelligence'),
           ('Project Management Certificate', 'https://www.coursera.org/professional-certificates/google-project-management', 'Google / Coursera', 'Agile Management, Change Management, Data analysis, Project management, Project planning and developing, Problem Solving and Project risk management, Strategic thinking'),
           ('Project Manager', 'https://skillsbuild.org/adult-learners/explore-learning/project-manager', 'IBM', 'Project management, Project planning and developing, Problem Solving and Project risk management'),
           ('Project Manager Professional Certificate', 'https://www.coursera.org/professional-certificates/ibm-project-manager', 'IBM / Coursera', 'Developing project timelines, roles and responsibility matrices, stakeholder management tools, and communications plans'),
           ('Talking to AI: Prompt Engineering for Project Managers (FEE)', 'https://www.pmi.org/shop/p-/elearning/talking-to-ai-prompt-engineering-for-project-managers/el128', 'Project Management Institute', 'Prompt engineering for project managers, AI readiness')
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
                                              'https://www.projectmanagement.com/topics/artificial-intelligence/',
                                              'https://www.coursera.org/professional-certificates/google-project-management',
                                              'https://skillsbuild.org/adult-learners/explore-learning/project-manager',
                                              'https://www.coursera.org/professional-certificates/ibm-project-manager',
                                              'https://www.pmi.org/shop/p-/elearning/talking-to-ai-prompt-engineering-for-project-managers/el128'
    )
WHERE jr.title = 'Project Manager'
  AND jr.jobLevel = 'Mid-level'
  AND jr.pathwayId = (SELECT pathway_id FROM [dbo].[pathways] WHERE pathway_title = 'Business and Management');

COMMIT TRAN;

-------------------------------
-- Block 9: Job-Specific Training Records for "Senior Product Manager"
-------------------------------
BEGIN TRAN;

MERGE [dbo].[Training] AS target
USING (VALUES
           ('AI Product Manager Professional Certificate', 'https://www.coursera.org/professional-certificates/ibm-ai-product-manager', 'IBM / Coursera', 'Artificial intelligence, Product management, AI product manager, Prompt engineering'),
           ('Data Analyst Certificate', 'https://www.coursera.org/professional-certificates/google-data-analytics', 'Google / Coursera', 'Data analysis, data visualization, Data driven decision making, Data-driven insights Responsible AI'),
           ('Data Analyst Professional Certificate', 'https://www.coursera.org/professional-certificates/ibm-data-analyst', 'IBM / Coursera', 'Data Analyst, Python Programming, Dashboard, Data visualization, SQL and RDBMS'),
           ('Learning Jira', 'https://www.linkedin.com/learning/learning-jira-cloud-edition-19890900', 'LinkedIn', 'Jira'),
           ('User Experience Design', 'https://skillsbuild.org/adult-learners/explore-learning/user-experience-design', 'IBM', 'Design user-centered digital products, Product Design, User Experience')
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
                                              'https://www.coursera.org/professional-certificates/ibm-ai-product-manager',
                                              'https://www.coursera.org/professional-certificates/google-data-analytics',
                                              'https://www.coursera.org/professional-certificates/ibm-data-analyst',
                                              'https://www.linkedin.com/learning/learning-jira-cloud-edition-19890900',
                                              'https://skillsbuild.org/adult-learners/explore-learning/user-experience-design'
    )
WHERE jr.title = 'Senior Product Manager'
  AND jr.jobLevel = 'Senior level'
  AND jr.pathwayId = (SELECT pathway_id FROM [dbo].[pathways] WHERE pathway_title = 'Business and Management');

COMMIT TRAN;
