-------------------------------
-- Block 1.1: Foundational Trainings for "Infrastructure and Operations" Job Group
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
           ('Building Career Agility and Resilience in the Age of AI', 'https://www.linkedin.com/learning/building-career-agility-and-resilience-in-the-age-of-ai/prepare-for-your-ai-enhanced-career?u=104', 'LinkedIn', 'AI technologies skills to develop a “future-proof career mindset”'),
           ('Career Management Essentials', 'https://ibm.biz/BdGpZT', 'IBM', 'Career development, Career management, Communication skills, Generative AI tool use, Networking skills, Presentation skills, Professional interviewing skills, Professional online brand development, Resume writing, Socialmedia presence, Workplace research'),
           ('Creating compelling Reports', 'https://skillsforall.com/course/compelling-reports', 'Cisco', 'Communication, presentation'),
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
           ('Introduction to Retrieval Augmented Generation (RAG)', 'https://u.cisco.com/tutorials/5353', 'Cisco U', 'Retrieval-augmented Generation'),
           ('Introduction to Retrieval Augmented Generation (RAG) (FEE)', 'https://www.coursera.org/projects/introduction-to-rag', 'Duke University / Coursera', 'Python programming, machine learning, retrieval augmented generation, large language models'),
           ('Responsible AI Foundations', 'https://www.linkedin.com/learning/paths/responsible-ai-foundations', 'LinkedIn', 'Ethical and Responsible AI, AI ethics and governance'),
           ('Working in a Digital World: Professional Skills', 'https://www.credly.com/org/ibm-skillsbuild/badge/working-in-a-digital-world-professional-skills', 'IBM', 'Agile methodologies, business acumen, creative thinking, critical thinking, communication, problem solving, solutioning')
) AS source(title, url, provider, skillsDeveloped)
ON target.url = source.url
WHEN NOT MATCHED THEN
    INSERT (id, title, url, provider, skillsDeveloped)
    VALUES (NEWID(), source.title, source.url, source.provider, source.skillsDeveloped);

COMMIT TRAN;

-------------------------------
-- Block 1.2: Link Trainings to "Infrastructure and Operations" Job Group
-------------------------------
BEGIN TRAN;

INSERT INTO [dbo].[PathwayTraining] (id, pathwayId, trainingId)
SELECT NEWID(), p.pathway_id, t.id
FROM [dbo].[pathways] p
         JOIN [dbo].[Training] t ON t.url IN (
                                              'https://ibm.biz/BdGpZ8',
                                              'https://a16z.com/ai-canon/',
                                              'https://academy.aiskills.eu/course/ai-ecosystem-overview',
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
                                              'https://academy.aiskills.eu/course/1-introduction-to-artificial-intelligence',
                                              'https://www.coursera.org/learn/introduction-to-data-analytics',
                                              'https://skillsforall.com/course/introduction-to-modern-ai?courseLang=en-US',
                                              'https://www.edx.org/learn/artificial-intelligence/ibm-introduction-to-prompt-engineering',
                                              'https://www.netacad.com/modules/introduction-to-responsible-ai-skills?courseLang=en-US',
                                              'https://u.cisco.com/tutorials/5353',
                                              'https://www.coursera.org/projects/introduction-to-rag',
                                              'https://www.linkedin.com/learning/paths/responsible-ai-foundations',
                                              'https://www.credly.com/org/ibm-skillsbuild/badge/working-in-a-digital-world-professional-skills'
    )
WHERE p.pathway_title = 'Infrastructure and Operations';

COMMIT TRAN;

-------------------------------
-- Block 2.1: Job-Specific Trainings for "Database Administrator"
-------------------------------
BEGIN TRAN;

MERGE [dbo].[Training] AS target
USING (VALUES
           ('AI Security Nuggets', 'https://www.netacad.com/modules/ai-security-nuggets?courseLang=en-US', 'Cisco', 'AI regulations, AI threat modeling, AI supply chain, Retrieval Augmented Generation (RAG), LLM stack'),
           ('How to Master Database Troubleshooting', 'https://www.linkedin.com/learning/how-to-master-database-troubleshooting', 'LinkedIn', 'Database troubleshooting'),
           ('Introduction to Networking and Cloud Computing', 'https://www.coursera.org/learn/introduction-to-networking-and-cloud-computing', 'Microsoft / Coursera', 'Cloud computing, Network Monitoring, Network Security, Computer Network'),
           ('Machine Learning Specialization', 'https://www.coursera.org/specializations/machine-learning-introduction', 'Stanford / DeepLearning.AI', 'Logistic regression, Artificial Neural Network, Linear Regression, Decision Trees'),
           ('Securing the Use of Generative AI in Your Organization', 'https://www.linkedin.com/learning/securing-the-use-of-generative-ai-in-your-organization/introduction-to-generative-ai?u=104', 'LinkedIn', 'Generative AI risk management, AI governance, LLM security, safeguarding sensitive information, digital resilience, compliance frameworks, mitigating attacks, cybersecurity, GRC policies, AI ethics'),
           ('SQL Server Machine Learning Services with Python', 'https://www.linkedin.com/learning/sql-server-machine-learning-services-python/analyze-sql-server-data-with-python?u=104', 'LinkedIn', 'SQL Server analytics, Python scripting for machine learning, standalone ML services, Python-based dashboards and visualizations, executing scripts without impacting SQL Server'),
           ('Training Neural Networks in Python', 'https://www.linkedin.com/learning/training-neural-networks-in-python-17058600/creating-a-neural-network-in-python?u=104', 'LinkedIn', 'Python for neural networks, algorithm design, neural architectures, network evaluation and tuning, model selection, neural training strategy, AI frameworks and solutions')
) AS source(title, url, provider, skillsDeveloped)
ON target.url = source.url
WHEN NOT MATCHED THEN
    INSERT (id, title, url, provider, skillsDeveloped)
    VALUES (NEWID(), source.title, source.url, source.provider, source.skillsDeveloped);

COMMIT TRAN;

-------------------------------
-- Block 2.2: Link Trainings to "Database Administrator" Job Role
-------------------------------
BEGIN TRAN;

INSERT INTO [dbo].[JobRoleTraining] (id, jobRoleId, trainingId)
SELECT NEWID(), jr.id, t.id
FROM [dbo].[JobRole] jr
         JOIN [dbo].[Training] t ON t.url IN (
                                              'https://www.netacad.com/modules/ai-security-nuggets?courseLang=en-US',
                                              'https://www.linkedin.com/learning/how-to-master-database-troubleshooting',
                                              'https://www.coursera.org/learn/introduction-to-networking-and-cloud-computing',
                                              'https://www.coursera.org/specializations/machine-learning-introduction',
                                              'https://www.linkedin.com/learning/securing-the-use-of-generative-ai-in-your-organization/introduction-to-generative-ai?u=104',
                                              'https://www.linkedin.com/learning/sql-server-machine-learning-services-python/analyze-sql-server-data-with-python?u=104',
                                              'https://www.linkedin.com/learning/training-neural-networks-in-python-17058600/creating-a-neural-network-in-python?u=104'
    )
WHERE jr.title = 'Database Administrator'
  AND jr.pathwayId = (SELECT pathway_id FROM [dbo].[pathways] WHERE pathway_title = 'Infrastructure and Operations');

COMMIT TRAN;

-------------------------------
-- Block 2.1: Job-Specific Trainings for "Help Desk Analyst"
-------------------------------
BEGIN TRAN;

MERGE [dbo].[Training] AS target
USING (VALUES
           ('Customer Service', 'https://skillsbuild.org/adult-learners/explore-learning/customer-service-representative', 'IBM', 'Customer engagement, problem solving, process controls'),
           ('IT Essentials (*)', 'https://www.netacad.com/courses/it-essentials?courseLang=en-US', 'Cisco', 'Help Desk Support, Customer Service'),
           ('IT Help Desk for Beginner', 'https://www.linkedin.com/learning/it-help-desk-for-beginners-22349140/', 'LinkedIn', 'Customer Service, Help Desk Support, troubleshooting, incident response'),
           ('Network Technician Career path', 'https://skillsforall.com/career-path/network-technician?courseLang=en-US', 'Cisco', 'System Administration, Operating Systems (Linux, Windows 10), LANs, TCP/IP, Technical Support, Cybersecurity')
) AS source(title, url, provider, skillsDeveloped)
ON target.url = source.url
WHEN NOT MATCHED THEN
    INSERT (id, title, url, provider, skillsDeveloped)
    VALUES (NEWID(), source.title, source.url, source.provider, source.skillsDeveloped);

COMMIT TRAN;

-------------------------------
-- Block 2.2: Link Trainings to "Help Desk Analyst" Job Role
-------------------------------
BEGIN TRAN;

INSERT INTO [dbo].[JobRoleTraining] (id, jobRoleId, trainingId)
SELECT NEWID(), jr.id, t.id
FROM [dbo].[JobRole] jr
         JOIN [dbo].[Training] t ON t.url IN (
                                              'https://skillsbuild.org/adult-learners/explore-learning/customer-service-representative',
                                              'https://www.netacad.com/courses/it-essentials?courseLang=en-US',
                                              'https://www.linkedin.com/learning/it-help-desk-for-beginners-22349140/',
                                              'https://skillsforall.com/career-path/network-technician?courseLang=en-US'
    )
WHERE jr.title = 'Help Desk Analyst'
  AND jr.pathwayId = (SELECT pathway_id FROM [dbo].[pathways] WHERE pathway_title = 'Infrastructure and Operations');

COMMIT TRAN;

-------------------------------
-- Block 3.1: Job-Specific Trainings for "IT Manager"
-------------------------------
BEGIN TRAN;

MERGE [dbo].[Training] AS target
USING (VALUES
           ('Azure OpenAI: Generative AI Models and How to Use Them', 'https://www.linkedin.com/learning/azure-openai-generative-ai-models-and-how-to-use-them/welcome?u=104', 'LinkedIn', 'Azure OpenAI, GPT models, embedding models, DALL-E models, copyright use, model combination, OpenAI services'),
           ('Data Engineering Pipeline Management with Apache Airflow (FEE)', 'https://www.linkedin.com/learning/data-engineering-pipeline-management-with-apache-airflow', 'LinkedIn', 'Role-based access control, DAG execution, SLA management, plugin usage, pipeline scheduling, CSV plugins, Apache Airflow fundamentals'),
           ('Prepare for the AWS Certified Machine Learning Specialty (MLS-C01)', 'https://www.linkedin.com/learning/paths/prepare-for-the-aws-certified-machine-learning-specialty-mls-c01-exam?u=104', 'LinkedIn', 'AWS Machine Learning Specialty preparation, building/training/tuning ML models, certification mapping, ML concept expansion, AWS ML tools'),
           ('Prepare for the Google Cloud Professional Machine Learning Engineer Certification', 'https://www.linkedin.com/learning/paths/prepare-for-the-google-cloud-professional-machine-learning-engineer-certification?u=104', 'LinkedIn', 'Google Cloud ML Engineer preparation, GCP tools and technologies, ML models for business problems, certification alignment, Google Vertex AI'),
           ('Securing the Use of Generative AI in Your Organization', 'https://www.linkedin.com/learning/securing-the-use-of-generative-ai-in-your-organization/introduction-to-generative-ai?u=104', 'LinkedIn', 'Generative AI governance, AI security, GRC policies, mitigating generative AI risks, LLM security, digital resilience, AI ethics')
) AS source(title, url, provider, skillsDeveloped)
ON target.url = source.url
WHEN NOT MATCHED THEN
    INSERT (id, title, url, provider, skillsDeveloped)
    VALUES (NEWID(), source.title, source.url, source.provider, source.skillsDeveloped);

COMMIT TRAN;

-------------------------------
-- Block 3.2: Link Trainings to "IT Manager" Job Role
-------------------------------
BEGIN TRAN;

INSERT INTO [dbo].[JobRoleTraining] (id, jobRoleId, trainingId)
SELECT NEWID(), jr.id, t.id
FROM [dbo].[JobRole] jr
         JOIN [dbo].[Training] t ON t.url IN (
                                              'https://www.linkedin.com/learning/azure-openai-generative-ai-models-and-how-to-use-them/welcome?u=104',
                                              'https://www.linkedin.com/learning/data-engineering-pipeline-management-with-apache-airflow',
                                              'https://www.linkedin.com/learning/paths/prepare-for-the-aws-certified-machine-learning-specialty-mls-c01-exam?u=104',
                                              'https://www.linkedin.com/learning/paths/prepare-for-the-google-cloud-professional-machine-learning-engineer-certification?u=104',
                                              'https://www.linkedin.com/learning/securing-the-use-of-generative-ai-in-your-organization/introduction-to-generative-ai?u=104'
    )
WHERE jr.title = 'IT Manager'
  AND jr.pathwayId = (SELECT pathway_id FROM [dbo].[pathways] WHERE pathway_title = 'Infrastructure and Operations');

COMMIT TRAN;

-------------------------------
-- Block 4.1: Job-Specific Trainings for "IT Support Technician"
-------------------------------
BEGIN TRAN;

MERGE [dbo].[Training] AS target
USING (VALUES
           ('Cloud Computing and Virtualization', 'https://skills.yourlearning.ibm.com/credential/CREDLY-1261b7bb-becb-431f-bb1f-36097dac3419', 'IBM', 'Cloud computing; virtualization'),
           ('Customer Service', 'https://skillsbuild.org/adult-learners/explore-learning/customer-service-representative', 'IBM', 'Customer engagement, problem solving, process controls'),
           ('Foundations of Project Management', 'https://www.coursera.org/learn/project-management-foundations', 'Google / Coursera', 'Project management'),
           ('IT Essentials (*)', 'https://www.netacad.com/courses/it-essentials?courseLang=en-US', 'Cisco', 'Help Desk Support, Customer Service'),
           ('IT Help Desk for Beginner', 'https://www.linkedin.com/learning/it-help-desk-for-beginners-22349140/', 'LinkedIn', 'Customer Service, Help Desk Support, troubleshooting, incident response'),
           ('IT Security and Compliance', 'https://skills.yourlearning.ibm.com/credential/CREDLY-2cd487a5-7bfa-4434-a24c-11bb3eecba8d', 'IBM', 'Security'),
           ('IT Support Certificate', 'https://www.coursera.org/professional-certificates/ibm-technical-support', 'IBM / Coursera', 'Computer assembly, wireless networking, installing programs, customer service'),
           ('IT Support Technician Certificate', 'https://skills.yourlearning.ibm.com/activity/PLAN-65C0754E684D', 'IBM', 'Computer assembly, wireless networking, installing programs, customer service'),
           ('Network Technician Career path', 'https://skillsforall.com/career-path/network-technician?courseLang=en-US', 'Cisco', 'System Administration, Operating Systems (Linux, Windows 10), LANs, TCP/IP, Technical Support, Cybersecurity'),
           ('Software and Operating Systems', 'https://skills.yourlearning.ibm.com/credential/CREDLY-5835479c-bc29-431f-af4d-60e3bee1d7de', 'IBM', 'Troubleshooting software/OS, configure settings, update/install software, diagnose issues, select tools for support, perform user management tasks')
) AS source(title, url, provider, skillsDeveloped)
ON target.url = source.url
WHEN NOT MATCHED THEN
    INSERT (id, title, url, provider, skillsDeveloped)
    VALUES (NEWID(), source.title, source.url, source.provider, source.skillsDeveloped);

COMMIT TRAN;

-------------------------------
-- Block 4.2: Link Trainings to "IT Support Technician" Job Role
-------------------------------
BEGIN TRAN;

INSERT INTO [dbo].[JobRoleTraining] (id, jobRoleId, trainingId)
SELECT NEWID(), jr.id, t.id
FROM [dbo].[JobRole] jr
         JOIN [dbo].[Training] t ON t.url IN (
                                              'https://skills.yourlearning.ibm.com/credential/CREDLY-1261b7bb-becb-431f-bb1f-36097dac3419',
                                              'https://skillsbuild.org/adult-learners/explore-learning/customer-service-representative',
                                              'https://www.coursera.org/learn/project-management-foundations',
                                              'https://www.netacad.com/courses/it-essentials?courseLang=en-US',
                                              'https://www.linkedin.com/learning/it-help-desk-for-beginners-22349140/',
                                              'https://skills.yourlearning.ibm.com/credential/CREDLY-2cd487a5-7bfa-4434-a24c-11bb3eecba8d',
                                              'https://www.coursera.org/professional-certificates/ibm-technical-support',
                                              'https://skills.yourlearning.ibm.com/activity/PLAN-65C0754E684D',
                                              'https://skillsforall.com/career-path/network-technician?courseLang=en-US',
                                              'https://skills.yourlearning.ibm.com/credential/CREDLY-5835479c-bc29-431f-af4d-60e3bee1d7de'
    )
WHERE jr.title = 'IT Support Technician'
  AND jr.pathwayId = (SELECT pathway_id FROM [dbo].[pathways] WHERE pathway_title = 'Infrastructure and Operations');

COMMIT TRAN;

-------------------------------
-- Block 5.1: Job-Specific Trainings for "Network Administrator"
-------------------------------
BEGIN TRAN;

MERGE [dbo].[Training] AS target
USING (VALUES
           ('CCNA: Enterprise Networking, Security, and Automation (*)', 'https://www.netacad.com/courses/networking/ccna-enterprise-networking-security-automation', 'Cisco', 'Dynamic Routing, Network Address Translation (NAT), Network Automation Basics, Basic OSPF, Quality of Service (QoS), Security Threat Mitigation, Software Driven Networks, Virtualization, Wide Area Networks'),
           ('CCNA: Introduction to Networks (*)', 'https://www.netacad.com/courses/networking/ccna-introduction-networks', 'Cisco', 'Ethernet, IP connectivity, IP services, IP Subnetting, IPv4 and IPv6, Addressing, Network Fundamentals, Security Fundamentals'),
           ('CCNA: Switching, Routing, and Wireless Essentials (*)', 'https://www.netacad.com/courses/networking/ccna-switching-routing-wireless-essentials', 'Cisco', 'Access Connectivity, Access Security, First-hop Redundancy, High Availability, IP services, Routing Switching Protocols, Wireless LAN Controllers'),
           ('Implementing and Administering Cisco Solutions | CCNA (FEE)', 'https://u.cisco.com/paths/implementing-administering-cisco-solutions-248', 'Cisco', 'Install, operate, configure, and verify basic IPv4 and IPv6 networks; configure switches, routers, and wireless LAN controllers; manage devices, identify security threats; automation, software-defined networking')
) AS source(title, url, provider, skillsDeveloped)
ON target.url = source.url
WHEN NOT MATCHED THEN
    INSERT (id, title, url, provider, skillsDeveloped)
    VALUES (NEWID(), source.title, source.url, source.provider, source.skillsDeveloped);

COMMIT TRAN;

-------------------------------
-- Block 5.2: Link Trainings to "Network Administrator" Job Role
-------------------------------
BEGIN TRAN;

INSERT INTO [dbo].[JobRoleTraining] (id, jobRoleId, trainingId)
SELECT NEWID(), jr.id, t.id
FROM [dbo].[JobRole] jr
         JOIN [dbo].[Training] t ON t.url IN (
                                              'https://www.netacad.com/courses/networking/ccna-enterprise-networking-security-automation',
                                              'https://www.netacad.com/courses/networking/ccna-introduction-networks',
                                              'https://www.netacad.com/courses/networking/ccna-switching-routing-wireless-essentials',
                                              'https://u.cisco.com/paths/implementing-administering-cisco-solutions-248'
    )
WHERE jr.title = 'Network Administrator'
  AND jr.pathwayId = (SELECT pathway_id FROM [dbo].[pathways] WHERE pathway_title = 'Infrastructure and Operations');

COMMIT TRAN;

-------------------------------
-- Block 6.1: Job-Specific Trainings for "Network and IT Automation Engineer"
-------------------------------
BEGIN TRAN;

MERGE [dbo].[Training] AS target
USING (VALUES
           ('DevNet Associate (*)', 'https://www.netacad.com/courses/devnet-associate?courseLang=en-US', 'Cisco', 'Application Deployment, Applications, Application Security, Automation, Cisco Platforms, Cisco Development, Cloud, DevOps, IoT, Python, Software Design, etc.'),
           ('Introduction to Retrieval Augmented Generation (RAG)', 'https://u.cisco.com/tutorials/5353', 'Cisco U', 'Retrieval-augmented Generation')
) AS source(title, url, provider, skillsDeveloped)
ON target.url = source.url
WHEN NOT MATCHED THEN
    INSERT (id, title, url, provider, skillsDeveloped)
    VALUES (NEWID(), source.title, source.url, source.provider, source.skillsDeveloped);

COMMIT TRAN;

-------------------------------
-- Block 6.2: Link Trainings to "Network and IT Automation Engineer" Job Role
-------------------------------
BEGIN TRAN;

INSERT INTO [dbo].[JobRoleTraining] (id, jobRoleId, trainingId)
SELECT NEWID(), jr.id, t.id
FROM [dbo].[JobRole] jr
         JOIN [dbo].[Training] t ON t.url IN (
                                              'https://www.netacad.com/courses/devnet-associate?courseLang=en-US',
                                              'https://u.cisco.com/tutorials/5353'
    )
WHERE jr.title = 'Network and IT Automation Engineer'
  AND jr.pathwayId = (SELECT pathway_id FROM [dbo].[pathways] WHERE pathway_title = 'Infrastructure and Operations');

COMMIT TRAN;

-------------------------------
-- Block 7.1: Job-Specific Trainings for "Network Support Technician"
-------------------------------
BEGIN TRAN;

MERGE [dbo].[Training] AS target
USING (VALUES
           ('Customer Service', 'https://skillsbuild.org/adult-learners/explore-learning/customer-service-representative', 'IBM', 'Customer engagement, problem solving and process controls'),
           ('Network Technician Career path', 'https://skillsforall.com/career-path/network-technician?courseLang=en-US', 'Cisco', 'Application Layer Services, IPv4 Addresses, Network Media, Network Types, Protocols Standards, Wireless Access, ARP, Binary Systems, Cisco Devices, Cisco IOS, DHCP, DNS, Ethernet, Hierarchical Network Design, IPv4 Subnetting, IPv6, Help Desk, User support')
) AS source(title, url, provider, skillsDeveloped)
ON target.url = source.url
WHEN NOT MATCHED THEN
    INSERT (id, title, url, provider, skillsDeveloped)
    VALUES (NEWID(), source.title, source.url, source.provider, source.skillsDeveloped);

COMMIT TRAN;

-------------------------------
-- Block 7.2: Link Trainings to "Network Support Technician" Job Role
-------------------------------
BEGIN TRAN;

INSERT INTO [dbo].[JobRoleTraining] (id, jobRoleId, trainingId)
SELECT NEWID(), jr.id, t.id
FROM [dbo].[JobRole] jr
         JOIN [dbo].[Training] t ON t.url IN (
                                              'https://skillsbuild.org/adult-learners/explore-learning/customer-service-representative',
                                              'https://skillsforall.com/career-path/network-technician?courseLang=en-US'
    )
WHERE jr.title = 'Network Support Technician'
  AND jr.pathwayId = (SELECT pathway_id FROM [dbo].[pathways] WHERE pathway_title = 'Infrastructure and Operations');

COMMIT TRAN;

-------------------------------
-- Block 8.1: Job-Specific Trainings for "Senior Network Engineer"
-------------------------------
BEGIN TRAN;

MERGE [dbo].[Training] AS target
USING (VALUES
           ('Cisco Enterprise Network Core Technologies (FEE)', 'https://www.cisco.com/site/us/en/learn/training-certifications/training/courses/encor.html', 'Cisco', 'Network Engineering, Firewall, Network Management, Network Troubleshooting'),
           ('Designing Cisco Enterprise Networks (FEE)', 'https://www.cisco.com/c/en/us/training-events/training-certifications/training/training-services/courses/designing-cisco-enterprise-networks-ensld.html', 'Cisco', 'Network Infrastructure, Routing Protocols, Network Architecture'),
           ('Designing and Implementing Cloud Connectivity (FEE)', 'https://www.cisco.com/c/en/us/training-events/training-certifications/training/courses/encc.html', 'Cisco', 'Network Security, Network Monitoring, SD-WAN, QoS, Sustainability Practices, SASE, Cloud-Native Security, Digital Experience Assurance, Sustainability Metrics'),
           ('Implement Automation for Cisco Enterprise Solutions (FEE)', 'https://www.cisco.com/site/us/en/learn/training-certifications/training/courses/enaui.html', 'Cisco', 'Network Performance Management, Automation, Python (Programming Language), Scripting, AI/ML for Networking, Data Analytics, Network Telemetry')
) AS source(title, url, provider, skillsDeveloped)
ON target.url = source.url
WHEN NOT MATCHED THEN
    INSERT (id, title, url, provider, skillsDeveloped)
    VALUES (NEWID(), source.title, source.url, source.provider, source.skillsDeveloped);

COMMIT TRAN;

-------------------------------
-- Block 8.2: Link Trainings to "Senior Network Engineer" Job Role
-------------------------------
BEGIN TRAN;

INSERT INTO [dbo].[JobRoleTraining] (id, jobRoleId, trainingId)
SELECT NEWID(), jr.id, t.id
FROM [dbo].[JobRole] jr
         JOIN [dbo].[Training] t ON t.url IN (
                                              'https://www.cisco.com/site/us/en/learn/training-certifications/training/courses/encor.html',
                                              'https://www.cisco.com/c/en/us/training-events/training-certifications/training/training-services/courses/designing-cisco-enterprise-networks-ensld.html',
                                              'https://www.cisco.com/c/en/us/training-events/training-certifications/training/courses/encc.html',
                                              'https://www.cisco.com/site/us/en/learn/training-certifications/training/courses/enaui.html'
    )
WHERE jr.title = 'Senior Network Engineer'
  AND jr.pathwayId = (SELECT pathway_id FROM [dbo].[pathways] WHERE pathway_title = 'Infrastructure and Operations');

COMMIT TRAN;

-------------------------------
-- Block 9.1: Job-Specific Trainings for "Systems Administrator"
-------------------------------
BEGIN TRAN;

MERGE [dbo].[Training] AS target
USING (VALUES
           ('Cybersecurity Essentials', 'https://www.netacad.com/catalogs/learn/cybersecurity', 'Cisco', 'Cybersecurity literacy, Asset protection, Security response, Network protection, Product expertise, Data breach analysis, Data defense, Cybersecurity policies'),
           ('Cybersecurity Fundamentals', 'https://www.credly.com/org/ibm-skillsbuild/badge/cybersecurity-fundamentals', 'IBM', 'Cybersecurity literacy, Cryptography, Cyber Attacks, Cyber threat analysis, Cyber threat analysis intelligence, Cybersecurity risk management'),
           ('Network and System Administration Online Training Courses', 'https://www.linkedin.com/learning/topics/network-and-system-administration', 'LinkedIn', 'Azure Administration, Server Administration, Network Routing, Jira, Backup and Recovery, IT Architecture'),
           ('Network Technician Career path', 'https://skillsforall.com/career-path/network-technician?courseLang=en-US', 'Cisco', 'System Administration, Operating Systems (Linux, Windows 10), Local Area Networks (LANs), TCP/IP, Technical Support, Cybersecurity'),
           ('Python 3 for Scripting for System Administrators', 'https://www.pluralsight.com/courses/python-3-scripting-for-system-administrators', 'Pluralsight', 'Scripting (Python), System Administration, Technical Support'),
           ('System Administration and IT Infrastructure Service', 'https://www.coursera.org/learn/system-administration-it-infrastructure-services', 'Google / Coursera', 'System Administration, Operating Systems, Local Area Networks, Virtualization, Backup Devices, Disaster Recovery, Access Management, Technical Support, Cloud Service, Configuration Management')
) AS source(title, url, provider, skillsDeveloped)
ON target.url = source.url
WHEN NOT MATCHED THEN
    INSERT (id, title, url, provider, skillsDeveloped)
    VALUES (NEWID(), source.title, source.url, source.provider, source.skillsDeveloped);

COMMIT TRAN;

-------------------------------
-- Block 9.2: Link Trainings to "Systems Administrator" Job Role
-------------------------------
BEGIN TRAN;

INSERT INTO [dbo].[JobRoleTraining] (id, jobRoleId, trainingId)
SELECT NEWID(), jr.id, t.id
FROM [dbo].[JobRole] jr
         JOIN [dbo].[Training] t ON t.url IN (
                                              'https://www.netacad.com/catalogs/learn/cybersecurity',
                                              'https://www.credly.com/org/ibm-skillsbuild/badge/cybersecurity-fundamentals',
                                              'https://www.linkedin.com/learning/topics/network-and-system-administration',
                                              'https://skillsforall.com/career-path/network-technician?courseLang=en-US',
                                              'https://www.pluralsight.com/courses/python-3-scripting-for-system-administrators',
                                              'https://www.coursera.org/learn/system-administration-it-infrastructure-services'
    )
WHERE jr.title = 'Systems Administrator'
  AND jr.pathwayId = (SELECT pathway_id FROM [dbo].[pathways] WHERE pathway_title = 'Infrastructure and Operations');

COMMIT TRAN;

-------------------------------
-- Block 10.1: Job-Specific Trainings for "Systems Analyst"
-------------------------------
BEGIN TRAN;

MERGE [dbo].[Training] AS target
USING (VALUES
           ('AI and Developer Productivity', 'https://www.linkedin.com/learning/ai-and-developer-productivity/ai-and-developer-productivity?u=104', 'LinkedIn', 'Prompts, code optimization, automated testing, quality assurance, intelligent debugging, issue resolution, collaboration, documentation techniques, interview preparation, and more'),
           ('AI Powered Programming with GitHub CoPilot', 'https://www.linkedin.com/learning/ai-powered-programming-with-github-copilot-by-microsoft-press/welcome-and-course-overview?u=104', 'LinkedIn', 'GitHub Copilot usage, IDE integration, comment-based generation, Copilot in unit testing, GitHub CoPilot to build and deploy apps'),
           ('Data Engineering Pipeline Management with Apache Airflow', 'https://www.linkedin.com/learning/data-engineering-pipeline-management-with-apache-airflow', 'LinkedIn', 'DAG orchestration, SLAs, Airflow plugins, role-based access, pipeline execution, DAG types (branching & SQL), data transformation pipelines'),
           ('Data Management with Apache NiFi', 'https://www.linkedin.com/learning/data-engineering-pipeline-management-with-apache-airflow', 'LinkedIn', 'Apache NiFi architecture, flow building, PostgreSQL integration, Amazon S3, processors, dataflow configuration, back pressure, and NiFi monitoring'),
           ('Google Cloud Platform for Machine Learning', 'https://www.linkedin.com/learning/google-cloud-platform-for-machine-learning-essential-training-2024-revision/welcome?u=104', 'LinkedIn', 'Vertex AI, MLops, model training/evaluation, using Google Cloud Studio, deploying models, using Vertex AI APIs, mastering end-to-end MLops')
) AS source(title, url, provider, skillsDeveloped)
ON target.url = source.url
WHEN NOT MATCHED THEN
    INSERT (id, title, url, provider, skillsDeveloped)
    VALUES (NEWID(), source.title, source.url, source.provider, source.skillsDeveloped);

COMMIT TRAN;

-------------------------------
-- Block 10.2: Link Trainings to "Systems Analyst" Job Role
-------------------------------
BEGIN TRAN;

INSERT INTO [dbo].[JobRoleTraining] (id, jobRoleId, trainingId)
SELECT NEWID(), jr.id, t.id
FROM [dbo].[JobRole] jr
         JOIN [dbo].[Training] t ON t.url IN (
                                              'https://www.linkedin.com/learning/ai-and-developer-productivity/ai-and-developer-productivity?u=104',
                                              'https://www.linkedin.com/learning/ai-powered-programming-with-github-copilot-by-microsoft-press/welcome-and-course-overview?u=104',
                                              'https://www.linkedin.com/learning/data-engineering-pipeline-management-with-apache-airflow',
                                              'https://www.linkedin.com/learning/data-management-with-apache-nifi',
                                              'https://www.linkedin.com/learning/google-cloud-platform-for-machine-learning-essential-training-2024-revision/welcome?u=104'
    )
WHERE jr.title = 'Systems Analyst'
  AND jr.pathwayId = (SELECT pathway_id FROM [dbo].[pathways] WHERE pathway_title = 'Infrastructure and Operations');

COMMIT TRAN;
