BEGIN TRAN;

------------------------------------------------------------------
-- 1) INSERT PATHWAYS (AKA JOB GROUP FAMILIES)
------------------------------------------------------------------
WITH source (pathway_title, tooltip, description) AS (
    SELECT *
    FROM (VALUES ('Business and Management',
                  'Managing the development, business analysis and marketing of technology products and services.',
                  'The role of AI in Business and Management has undergone a profound evolution since IBM''s 1979 declaration that "A computer can never be held accountable; therefore, a computer must never make a management decision." Fast forward to today, while AI has made significant strides, human oversight remains paramount. AI today can help to create product strategies, provide predictive analytics, automate processes, develop reports, manage large-scale projects, and improve customer satisfaction. However, this reliance on AI necessitates robust contingency plans to mitigate risks associated with business decisions, system failures or technical glitches. The increasing integration of AI underscores the demand for skilled workers in the field. Organizations may encounter challenges in recruiting and retaining AI talent, highlighting the need for skill development initiatives. Despite AI''s capabilities, management decisions ultimately remain within the purview of human expertise and judgment, even as AI continues to reshape business operations.'),

                 ('Cybersecurity',
                  'Protecting systems, networks, and data from security breaches and cyberattacks.',
                  'With the advent of AI, the Cybersecurity job roles have witnessed transition, as 70% of Cybersecurity leaders (CISOs) believe AI gives the advantage to attackers over defenders. However, 35% of the CISOs are already experimenting with it for cyber defense, and 61% will likely use it in the next 12 months. Additionally, 86% of CISOs believe that Gen AI will help alleviate skills gaps and talent shortages on the security team. With the intervention of AI there has been an upgrade to the quality of work. Routine tasks such as log analysis and basic threat detection are being automated—potentially reducing time spent on entry-level tasks—while the right skillset can leverage AI to automate report generation and malware analysis.'),

                 ('Data Science',
                  'Analyzing and interpreting large sets of data to extract valuable insights.',
                  'Data science leverages advanced statistics and machine learning to tackle business and product challenges through a structured approach encompassing problem identification, data collection, exploration, cleaning, model building, iteration, and communication. In this evolving landscape, the integration of AI marks a transformative shift in business operations and decision-making. AI technologies like NLP, LLMs, Gen AI, and automated data processing have revolutionized data analysis with complex nonlinear correlations and advanced models. While AI enhances efficiency and accelerates data processing, it emphasizes the ongoing necessity of human expertise in interpreting results, validating outputs, and making strategic decisions.'),

                 ('Design and User Experience',
                  'Designing the user experience and interface.',
                  'Effective design hinges on understanding human needs and emotions. This user-centric approach is critical for creating products that resonate with users and achieve desired outcomes. The significance of Design and UX skills is underscored by the World Economic Forum''s Future of Jobs Report 2023, which identifies these skills as top priorities for reskilling and upskilling between 2023 and 2027. Although AI automates routine tasks within UX—streamlining workflows and facilitating data analysis—the human touch remains essential in creating empathetic, innovative designs.'),

                 ('Infrastructure and Operations',
                  'Managing and maintaining computer networks and IT infrastructure.',
                  'Infrastructure and Operations roles deploy, operate, and manage a company’s technology resources. AI is transforming these roles from human-dependent functions to smarter networks that manage configurations, troubleshoot issues, and adapt to changing demands. As per the IBM Global AI Adoption Index 2022, 33% of organizations use AI to automate IT processes—freeing up time for complex problem solving, strategic decision making, and stakeholder management.'),

                 ('Software Development',
                  'Designing, coding, testing, and maintaining software applications and systems.',
                  'Software Development is a crucial business element in an era of rapid digitization and evolving user needs. The role of AI in this sector has evolved from basic assistance to now helping developers design efficient and adaptive products. AI tools, including Gen AI and NLP, provide code suggestions, bug detection, and testing capabilities, ensuring developers have more time to focus on broader business requirements. A Gartner report suggests that by 2025, more than half of all software engineering leader role descriptions will explicitly require oversight of Gen AI.'),

                 ('Testing and Quality Assurance',
                  'Providing technical support and assistance to users through rigorous software testing and QA.',
                  'Testing and Quality Assurance (QA) workers are crucial for ensuring software reliability and functionality. They plan and execute tests rigorously to detect defects and collaborate with various teams to resolve issues. AI has transformed these roles through automated tools such as Selenium and Appium, enhancing accuracy and speed in defect identification. As AI continues to assume routine tasks like documentation and error detection, upskilling in AI-driven testing tools becomes imperative.')) AS source (pathway_title, tooltip, description)
    )

    MERGE INTO [dbo].[pathways] AS target
USING source
ON target.pathway_title = source.pathway_title

WHEN MATCHED THEN
    UPDATE SET tooltip = source.tooltip,
               description = source.description

WHEN NOT MATCHED BY TARGET THEN
    INSERT (pathway_id, pathway_title, tooltip, description)
    VALUES (NEWID(), source.pathway_title, source.tooltip, source.description);

------------------------------------------------------------------
-- 2) INSERT JOB ROLES WITH DETAILED JOB LEVELS
------------------------------------------------------------------

-- BUSINESS AND MANAGEMENT:
-- Entry level: Business Analyst, Business Intelligence Analyst, Business Systems Analyst, Customer Service Representative
-- Mid-level: Digital Marketing Specialist, Product Manager, Project Manager
-- Senior level: Senior Product Manager
INSERT INTO [dbo].[JobRole] (id, title, pathwayId, jobLevel, jobDescription, principalTasks, principalSkills, aiImpact,
                             keyInsights, aiTransformation)
SELECT NEWID(),
       'Business Analyst',
       p.pathway_id,
       'Entry level',
    -- jobDescription
    'Business Analyst identifies business opportunities through data analysis, recommends operational enhancements, and documents detailed requirements. They translate business needs into technical specifications, analyze and refine requirements for business systems and solutions, develop dashboards, and oversee data quality. Additionally, they conduct market research, manage project timelines, and lead change management initiatives for the smooth adoption of new processes and communicate and collaborate with stakeholders to address business needs.',
    -- principalTasks
    'Analyze business processes, workflows, data, and requirements~Analyze data using statistical methods~Conduct elicitation sessions with stakeholders to gather requirements~Coordinate with IT to improve data collection and analysis methods~Design and manage data analytics and reporting tools for business insights~Develop dashboards and visualizations for Key Performance Indicators (KPIs)~Document detailed business, functional, and system requirements~Ensure alignment with business objectives~Identify business issues and opportunities using the data analytics~Lead change management initiatives to ensure smooth adoption of new processes and systems across the organization~Model and map business processes and data flows~Oversee data governance and ensure data quality and consistency~Perform market research and competitive analysis to inform strategy, plan, execute, and oversee project timelines and deliverables~Recommend changes or enhancements to business operations based on findings from data analysis~Translate business needs into technical specifications for data projects',
    -- principalSkills
    'Communicate findings to stakeholders~Create and use statistical models~Critical thinking~Define and analyze business problems and reframe it as an analytic problem~Define key metrics for success~Design and evaluate experiments~Determine information, analysis, and data required to support decision making and answer the business problem~Develop a proposed set of drivers and relationships to outputs, assumptions and constraints~Explore, organize, clean, transform and visualize data using Microsoft Excel, SQL, and Tableau~Identify enhancements based on performance data~Identify sources, uses, and characteristics of a data set~Interpret results and draw meaningful conclusions~Manage and maintain data~Monitor performance of the solution against predefined KPIs using dashboards~Problem solving',
    -- aiImpact
    'AI tools are poised to drastically change the landscape of business analytics through automation, predictive analysis, and ever improving strategic insights. Larger and larger bodies of data will be processed and cleaned at drastically improved speeds, facilitating realtime analysis that will improve strategic decision making. AI tools will be able to assist in the structuring of data. Key factors for business analysts will involve data science and advanced math skills, natural language processing, and other core skills that form the foundation of AI proficiency', -- aiImpact,
    -- keyInsights
    'Automation: Many facets of business analysis are primed for automation, including data processing, cleaning, and initial analysis, with briefs and reports being created through a blend of data processing AI, like NLP and Gen AI tools~Decision making support: Deeper, more insightful analysis of larger bodies of data will be powered by AI tools, helping analysts produce more insightful recommendations around strategic considerations~Predictive analytics: Pattern recognition and other AI powered tools will allow business analysts to generate more accurate business forecasts further in advance~Strategic insight: As business analysts increasingly rely on AI tools to support their responsibilities, predictive analytics will offer better inferences from which to draw better strategic recommendations',
    -- aiTransformation
    'High'
FROM [dbo].[pathways] p
WHERE p.pathway_title = 'Business and Management';

INSERT INTO [dbo].[JobRole] (id, title, pathwayId, jobLevel, jobDescription, principalTasks, principalSkills, aiImpact,
                             keyInsights, aiTransformation)
SELECT NEWID(),
       'Business Intelligence Analyst',
       p.pathway_id,
       'Entry level',
       -- jobDescription
       'Business Intelligence Analysts are required to produce financial and market intelligence by querying data repositories and generating periodic reports. They devise methods for identifying data patterns and trends in available information sources to support decision making, monitor performance, and inform strategy.',
       -- principalTasks
       'Generate standard or custom reports summarizing business, financial, or economic data for review by executives, managers, clients, and other stakeholders~Synthesize current business intelligence or trend data to support recommendations for action~Maintain library of model documents, templates, or other reusable knowledge assets~Create business intelligence tools or systems, including design of related databases, spreadsheets, or outputs~Manage timely flow of business intelligence information to users~Collect business intelligence data from available industry reports, public information, field reports, or purchased sources~Analyze competitive market strategies through analysis of related product, market, or share trends~Maintain or update business intelligence tools, databases, dashboards, systems, or methods~Identify or monitor current and potential customers, using business intelligence tools~Disseminate information regarding tools, reports, or metadata enhancements~Provide technical support for existing reports, dashboards, or other tools~Identify and analyze industry or geographic trends with business strategy implications~Communicate with customers, competitors, suppliers, worker organizations, or others to stay abreast of industry or business trends~Create or review technical design documentation to ensure the accurate development of reporting solutions~Analyze technology trends to identify markets for future product development or to improve sales of existing products~Conduct or coordinate tests to ensure that intelligence is consistent with defined needs~Document specifications for business intelligence or information technology reports, dashboards, or other outputs',
       -- principalSkills
       'Agile methodology~Business intelligence~Business process~Business requirements~Computer science~Dashboard~Data analysis~Data modeling~Data science~Data visualization~Finance~Machine learning~Power BI~Project management~Python~R~SAP applications~SQL~Statistics~Tableau',
       -- aiImpact
       'Gen AI has the potential to have a high transformative impact on Business Intelligence (BI) Analysts. While their core analytical skills will remain essential, AI will automate many routine tasks, enabling BI Analysts to focus on higher-level insights and strategic decision-making. This shift could lead to an evolution of the BI Analyst role, with an emphasis on collaboration with AI tools and interpretation of AI-generated outputs',
       -- keyInsights
       'Automated data preparation and analysis: AI may allow to automate data cleaning, transformation, and basic analysis, freeing up analysts to focus on more complex tasks and insights~Enhanced pattern recognition and anomaly detection: AI algorithms may identify complex patterns and anomalies in large datasets faster and more accurately than humans, leading to more proactive decision-making~Natural language querying: Gen AI may allow users to interact with data using natural language, making BI tools more accessible to non-technical users and democratizing data insights~Automated report generation: AI may be able to generate reports, summaries, and visualizations based on user queries or predefined templates, saving analysts time and effort~Predictive analytics and forecasting: AI may be able to leverage machine learning to forecast future trends and outcomes, helping businesses make more informed decisions',
       -- aiTransformation
       'High'
FROM [dbo].[pathways] p
WHERE p.pathway_title = 'Business and Management';

INSERT INTO [dbo].[JobRole] (id, title, pathwayId, jobLevel, jobDescription, principalTasks, principalSkills, aiImpact,
                             keyInsights, aiTransformation)
SELECT NEWID(), 'Business Systems Analyst', p.pathway_id, 'Entry level',
       -- jobDescription
       '''Conduct organizational studies and evaluations, design systems and procedures, conduct work simplification and measurement studies, and prepare operations and procedures manuals to assist management in operating more efficiently and effectively. Includes program analysts and management consultants.',
       -- principalTasks
       'Gather and organize information on problems or procedures~
        Confer with personnel concerned to ensure successful functioning of newly implemented systems or procedures~
        Document the findings of the study and prepare recommendations for the implementation of new systems, procedures, or organizational changes~
        Plan study of work problems and procedures, such as organizational change, communications, information flow, integrated production methods, inventory control, or cost analysis~
        Interview personnel and conduct on-site observations to ascertain unit functions, work performed, and the methods, equipment, and personnel used~
        Prepare manuals and train workers in use of new forms, reports, procedures or equipment, according to organizational policy~
        Review forms and reports and confer with management and users about format, distribution, and purpose, identifying problems and improvements~
        Develop and implement records management program for filing, protection, and retrieval of records, and assure compliance with program~
        Design, evaluate, recommend, and approve changes of forms and reports~
        Recommend purchase of storage equipment and design area layout to locate equipment in space available',
       -- principalSkills
       'Agile methodology~Automation~Business analysis~Business operations~Business process~Business requirements~Business strategies~Change management~Data analysis~Finance~Key performance indicators~Management consulting~Process improvement~Project management~Python~Requirements elicitation~Scrum~SQL~User story~Workflow management',
       -- aiImpact
       'Gen AI has the potential to have a moderate transformative impact on Business Systems Analysts (BSA). While the core analysis, problem-solving, and consulting skills of BSAs remain vital, AI can significantly augment their capabilities and streamline many tasks. This shift may necessitate a recalibration of the BSA role, emphasizing the interpretation of AI-generated insights, effective communication, and strategic decision-making. In conclusion, Gen AI presents both challenges and opportunities for BSAs. By embracing AI as a powerful tool and developing the necessary skills, BSAs can advance the work they are already doing as strategic advisors, driving innovation and efficiency in their organizations.',
       -- keyInsights
       'Automated data analysis and report generation: AI may enable the rapid analysis of large datasets, pattern identification, and comprehensive report generation, saving BSAs significant time and effort and allowing them to focus on higher-level analysis and solution design~Enhanced process optimization: AI-powered tools may be able to model and simulate various scenarios, helping BSAs identify bottlenecks, inefficiencies, and opportunities for improvement in business processes~Intelligent recommendations: AI can analyze data to offer personalized recommendations for process improvements, resource allocation, and technology solutions, enhancing decision-making for both BSAs and management~Increased efficiency and productivity: Automating repetitive tasks and streamlining data analysis can significantly improve the speed and efficiency of BSAs'' work',
       -- aiTransformation
       'Moderate'
FROM [dbo].[pathways] p
WHERE p.pathway_title = 'Business and Management';

INSERT INTO [dbo].[JobRole] (id, title, pathwayId, jobLevel, jobDescription, principalTasks, principalSkills, aiImpact, keyInsights, aiTransformation)
SELECT NEWID(),
       'Customer Service Representative',
       p.pathway_id,
       'Entry level',
       -- jobDescription
       'Customer Service Representatives are highly skilled workers who collaborate with AI systems to deliver exceptional support. Their responsibilities include managing complex customer interactions, analyzing data to make informed decisions, and explaining AI-driven processes to customers. They must exhibit empathy, technical proficiency, and effective communication to foster trust and transparency.',
       -- principalTasks
       'Handle complex customer inquiries~Manage the company''s customer-facing chatbots~Provide emotional support to customers~Build relationships with customers~Handle customer escalations~Engage in continuous reskilling and upskilling',
       -- principalSkills
       'Active listening~Complex problem-solving~Conversationalist~Data analysis~Emotional intelligence~Empathy~Laws and regulations on data protection and privacy and security~Multitasking~Patience~Technical proficiency~Time management~Verbal and written communication',
       -- aiImpact
       'AI has transformed customer service by automating basic inquiries and enabling representatives to focus on higher-level concerns. Human CSRs remain crucial for managing complex interactions and ensuring emotional and contextual understanding. The integration of AI requires CSRs to adapt by developing skills to interact with AI systems and uphold security and privacy standards.',
       -- keyInsights
       'One-third of customers will use digital assistants to interact with customer service~Three-quarters of customers call customer service due to loneliness~AI allows faster and more accurate information retrieval and personalization~Data privacy and cybersecurity concerns are increasing~CSRs will need to learn to interact with machine customers and apply prompt engineering for AI tools',
       -- aiTransformation
       'High'
FROM [dbo].[pathways] p
WHERE p.pathway_title = 'Business and Management';


INSERT INTO [dbo].[JobRole] (id, title, pathwayId, jobLevel, jobDescription, principalTasks, principalSkills, aiImpact,
                             keyInsights, aiTransformation)
SELECT NEWID(),
       'Digital Marketing Specialist',
       p.pathway_id,
       'Mid-level',
       -- jobDescription
       'Digital Marketing Specialists plan, direct, or coordinate marketing policies and programs, such as determining the demand for products and services offered by a firm and its competitors and identify potential customers. They develop pricing strategies with the goal of maximizing the firm''s profits or share of the market while ensuring the firm''s customers are satisfied and oversee product development or monitor trends that indicate the need for new products and services.',
       -- principalTasks
       'Recommend modifications to products, packaging, production processes, or other characteristics to improve the environmental soundness or sustainability of products~Advise business or other groups on local, national, or international factors affecting the buying or selling of products or services~Select products or accessories to be displayed at trade or special production shows~Develop business cases for environmental marketing strategies~Integrate environmental information into product or company marketing strategies, policies, or activities~Identify, develop, or evaluate marketing strategy, based on knowledge of establishment objectives, market characteristics, and cost and markup factors~Formulate, direct, or coordinate marketing activities or policies to promote products or services, working with advertising or promotion managers~Evaluate the financial aspects of product development, such as budgets, expenditures, research and development appropriations, or return-on-investment and profit-loss projections~Develop pricing strategies, balancing firm objectives and customer satisfaction~Compile lists describing product or service offerings~Direct the hiring, training, or performance evaluations of marketing or sales staff and oversee their daily activities~Consult with product development personnel on product specifications, such as design, color, or packaging~Use sales forecasting or strategic planning to ensure the sale and profitability of products, lines, or services, analyzing business developments and monitoring market trends~Negotiate contracts with vendors or distributors to manage product distribution, establishing distribution networks or developing distribution strategies~Coordinate or participate in promotional activities or trade shows, working with developers, advertisers, or production managers, to market products or services~Initiate market research studies or analyze their findings~Confer with legal staff to resolve problems, such as copyright infringement or royalty sharing with outside producers or distributors~Consult with buying personnel to gain advice regarding the types of products or services expected to be in demand~Conduct economic or commercial surveys to identify potential markets for products or services',
       -- principalSkills
       'Business development~Communication~Customer relationship management~Customer service~Detail oriented~Digital marketing~Leadership~Management~Marketing~Microsoft office~Microsoft excel~Planning~Presentations~Problem solving~Project management~Research information~Sales~Self-motivation~Social media~Writing',
       -- aiImpact
       'Gen AI may have a transformative impact on Digital Marketing Specialists. By speeding up content creation, personalizing customer interactions, and providing data-driven insights, AI may fundamentally change how marketing strategies are conceived and executed. This technology may significantly enhance efficiency and open up new creative possibilities, which may also necessitate a shift in the skills required for success in this field. By understanding the potential impact of Gen AI and adapting their skillset accordingly, Digital Marketing Specialists can leverage this technology to revolutionize their strategies, achieve greater efficiency, and deliver more impactful results.',
       -- keyInsights
       'Enhanced content creation: AI can generate diverse marketing materials such as ad copy, social media posts, blog articles, and email campaigns, drastically reducing the time and resources required for content production~Data-driven decision making: AI-powered analytics may be able to identify patterns and trends in customer behavior, market conditions, and campaign performance, which may lead to more informed and effective decisions~Improved customer service: AI chatbots can handle routine customer inquiries, freeing up human agents to focus on complex issues and provide more personalized support~New creative opportunities: AI can generate novel ideas and concepts, sparking creativity and pushing the boundaries of traditional marketing approaches~Hyper-personalization: AI can analyze customer data to create highly personalized marketing messages and experiences, leading to increased engagement and conversion rates',
       -- aiTransformation
       'High'
FROM [dbo].[pathways] p
WHERE p.pathway_title = 'Business and Management';

INSERT INTO [dbo].[JobRole] (id, title, pathwayId, jobLevel, jobDescription, principalTasks, principalSkills, aiImpact,
                             keyInsights, aiTransformation)
SELECT NEWID(),
       'Product Manager',
       p.pathway_id,
       'Mid-level',
       -- jobDescription
       'A Product Manager leads the development and lifecycle of a product, defining vision, strategy, and roadmap. Responsibilities include market research, stakeholder collaboration, prioritizing features, ensuring alignment with business goals, and overseeing product launch and performance. Strong communication, analytical, and problem-solving skills are essential.',
       -- principalTasks
       'Coordinate and lead scrum meetings to ensure effective project management and collaboration~Manage software project lifecycles, from planning to delivery, ensuring milestones are met~Implement agile methodologies to adapt to changing requirements and improve team productivity~Oversee quality assurance processes to maintain product reliability and user satisfaction~Conduct data analysis to derive insights into user behavior and inform product decisions~Provide team leadership and guidance to foster a collaborative and productive work environment',
       -- principalSkills
       'Agile methodologies~Business intelligence~Competitive analysis~Data analysis~Problem solving~Process improvement~Product design~Scrum~SQL~Strategic planning~User acceptance testing~User experience',
       -- aiImpact
       'AI impact on the Product Manager role might be moderate. Product Managers might focus on upskilling skills like strategic planning and client relationship management. While skills in data analysis and quality assurance remain relevant, their demand for Product Managers will decline due to AI-assisted automation and optimization.',
       -- keyInsights
       'The Product Manager role involves strategic, analytical, and interpersonal tasks requiring human judgment, creativity, and interaction~Scrum and agile methodologies: AI can optimize workflows but lacks leadership capabilities (moderate impact)~Software project management: AI manages tasks and resources but can''t handle negotiation or decision-making in ambiguity (moderate impact)~SaaS integration: AI analyzes and recommends solutions but can''t assess strategic fit or negotiate terms (moderate impact)~Client relationship management: AI can interact and gather feedback but can''t build deep relationships (low impact)~Quality assurance and data analysis: AI excels in automation and analysis (high impact)~SQL and JavaScript: AI assists with coding but lacks complex problem-solving (high impact)~Team leadership and user experience: AI can''t lead or design holistic experiences (low to moderate impact)~Overall, AI can augment but not fully replace the human elements essential for success in this role',
       -- aiTransformation
       'Moderate'
FROM [dbo].[pathways] p
WHERE p.pathway_title = 'Business and Management';


INSERT INTO [dbo].[JobRole] (id, title, pathwayId, jobLevel, jobDescription, principalTasks, principalSkills, aiImpact,
                             keyInsights, aiTransformation)
SELECT NEWID(),
       'Project Manager',
       p.pathway_id,
       'Mid-level',
       -- jobDescription
       'An IT Project Manager is responsible for planning and executing projects within defined scope, timelines, and budgets. They coordinate and communicate with team members, stakeholders, and clients, ensuring project objectives are met. They also manage risks, resolve issues, and produce deliverables.',
       -- principalTasks
       'Analyze and coordinate the schedule, timeline, procurement, staffing, and budget of a product or service on a per project basis~Lead and guide the work of technical staff~Serve as a point of contact for the client or customer~Communicate with key stakeholders to determine project requirements and objectives~Assign duties or responsibilities to project personnel~Confer with project personnel to identify and resolve problems~Create project status presentations for delivery to customers or project personnel~Develop or update project plans including information such as objectives, technologies, schedules, funding, and staffing~Identify project needs such as resources, staff, or finances by reviewing project objectives and schedules~Identify, review, or select vendors or consultants to meet project needs~Monitor costs incurred by project staff to identify budget issues~Monitor project milestones and deliverables~Monitor the performance of project team members to provide performance feedback~Negotiate with project stakeholders or suppliers to obtain resources or materials~Plan, schedule, or coordinate project activities to meet deadlines~Prepare and submit budget estimates, progress reports, or cost tracking reports~Produce and distribute project documents~Propose, review, or approve modifications to project plans~Recruit or hire project personnel~Report project status, such as budget, resources, technical issues, or customer satisfaction, to managers~Request and review project updates to ensure deadlines are met~Schedule or facilitate project meetings~Submit project deliverables to clients, ensuring adherence to quality standards',
       -- principalSkills
       'Agile methodology~Change management~Communication~Data analysis~Finance~Process improvement~Project management~Project management software~Project planning and developing~Project risk management~Resource and workflow management~Presentation skills~Problem solving~Project coordination~Stakeholder management~Teamwork and collaboration',
       -- aiImpact
       'AI may transform IT project manager roles by streamlining processes, planning, reporting, and the resourcing of IT projects, allowing project managers to focus on more strategic activities. Robust groups of tasks will be assisted or automated while being overseen by IT project managers. Every stage of an IT project’s lifecycle will be affected by AI advancements and tools. Planning, estimates, and resourcing will be impacted with the use of AI-enhanced requirement and predictive analysis. AI tools will assist IT project managers in the day-to-day tracking and reporting of project life cycles, while automating many aspects of communication across stakeholders. AI will not replace creativity, negotiation, coaching, team building, collaboration, and other soft skills that are critical to the success of a project. AI will not replace Project Managers; AI will be a high-value tool within the Project Manager’s toolbox.',
       -- keyInsights
       'Streamlined task management: AI has the potential to streamline the execution of routine tasks such as scheduling, resource allocation, and progress tracking, freeing up project managers to focus on more strategic aspects of the project~Enhanced risk management: AI can analyze historical project data to identify potential risks and suggest mitigation strategies, improving project outcomes~Improved communication: AI-powered tools can facilitate communication within the project team, generating reports, summaries, and even translating documents in real-time~Data-driven decision making: AI can provide insights based on project data, helping project managers make informed decisions about resource allocation, timeline adjustments, and risk mitigation~Virtual assistants: AI-powered virtual assistants may be able to handle administrative tasks, schedule meetings, and provide project updates, improving efficiency and productivity',
       -- aiTransformation
       'High'
FROM [dbo].[pathways] p
WHERE p.pathway_title = 'Business and Management';

INSERT INTO [dbo].[JobRole] (id, title, pathwayId, jobLevel, jobDescription, principalTasks, principalSkills, aiImpact,
                             keyInsights, aiTransformation)
SELECT NEWID(),
       'Senior Product Manager',
       p.pathway_id,
       'Senior level',
       -- jobDescription
       'A Senior Product Manager oversees the development and lifecycle of multiple products, defining vision, strategy, and roadmap. Responsibilities include advanced market research, strategic stakeholder collaboration, prioritizing features, ensuring alignment with business goals, and leading product launch and performance. Exceptional leadership, strategic thinking, and communication skills are essential.',
       -- principalTasks
       'Develop and refine product strategies to align with market demands and business objectives~Perform user acceptance testing to validate product functionality and user experience~Identify areas for process improvement and implement initiatives to streamline workflows~Explore business development opportunities and partnerships to expand product reach~Implement agile methodologies to facilitate iterative development and enhance team agility~Utilize SQL queries to extract and analyze data for insights into user behavior and market trends~Gather and prioritize requirements from stakeholders to drive product development efforts~Enhance user experience through iterative design and usability testing~Manage software development life cycle processes to ensure timely delivery and quality~Conduct data analysis to identify trends and opportunities for product enhancement',
       -- principalSkills
       'Agile methodologies~Business development~Cross functional team leadership~Data analysis~JIRA~Problem solving~Process improvement~Product development life cycle~Product strategy~Quality assurance~SaaS~SQL~User acceptance testing~User experience',
       -- aiImpact
       'AI impact on the Senior Product Manager role might be moderate. Senior Product Managers might focus on upskilling skills like strategic planning and client relationship management. While skills in data analysis and quality assurance remain relevant, their demand for Senior Product Managers will decline due to AI-assisted automation and optimization.',
       -- keyInsights
       'The Senior Product Manager role involves strategic, analytical, and interpersonal tasks requiring human judgment, creativity, and interaction~Scrum and agile methodologies: AI can optimize workflows but lacks leadership capabilities (moderate impact)~Advanced market research: AI can process large datasets for market trends but cannot fully grasp nuanced market dynamics or strategic implications (moderate impact)~Strategic stakeholder collaboration: AI can assist in communication but cannot build and maintain the deep, strategic relationships needed (low impact)~Feature prioritization: AI can suggest prioritization based on data, but human insight is needed for strategic alignment and trade-off decisions (moderate impact)~Client relationship management: AI can interact and gather feedback but can''t build or sustain deep, trust-based client relationships (low impact)~Quality assurance and data analysis: AI excels in automation and data analysis, enhancing tasks significantly (high impact)~SQL and advanced analytics: AI assists with data extraction and analysis but cannot handle all complex problem-solving scenarios (high impact)~Strategic planning: AI can provide data-driven insights and forecasts, augmenting but not replacing human strategic thinking (moderate impact)~Team leadership and user experience: AI cannot lead teams or design holistic user experiences that require empathy and creativity (low to moderate impact)~Overall, AI can augment many aspects of the senior product manager role but cannot fully replace the essential human elements of strategic thinking, leadership, and deep interpersonal relationships',
       -- aiTransformation
       'Moderate'
FROM [dbo].[pathways] p
WHERE p.pathway_title = 'Business and Management';


-- CYBERSECURITY:
-- Entry level: Cybersecurity Analyst, Information Security Specialist, Soc Analyst Level 1
-- Mid-level: Ethical Hacker
INSERT INTO [dbo].[JobRole] (id, title, pathwayId, jobLevel, jobDescription, principalTasks, principalSkills, aiImpact,
                             keyInsights, aiTransformation)
SELECT NEWID(),
       'Cybersecurity Analyst',
       p.pathway_id,
       'Entry level',
       -- jobDescription
       'Cybersecurity Analysts are responsible for developing and implementing security measures to protect computer systems and networks. They monitor for security breaches, investigate violations, and update security systems to prevent future incidents. They also conduct risk assessments, document security policies and procedures, and educate users about security best practices.',
       -- principalTasks
       'Develop plans to safeguard computer files against accidental or unauthorized modification, destruction, or disclosure and to meet emergency data processing needs~Monitor current reports of computer viruses to determine when to update virus protection systems~Encrypt data transmissions and erect firewalls to conceal confidential information as it is being transmitted and to keep out tainted digital transfers~Perform risk assessments and execute tests of data processing system to ensure functioning of data processing activities and security measures~Modify computer security files to incorporate new software, correct errors, or change individual access status~Review violations of computer security procedures and discuss procedures with violators to ensure violations are not repeated~Document computer security and emergency measures policies, procedures, and tests~Confer with users to discuss issues such as computer data access needs, security violations, and programming changes~Monitor use of data files and regulate access to safeguard information in computer files~Coordinate implementation of computer system plan with establishment personnel and outside vendors~Train users and promote security awareness to ensure system security and to improve server and network efficiency',
       -- principalSkills
       'Access controls~Authorization (computing)~Communication~Configuration management~Continuous monitoring~Coordinating~Cyber threat intelligence~Encryption~Firewall~Governance~Incident response~Information assurance~Information systems security~Investigation~Manual malware analysis~Network security~Operating systems~Penetration testing~Planning~Presentations~Project management~Research information~Risk analysis~Risk management~Risk mitigation~Scripting~Security awareness~Security controls~Security information and event management~Security policies~Security requirements analysis~Training and development~Vulnerability assessments~Vulnerability management~Vulnerability scanning~Writing',
       -- aiImpact
       'Gen AI may drive a significant shift in the focus of Cybersecurity Analysts. Cybersecurity Analysts may need to adopt new skills related to prompt engineering, LLM architecture, and Retrieval-Augmented Generation (RAG) while enhancing existing skills in information assurance, risk management, and security policy analysis. They should be aware of which skills which may be streamlined by use of AI (such as writing and malware analysis) and place greater focus on skills that require human oversight, critical thinking, and decision making. Looking ahead, direct human involvement will still be crucial for over half of the Cybersecurity Analyst skills to ensure the effective application and monitoring of Gen AI tools. The emphasis will be on understanding and integrating Gen AI technologies, ensuring Cybersecurity Analysts can effectively defend against advanced threats and enhance their operational efficiency. AI will augment many aspects of the Cybersecurity Analyst role, significantly improving efficiency and effectiveness. However, it cannot fully replace the critical human elements of strategic thinking, problem-solving, communication, and collaboration. The Cybersecurity Analyst role will probably evolve to become more strategic, proactive, and focused on complex problem-solving, while AI handles more routine and repetitive tasks.',
       -- keyInsights
       'Enhanced threat detection: Gen AI can analyze vast datasets and identify patterns indicative of potential security threats much faster than humans, leading to proactive defense measures~Automated incident response: AI-powered tools can automate parts of the incident response process, such as isolating infected systems and generating reports, allowing for quicker containment and recovery~Vulnerability assessment and patching: AI can simulate attacks and identify system weaknesses, suggesting potential patches and fixes, streamlining the vulnerability management process~Enhanced security awareness training: AI can create realistic phishing simulations and tailor educational content to individual users, improving overall security awareness within organizations',
       -- aiTransformation
       'High'
FROM [dbo].[pathways] p
WHERE p.pathway_title = 'Cybersecurity';

INSERT INTO [dbo].[JobRole] (
    id, title, pathwayId, jobLevel,
    jobDescription, principalTasks, principalSkills,
    aiImpact, keyInsights, aiTransformation
)
SELECT NEWID(),
       'Information Security Specialist',
       p.pathway_id,
       'Entry level',
       -- jobDescription
       'The entry level Information Security Specialist enforces security policies, documents system security operations, implements cybersecurity measures, conducts security reviews, identifies, and mitigates risks, and develops risk management plans. They assess security controls, monitor trends, resolve incidents, ensure compliance, provide leadership recommendations, and contribute to disaster recovery and continuity plans.',
       -- principalTasks
       'Analyze and report organization and system security posture trends~Apply security policies to meet security objectives of the system~Assess and monitor cybersecurity related to system implementation and testing practices~Assess the effectiveness of security controls~Ensure all systems security operations and maintenance activities are properly documented and updated as necessary~Implement measures to resolve vulnerabilities, mitigate risks, and recommend changes to system or system components as needed~Implement specific cybersecurity countermeasures for systems and/or applications~Perform security reviews, identify gaps in security architecture, and develop a security risk management plan~Provide advice and input for disaster recovery, contingency, and continuity of operations plans~Provide cybersecurity recommendations to leadership based on significant threats and vulnerabilities~Resolve computer security incidents and vulnerability compliance~Verify minimum security requirements are in place for all applications',
       -- principalSkills
       'Apply cybersecurity and privacy principles to organizational requirements~Assess security controls based on cybersecurity principles and tenets~Assess security systems designs~Design the integration of hardware and software solutions~Determine how a security system should work and how changes will affect outcomes~Develop and apply security system access controls~Evaluate the adequacy of security designs~Recognize vulnerabilities in security systems~Write code in a currently supported programming language',
       -- aiImpact
       'Information And Cybersecurity Specialists will benefit from advances in artificial intelligence-fueled tools that can help better meet the demands of these roles. Realtime network traffic analysis at scale coupled with predictive analytics based on models trained on relevant historical data will create new requirements to recontextualize legacy knowledge and skills. Where contemporary malware detection matches software signatures against constantly updated databases, Information Security Specialists will leverage tools that detect anomalies in the behavior of code running on diverse end devices. The ensuing technological arms race between malicious actors and Information Security Specialists will demand agility, tenacity, and curiosity.',
       -- keyInsights
       'Advancing threat detection: Predictive analytics tools, deployed on local hardware, servers, and network devices will require new and augmented sets of skills. These AI-enhanced, pattern recognition tools will help identify threats at the earliest stages of their deployment~Faster incident response: Aspects of isolating and shutting down a threat once detected will become automated, speeding up security outcomes by freeing up Information Security Specialists to focus on identifying measures of remediation~Vulnerability detection and management: Automated audits of systems, networks, and software, powered by AI, will help Information Security Specialists further enhance the security position of organizations, products, and infrastructure by identifying existing vulnerabilities early and kicking off the process of correcting them',
       -- aiTransformation
       'High'
FROM [dbo].[pathways] p
WHERE p.pathway_title = 'Cybersecurity';

INSERT INTO [dbo].[JobRole] (
    id, title, pathwayId, jobLevel,
    jobDescription, principalTasks, principalSkills,
    aiImpact, keyInsights, aiTransformation
)
SELECT NEWID(),
       'Ethical Hacker',
       p.pathway_id,
       'Mid-level',
       -- jobDescription
       'Ethical Hackers assess and audit the security of servers, systems, and networks to identify vulnerabilities. They develop and execute tests simulating cyber threats, and design security solutions to known vulnerabilities, all while adhering to ethical guidelines and authorized parameters. They also investigate security incidents, maintain knowledge of hacking trends, and deliver specialized security awareness training.',
       -- principalTasks
       'Assess the holistic security of servers, systems, or network devices, including vulnerability to temperature, vandalism, or natural disasters~Collect stakeholder data to evaluate risk and to develop mitigation strategies~Conduct network and security system audits, using established criteria~Configure information systems to incorporate principles of least functionality and access~Design security solutions to address known device vulnerabilities~Develop and execute tests that simulate the techniques of known cyber threat actors~Develop infiltration tests that ethically exploit device vulnerabilities, adhering to authorized testing methodologies and ethical hacking guidelines~Develop presentations on threat intelligence~Conduct penetration tests against systems and networks and design innovative processes pertaining wireless deployments, data networks and telecommunication protocols~Discuss security solutions with information technology teams or management~Evaluate vulnerability assessments of local computing environments, networks, infrastructures, or enclave boundaries~Gather cyber intelligence on modern threats and research weaponizable vulnerabilities~Identify new threat tactics, techniques, or procedures used by cyber threat actors~Identify security system weaknesses, using ethical hacking techniques~Investigate security incidents, using computer forensics, network forensics, root cause analysis, or malware analysis~Maintain up-to-date knowledge of hacking trends~Prepare and submit reports describing the results of security fixes~Test the security of systems by conducting authorized assessments to identify vulnerabilities~Update corporate policies to improve cybersecurity~Write audit reports to communicate technical and procedural findings and recommend solutions~Perform targeted social engineering assessments to evaluate human vulnerabilities and awareness~Deliver Specialized Security Awareness Training tailored to the organization''s unique threats and vulnerabilities',
       -- principalSkills
       'Application security~Auditing and reporting~Automation~Burp suite~Communication~Cybersecurity~Ethical hacking~Gap analysis~Information processing~Management~Metasploit~Network infrastructure~NIST 800-53~Offensive security~Open web application security project~Operations~Penetration testing~Personnel procedures~Presentations~Process improvement~Python~Research information~Risk analysis~Scripting~Security controls~Security requirements analysis~Social engineering~Test tools~Vulnerability assessments~Vulnerability management~Vulnerability scanning~Web applications~White box testing~Writing',
       -- aiImpact
       'Gen AI will significantly impact Ethical Hackers'' skillsets. Key areas like vulnerability scanning and environmental threat monitoring stand to benefit from AI-powered tools, enabling automatic detection of vulnerabilities and assessing environmental risks to servers and networks. However, human supervision remains crucial in half of the skillset, requiring Ethical Hackers to understand and integrate Gen AI technologies effectively. The job''s focus will shift towards leveraging Gen AI to identify vulnerabilities efficiently, demanding expertise in Gen AI''s capabilities rather than just technical proficiency. Additionally, while some skills like process improvement and security requirements analysis will be augmented, others like writing and research face displacement risks. This underscores the need for Ethical Hackers to adapt to emerging AI technologies and evolving job demands to remain effective in their roles.',
       -- keyInsights
       'Security auditing and reporting: AI can help automate report generation and analysis, highlighting critical vulnerabilities and suggesting remediation steps~Security recommendations and remediation: While AI can offer suggestions, the final decision-making on remediation strategies often requires human judgment~Social engineering assessment: AI can assist in analyzing communication patterns and identifying potential social engineering attempts, but human insight is crucial~Security research and tool development: AI can analyze large datasets of vulnerabilities, but developing new tools and techniques still requires human creativity~Security awareness training: AI can personalize training materials and simulations, though human rapport is essential~Incident response support: AI can help in analyzing incident data and suggesting containment strategies, but human intervention is needed during crises~Ethical Hackers must understand Gen AI capabilities to exploit vulnerabilities and evaluate integration risks~Expertise in AI and ML will be increasingly important for leveraging AI tools~Critical thinking and problem solving will be essential for evaluating AI-generated outputs and decisions',
       -- aiTransformation
       'Moderate'
FROM [dbo].[pathways] p
WHERE p.pathway_title = 'Cybersecurity';

INSERT INTO [dbo].[JobRole] (
    id, title, pathwayId, jobLevel,
    jobDescription, principalTasks, principalSkills,
    aiImpact, keyInsights, aiTransformation
)
SELECT NEWID(),
       'Soc Analyst Level 1',
       p.pathway_id,
       'Entry level',
       -- jobDescription
       'A SOC Analyst – Level 1 is responsible for monitoring and analyzing security events and incidents within an organization''s network. They respond to alerts, perform initial investigations, and escalate issues as needed, while also maintaining and implementing security measures to detect and respond to threats.',
       -- principalTasks
       'Continuously monitor security alerts, logs, and events, focusing on indicators of compromise, anomalous activities, and known attack patterns to identify potential security incidents~Analyze and categorize incidents~Understand criteria for incident escalation, ensuring a comprehensive grasp of when and how to escalate issues to higher levels or other teams within the organization~Monitor use of data files and regulate access to safeguard information in computer files~Coordinate activities within incident response and ongoing monitoring to ensure the effective implementation of security measures~Engage with users during incident response and security violations to address immediate access issues and concerns~Monitor and respond to alerts related to encryption and firewall events to ensure the concealment of confidential information and prevent digital threats~Develop and implement immediate operational plans for safeguarding computer files against unauthorized access or breaches~Perform risk assessments and execute tests of data processing systems to ensure functioning of data processing activities and security measures~Review violations of computer security procedures and engage with violators to ensure violations are not repeated~Monitor current reports of computer viruses to determine when to update virus protection systems',
       -- principalSkills
       'Communication~Coordinating~Customer service~Cyber threat intelligence~Cybersecurity~Endpoint detection and response~Firewall~Incident management~Incident response~Intrusion detection and prevention~Investigation~Log analysis~Manual malware analysis~Operations~Penetration testing~Security controls~Security information and event management~Standard operating procedure~Triage~Troubleshooting~Vulnerability management',
       -- aiImpact
       'Gen AI has the potential to transform the role of SOC Analyst Level 1 in cybersecurity through several key advancements. It enhances threat detection by creating sophisticated models that evolve to identify new cyber threats, requiring analysts to interpret these findings. Automated responses to common threats shift the role towards overseeing AI systems. Gen AI aids in data synthesis for training and testing without real threats. It generates actionable threat intelligence, reduces false positives, and simulates adversarial attacks, enhancing security robustness. Continuous learning, ethical considerations, prompt engineering and understanding methods for grounding the model (e.g., RAG) define the evolving responsibilities of SOC Analysts.',
       -- keyInsights
       'Alert monitoring and triage: AI-powered SIEM systems and threat detection platforms can automate the initial analysis of security alerts, significantly reducing the time and effort required for this task~Log analysis: AI-driven log analysis tools can quickly sift through massive amounts of log data to identify patterns and anomalies, reducing the need for manual analysis~Vulnerability scanning: AI can automate vulnerability scanning and assessment, providing quicker and more comprehensive results than manual processes~Threat intelligence analysis: AI can rapidly process and analyze threat intelligence feeds, identifying relevant information and alerting analysts to emerging threats~Incident response: AI can assist in incident response by automating data collection, suggesting containment actions, and generating initial reports. However, human analysts will still be needed to make critical decisions, investigate complex incidents, and communicate with stakeholders~Threat hunting: AI can help identify potential threats by analyzing patterns in security data, but human analysts are still needed to develop hunting hypotheses, investigate leads, and make strategic decisions~Communication and collaboration: Effective communication with stakeholders remains crucial. AI cannot replace the human element in building relationships, explaining technical issues, and providing reassurance during incidents~Decision making and judgment: AI can offer recommendations, but critical decisions must still be made by human analysts~SOC Analysts will need to understand prompt engineering and how to translate AI-generated output into action',
       -- aiTransformation
       'High'
FROM [dbo].[pathways] p
WHERE p.pathway_title = 'Cybersecurity';

-- DATA SCIENCE:
-- Entry level: Data Analyst, Data Specialist
-- Mid-level: Data Engineer, Data Scientist
INSERT INTO [dbo].[JobRole] (
    id, title, pathwayId, jobLevel,
    jobDescription, principalTasks, principalSkills,
    aiImpact, keyInsights, aiTransformation
)
SELECT NEWID(),
       'Data Analyst',
       p.pathway_id,
       'Entry level',
       -- jobDescription
       'Data Analysts synthesize and analyze data to generate reports for stakeholders, providing insights and recommendations based on current trends. They maintain a library of reusable assets, create business intelligence tools, and ensure timely delivery of analytical information. Additionally, they collect, validate, and update data while staying updated on industry advancements, collaborating with stakeholders to define meaningful key performance indicators (KPIs) aligned with organizational goals.',
       -- principalTasks
       'Generate standard or custom reports summarizing data for review by executives, managers, clients, and other stakeholders~Synthesize current trend data to support recommendations for action~Maintain library of model documents, templates, or other reusable knowledge assets~Create business intelligence tools or systems, including design of related databases, spreadsheets, or outputs~Manage timely flow of analytical information to users~Collect data from available industry reports, public information, field reports, or purchased sources~Maintain or update data analysis tools, databases, dashboards, systems, or methods~Provide training sessions to enhance data literacy among stakeholders, enabling them to interpret and leverage data for informed decision-making~Provide technical support for analytical reports, dashboards, or other tools~Identify and analyze industry or geographic trends with business strategy implications~Continuously monitor and assess new tools and techniques in the data analysis field, ensuring the adoption of best practices and staying abreast of industry advancements~Create or review technical design documentation to ensure the accurate development of reporting solutions~Analyze technology trends to identify markets for future product development or to improve sales of existing products~Create and implement procedures to validate the accuracy and reliability of data~Clean and preprocess data before analysis, ensuring data quality and relevance~Explore datasets using statistical and visual methods to identify patterns, trends, and outliers~Develop scripts or programs to automate repetitive data-related tasks, enhancing efficiency and reducing manual effort in data analysis workflows~Collaborate with stakeholders to define and establish meaningful KPIs based on data insights, aligning with organizational goals~Document specifications for data analysis reports, dashboards, or other outputs',
       -- principalSkills
       'Analytical skills~Auditing~Business intelligence~Business requirements~Business strategies~Communication~Data cleansing~Data collection~Data dashboards~Data governance~Data management~Data modeling~Data preprocessing~Data quality~Data visualization~Data warehousing~Decision making~Descriptive statistics~Innovation~Microsoft Excel~Operations~Presentations~Python~R~SQL~Writing',
       -- aiImpact
       'The role of Data Analysts is shifting towards leveraging Gen AI for enhanced efficiency and insight generation, while still requiring human oversight and validation, especially in critical areas where errors could have significant consequences. Key areas include effective prompt engineering, understanding LLM capabilities and biases. This shift will require Data Analysts to focus more on complex, strategic, and analytical skills, such as auditing, decision making, and innovation, while routine data tasks that require coding could be automated or augmented.',
       -- keyInsights
       'More than half of the skills will likely be impacted by Gen AI in the near term, with a notable fraction being augmented to boost efficiency~In the long run, a further portion of skills could be automated, but the high consequence of errors associated with this work will still necessitate direct human involvement in a notable fraction of skills. These skills could be augmented with advanced Gen AI~Data Analysts will need to understand effective prompt engineering, as Gen AI technologies can be of great aid in their work analyzing, synthesizing and visualizing results from large datasets~Gen AI is particularly useful as an analytic and search tool for textual data analysis. However, experts emphasize human validation and review of AI-generated insights, especially for tasks requiring high accuracy~Integrating Python sandboxes (code interpreter) with Large Language Models (LLMs) enhances data analysis. However, human inspection and oversight of code and processes are essential for accuracy and reliability~Understanding the biases of LLMs will be critical for these workers, as they will need to be able to interpret, validate, and effectively implement Gen AI outputs in the context of their business use case',
       -- aiTransformation
       'Moderate'
FROM [dbo].[pathways] p
WHERE p.pathway_title = 'Data Science';

INSERT INTO [dbo].[JobRole] (
    id, title, pathwayId, jobLevel,
    jobDescription, principalTasks, principalSkills,
    aiImpact, keyInsights, aiTransformation
)
SELECT NEWID(),
       'Data Engineer',
       p.pathway_id,
       'Mid-level',
       -- jobDescription
       'Data Engineers are responsible for designing, construct, and maintain scalable data pipelines that ensure the efficient extraction, transformation, and loading (ETL) of data from various sources to data warehouses or lakes. They collaborate with data scientists, analysts, and other stakeholders to integrate data from disparate systems, ensuring data quality, consistency, and security throughout the data lifecycle. They also optimize data processing workflows for performance and scalability while automating repetitive tasks to enhance the overall efficiency and reliability of the data infrastructure.',
       -- principalTasks
       'Building and maintaining ETL processes: Developing and managing Extract, Transform, Load (ETL) processes to ensure that data is accurately and efficiently transferred from source systems to data storage solutions, such as data warehouses or data lakes~Ensuring data quality and integrity: Implementing data validation and cleaning procedures to ensure the accuracy, consistency, and reliability of data throughout its lifecycle, including monitoring and troubleshooting data issues as they arise~Optimizing data infrastructure: Continuously optimizing the data architecture for performance, scalability, and cost-efficiency, including the use of indexing, partitioning, and other techniques to enhance data processing speed and storage utilization',
       -- principalSkills
       'Apache spark~Azure Databricks~Extract, transform, load~Hadoop~Hive~PySpark~Python~Scala~Snowflake cloud',
       -- aiImpact
       'Gen AI may be able to help accomplish many of the tasks for which this role is responsible, leaving more time for people in this role to focus on higher value-added complementary skills. Specifically for Data Engineers, this may mean understanding how to use Gen AI to increase productivity when developing ETL processes.',
       -- keyInsights
       'Workers in this role can enhance their productivity by leveraging Gen AI for data modeling, optimizing workflows with Apache Airflow and Tableau, therefore dedicating more time to data engineering tasks.',
       -- aiTransformation
       'Moderate'
FROM [dbo].[pathways] p
WHERE p.pathway_title = 'Data Science';

INSERT INTO [dbo].[JobRole] (
    id, title, pathwayId, jobLevel,
    jobDescription, principalTasks, principalSkills,
    aiImpact, keyInsights, aiTransformation
)
SELECT NEWID(),
       'Data Scientist',
       p.pathway_id,
       'Mid-level',
       -- jobDescription
       'A Data Scientist analyzes complex data sets to derive actionable insights and build predictive models. Responsibilities include data cleaning, statistical analysis, machine learning, and communicating findings to stakeholders. Proficiency in programming, data visualization, and strong analytical skills are essential.',
       -- principalTasks
       'Utilize Python libraries and frameworks for data manipulation, analysis, and modeling~Conduct statistical analysis to extract insights and identify patterns in large datasets~Develop and implement machine learning algorithms for predictive modeling and analysis~Create data visualizations to communicate findings and insights to stakeholders~Apply R programming for statistical analysis and data visualization tasks~Utilize Tableau for interactive data visualization and dashboard creation~Perform data mining techniques to discover actionable insights from structured and unstructured data~Design and implement statistical models for predictive analytics and forecasting~Utilize Hadoop for distributed storage and processing of large-scale datasets~Apply natural language processing techniques for text mining and sentiment analysis tasks~Drives the design, development and optimization of AI/ML frameworks',
       -- principalSkills
       'Apache spark~Artificial intelligence~Big data~Data analytics~Data mining~Data visualization~Deep learning~Hadoop~Hive~Machine learning~Natural language processing~NumPy~Pandas~Predictive analytics~Predictive modeling~Python~R~Statistical modeling~Tableau~TensorFlow',
       -- aiImpact
       'AI will significantly impact the Data Scientist role by automating data cleaning, analysis, and model building. Data Scientists will need to focus on upskilling in areas like AI model interpretability, advanced machine learning techniques, and domain-specific knowledge. While AI can handle many routine tasks, human expertise in strategic decision-making and communication remains essential.',
       -- keyInsights
       'The Data Scientist role involves data analysis, machine learning, and deriving actionable insights from complex datasets, requiring human judgment, creativity, and strategic thinking~Data cleaning: AI can automate data cleaning processes, significantly reducing the time spent on this task (high impact)~Statistical analysis: AI can perform statistical analyses quickly and accurately, but human oversight is needed to ensure appropriate methods and interpretations (moderate impact)~Machine learning: AI can build and optimize machine learning models, but human expertise is needed for model selection, tuning, and understanding domain-specific nuances (high impact)~Data visualization: AI tools can create visualizations, but human insight is needed to design effective and meaningful representations (moderate impact)~Communication of findings: AI can generate reports, but the ability to communicate complex findings to non-technical stakeholders requires human skills (low impact)~Strategic decision-making: AI can provide data-driven insights, but strategic decisions require human judgment and contextual understanding (low impact)~Overall, AI will augment many technical aspects of the Data Scientist role, automating routine tasks and enhancing analytical capabilities. However, human expertise in strategic thinking, model interpretation, and effective communication remains crucial for success',
       -- aiTransformation
       'High'
FROM [dbo].[pathways] p
WHERE p.pathway_title = 'Data Science';

INSERT INTO [dbo].[JobRole] (
    id, title, pathwayId, jobLevel,
    jobDescription, principalTasks, principalSkills,
    aiImpact, keyInsights, aiTransformation
)
SELECT NEWID(),
       'Data Specialist',
       p.pathway_id,
       'Entry level',
       -- jobDescription
       'Data Specialists ensures the accuracy, integrity, and quality of data by implementing data validation protocols, managing data cleansing processes, and maintaining comprehensive data documentation. They perform detailed data analysis and reporting to generate actionable insights, creating reports and visualizations to support business decision-making and strategic planning. They also integrate data from various sources and collaborate with cross-functional teams to support data-driven projects and initiatives, ensuring effective data utilization across the organization.',
       -- principalTasks
       'Data management and quality assurance: Ensure the accuracy, integrity, and quality of data by implementing data validation protocols, managing data cleansing processes, and maintaining comprehensive data documentation~Data analysis and reporting: Perform detailed data analysis to generate actionable insights, creating reports and visualizations to support business decision-making and strategic planning~Data integration and collaboration: Integrate data from various sources and collaborate with cross-functional teams to support data-driven projects and initiatives, ensuring effective data utilization across the organization​',
       -- principalSkills
       'Data analytics~Data visualization~Java~Microsoft Power BI~Microsoft SQL server~Python~R~SQL~Tableau',
       -- aiImpact
       'Gen AI may be able to help accomplish many of the tasks for which this role is responsible, leaving more time for people in this role to focus on higher value-added complementary skills. Specifically for Data Specialists, this may mean understanding how to use Gen AI to increase productivity when analyzing and visualizing data.',
       -- keyInsights
       'Workers in this role can enhance their productivity by leveraging Gen AI for data entry automation, optimizing workflows with Tableau and Apache, and dedicating more time to data engineering tasks.',
       -- aiTransformation
       'Moderate'
FROM [dbo].[pathways] p
WHERE p.pathway_title = 'Data Science';

-- DESIGN AND USER EXPERIENCE:
-- Entry level: Design Engineer, UX Designer
-- Mid-level: Product Design Engineer
INSERT INTO [dbo].[JobRole] (
    id, title, pathwayId, jobLevel,
    jobDescription, principalTasks, principalSkills,
    aiImpact, keyInsights, aiTransformation
)
SELECT NEWID(),
       'Design Engineer',
       p.pathway_id,
       'Entry level',
       -- jobDescription
       'Design Engineers develop and modify product designs by creating detailed prototypes, performing rigorous testing, and ensuring adherence to engineering principles and client requirements​. They collaborate with cross-functional teams, including manufacturing and senior engineers, to oversee the entire lifecycle of a project from conceptualization to final production. Also, they are responsible to maintain comprehensive documentation of design processes, project schedules, and budget compliance while staying updated with the latest technological advancements and design trends.',
       -- principalTasks
       'Collaboration and documentation: Working closely with other engineers and departments to meet project requirements and timelines while maintaining detailed documentation of design processes and progress, ensuring all designs comply with safety standards and regulatory requirements~Product and component design: Creating new products or improving existing ones across various sectors, including mechanical, structural, and electrical design, and managing the entire lifecycle of a project from conceptualization through to testing and manufacturing~Prototype development and testing: Conducting research, designing, and prototyping products, all while adhering to engineering principles, performing product testing, and modifying designs to enhance functionality and effectiveness​',
       -- principalSkills
       'CAD~CATIA~Finite element analysis~Geometric dimensioning~MATLAB~Mechanical engineering~PTC Creo~Siemens NX~SolidWorks',
       -- aiImpact
       'Gen AI may be able to help accomplish many of the tasks for which this role is responsible, leaving more time for people in this role to focus on higher value-added complementary skills. Specifically for Design Engineers, this may mean understanding how to use Gen AI to iterate prototypes, particularly by accelerating finite element analysis and other modeling exercises.',
       -- keyInsights
       'Workers in this role can enhance their productivity by leveraging Gen AI for finite element analysis automation, optimizing product design workflows and dedicating more time to engineering management processes.',
       -- aiTransformation
       'Moderate'
FROM [dbo].[pathways] p
WHERE p.pathway_title = 'Design and User Experience';

INSERT INTO [dbo].[JobRole] (
    id, title, pathwayId, jobLevel,
    jobDescription, principalTasks, principalSkills,
    aiImpact, keyInsights, aiTransformation
)
SELECT NEWID(),
       'Product Design Engineer',
       p.pathway_id,
       'Mid-level',
       -- jobDescription
       'Designs digital user interfaces or websites. Develop and test layouts, interfaces, functionality, and navigation menus to ensure compatibility and usability across browsers or devices. May use web framework applications as well as client-side code and processes. May evaluate web design following web and accessibility standards and may analyze web use metrics and optimize websites for marketability and search engine ranking. May design and test interfaces that facilitate the human-computer interaction and maximize the usability of digital devices, websites, and software with a focus on aesthetics and design. May create graphics used in websites and manage website content and links.',
       -- principalTasks
       'Provide clear, detailed descriptions of website specifications, such as product features, activities, software, communication protocols, programming languages, and operating systems software and hardware~Register websites with search engines to increase website traffic~Research and apply innovative solutions for product design, visuals, and user experience to meet the needs of individual web development projects~Research, document, rate, or select alternatives for web architecture or technologies~Respond to user email inquiries or set up automated systems to send responses~Select programming languages, design tools, or applications~Write and edit technical documentation for digital interface products and designs, such as user manuals, testing protocols, and reports~Write supporting code for web applications or websites~Direct and execute pre-production activities, such as creating mood boards or storyboards and establishing a project timeline~Document technical factors such as server load, bandwidth, database performance, and browser and device types~Identify or maintain links to and from other websites and check links to ensure proper functioning~Identify problems uncovered by testing or customer feedback, and correct problems or refer problems to appropriate personnel for correction~Incorporate technical considerations into website design plans, such as budgets, equipment, performance requirements, or legal issues including accessibility and privacy',
       -- principalSkills
       'Communication~Detail oriented~Figma (design software)~Innovation~Leadership~Management~Marketing~Mechanical engineering~New product development~Operations~Planning~Presentations~Problem solving~Product design~Project management~Prototyping~Research information~Sales~Self-motivation~User experience',
       -- aiImpact
       'Gen AI has the potential to significantly impact Product Designers. AI tools can significantly augment the design process by automating repetitive tasks, generating design variations, and even assisting in prototyping and user testing. While this can lead to significant efficiency gains, it also presents challenges for designers, requiring them to adapt their skillset and focus on higher-level creative and strategic aspects of their work. By embracing AI as a collaborative tool and developing the necessary skills, designers can unlock new levels of creativity, efficiency, and innovation, ultimately creating better products for users.',
       -- keyInsights
       'Rapid prototyping: AI can generate multiple design iterations quickly based on given parameters, allowing designers to streamline the execution of a wider range of ideas and concepts in a shorter time frame~Enhanced user research: AI can analyze user data and provide insights into user behavior, preferences, and pain points, helping designers make more informed decisions~Streamlined design tasks: Gen AI can streamline design of repetitive tasks such as creating layouts, generating icons, or optimizing images, freeing up designers to focus on higher-level design challenges~Improved accessibility: AI tools can assist in designing interfaces that are accessible to users with disabilities, ensuring a broader audience can use the product~Personalized experiences: AI can help create dynamic interfaces that adapt to individual user preferences and behavior, enhancing user satisfaction of IT support operations',
       -- aiTransformation
       'High'
FROM [dbo].[pathways] p
WHERE p.pathway_title = 'Design and User Experience';

INSERT INTO [dbo].[JobRole] (
    id, title, pathwayId, jobLevel,
    jobDescription, principalTasks, principalSkills,
    aiImpact, keyInsights, aiTransformation
)
SELECT NEWID(),
       'UX Designer',
       p.pathway_id,
       'Entry level',
       -- jobDescription
       'An entry level UX Designer enhances product usability, researches user behavior, and compiles audience insights. They develop and test design models, create accessible website layouts, and prototype interfaces using HTML/CSS. Additionally, they gather requirements, refine specifications, evaluate existing designs, and present design strategies and improvement recommendations and/or updates to stakeholders, ensuring alignment with business and user needs.',
       -- principalTasks
       'Articulate design decision by presenting strategy and concepts to key stakeholders~Assist with technology design to make products easier to use~Compile information about audience for a site~Design and technology features that improve accessibility and value for users~Determine user preferences and assess process followed to access product functions~Develop website layout~Develop and test new design models and incorporate findings to improve product design~Experiential and business from stakeholders~Gather and refine specifications and requirements based on design~Prototype website layout and user interfaces using HTML/CSS~Research the behavior of internet users and consumers',
       -- principalSkills
       'Analytical thinking~Benchmarking/ data/ metrics~Conduct usability tests and incorporate results into design process~Create personas~Create prototype~Data and knowledge driven problem definition and solving~Describe scenarios~Develop user flows~Make iterations~Presentation~Research information~Strong communication~Translate user problems into practical design solutions~Understand and synthesize technology into meaningful human experiences~Validate design solutions',
       -- aiImpact
       'Design ideation, design processes, and design output. UX Designers will be able to create and facilitate more personalized experiences, leverage and incorporate data analytics to improve design decisions, and more efficiently develop tangible concepts. The outcomes of these changes can improve user satisfaction and accessibility, as well as business outcomes through a more efficient design process.',
       -- keyInsights
       'User impact and outcomes: UX Designers will need to create designs that allow for bespoke experiences within discrete sections or modules of an application. Additionally, expanding voice interactions and other emerging user input/output paradigms will require a shift in some of the ways user interactions are facilitated. This can be especially impactful for differently abled users who will experience expanded accessibility in several ways~Solution design and development: Refined user research and insights based on large scale real and synthetic user persona data will fuel designed solutions to user problems of all sizes. These developments will benefit users and businesses alike. Some of these insights will facilitate automated design generation and simulated testing solutions~Design deliverables: Accelerated design iterations with Gen AI tools that can draft testable, high-fidelity prototypes in the time it may currently take designers to create paper sketches of wireframes. As new tools are created, design and testing will become faster, with some aspects of design iteration automated',
       -- aiTransformation
       'High'
FROM [dbo].[pathways] p
WHERE p.pathway_title = 'Design and User Experience';

-- INFRASTRUCTURE AND OPERATIONS:
-- Entry level: Help Desk Analyst, IT Support Technician, Network Support Technician, Systems Analyst
-- Mid-level: Database Administrator, IT Manager, Network Administrator, Network and IT Automation Engineer, Systems Administrator
-- Senior level: Senior Network Engineer
INSERT INTO [dbo].[JobRole] (
    id, title, pathwayId, jobLevel,
    jobDescription, principalTasks, principalSkills,
    aiImpact, keyInsights, aiTransformation
)
SELECT NEWID(),
       'Database Administrator',
       p.pathway_id,
       'Mid-level',
       -- jobDescription
       'A Database Administrator (DBA) is responsible for managing and maintaining an organization''s database systems. They ensure data integrity, security, and performance, as well as troubleshoot any issues that may arise.',
       -- principalTasks
       'Data backup and disaster recovery: Develop and implement data backup procedures to prevent data loss and configure disaster recovery plans to ensure database availability and continuity~Database design and modeling: Design and model databases according to organizational needs and industry best practices to support efficient data storage, processing, and retrieval~Database installation and maintenance: Install, configure, update, and maintain database systems and software to ensure smooth operations~Database security management: Implement and maintain robust security measures to protect databases from unauthorized access and ensure data integrity~Database troubleshooting: Identify and resolve issues related to database performance, accessibility, and functionality~Performance monitoring and tuning: Monitor database performance and configure databases for optimal efficiency and speed~SQL query optimization: Write and optimize SQL queries to improve database performance and response times~System integration: Integrate database systems with other software applications and ensure seamless data interchange and functionality across platforms~Technical documentation and reporting: Create detailed reports and maintain documentation for database specifications, configurations, and performance metrics~User access management: Manage user access and authentication to ensure database security and compliance with data protection regulations',
       -- principalSkills
       'Cloud computing~Communication~Database design~Demonstrating responsibility~Disaster recovery~Documentation maintenance~Enterprise software~Interpersonal collaboration~Leadership demonstration~Microsoft SQL server~Network disaster recovery~Performance tuning~Problem solving~Systems management~Time management~Troubleshooting',
       -- aiImpact
       'AI impact on the Database Administrator role might be moderate. While documentation and performance tuning can be highly automated, skills like troubleshooting, systems management, and database design are less affected. Database Administrators should focus on upskilling in areas like disaster recovery and enterprise software, where AI can complement their work. Technical skills like Microsoft SQL server and cloud computing are moderately to highly susceptible to AI automation.',
       -- keyInsights
       'Impact on number of hours: Gen AI can automate some tasks like documentation and performance tuning, but the overall impact on working hours may be limited~New skills: Database Administrators will need to acquire skills in AI security, TensorFlow, neural networks, and image signal processing to adapt to the changing landscape~Skills in demand: Problem-solving, communication, and interpersonal collaboration will remain essential for database administrators, as they often work closely with other teams to ensure smooth database operations',
       -- aiTransformation
       'Moderate'
FROM [dbo].[pathways] p
WHERE p.pathway_title = 'Infrastructure and Operations';

INSERT INTO [dbo].[JobRole] (
    id, title, pathwayId, jobLevel,
    jobDescription, principalTasks, principalSkills,
    aiImpact, keyInsights, aiTransformation
)
SELECT NEWID(),
       'Help Desk Analyst',
       p.pathway_id,
       'Entry level',
       -- jobDescription
       'Help Desk Analysts are the first line of technical support for computer users. They provide assistance via phone or electronically, troubleshooting hardware, software, and network issues. These workers translate technical jargon into user-friendly solutions, guiding individuals through problem-solving steps. Help Desk Analysts combine technical knowledge with strong communication skills to ensure a positive user experience, resolving issues efficiently and effectively.',
       -- principalTasks
       'Diagnose and troubleshoot~Provide technical support~Install and configure~Educate and train~Document and track~Escalate complex problems~Test and evaluate~Monitor system performance~Create and update knowledge base~Prioritize and manage requests~Collaborate with IT teams~Maintain security standards~Stay updated on technology~Communicate effectively~Provide excellent customer service',
       -- principalSkills
       'Ability to explain technical concepts clearly to non-technical users~Ability to think creatively and adapt to different situations~Ability to work under pressure and meet deadlines~Active listening~Analytical skills to identify root causes of issues~Computer hardware (desktops, laptops, peripherals)~Documentation maintenance~Excellent verbal and written communication~Help desk software (ServiceNow, Zendesk, etc.)~Implementing solutions and workarounds~Microsoft Office suite (Word, Excel, Outlook, PowerPoint)~Networking fundamentals (LAN, Wi-Fi)~Operating systems (Windows 10, macOS, potentially Linux)~Patience and ability to handle difficult situations~Prioritization and multitasking~Strong customer focus and empathy',
       -- aiImpact
       'Gen AI is set to revolutionize the Help Desk Analyst role, automating routine tasks, and enabling a shift towards proactive problem prevention and enhanced customer service. While the demand for analysts handling basic issues may decrease, skilled workers who can leverage AI tools, tackle complex problems, and foster strong customer relationships will be highly sought after. To thrive in this evolving landscape, Help Desk Analysts must embrace AI, upskill in strategic areas, and adopt a proactive approach to IT support.',
       -- keyInsights
       'Tier-1 support and initial troubleshooting: AI chatbots can handle routine inquiries, password resets, and basic troubleshooting, freeing up analysts for more complex issues~Knowledge base creation and maintenance: AI can automatically generate, and update knowledge articles based on resolved tickets and user interactions~Data analysis and reporting: AI can analyze help desk data to identify trends, predict potential problems, and suggest improvements to processes~Complex troubleshooting: AI can suggest solutions based on past cases and knowledge articles, assisting analysts in diagnosing and resolving complex problems faster~Customer communication: AI powered tools can help analysts communicate more effectively by suggesting responses, translating technical jargon, and personalizing interactions',
       -- aiTransformation
       'High'
FROM [dbo].[pathways] p
WHERE p.pathway_title = 'Infrastructure and Operations';

INSERT INTO [dbo].[JobRole] (
    id, title, pathwayId, jobLevel,
    jobDescription, principalTasks, principalSkills,
    aiImpact, keyInsights, aiTransformation
)
SELECT NEWID(),
       'IT Manager',
       p.pathway_id,
       'Mid-level',
       -- jobDescription
       'IT Manager oversees IT Infrastructure and Operations. They manage and maintain the organization''s IT infrastructure, ensuring all systems, networks, and hardware operate efficiently and securely. They lead and develop IT Teams, providing guidance, training, and support to ensure the team meets organizational goals and technological demands. Furthermore, they develop strategic plans for IT projects, align IT initiatives with business goals, and manage the IT budget to optimize costs and investments.',
       -- principalTasks
       'Infrastructure management: Maintaining essential IT infrastructure, such as operating systems, security tools, applications, servers, email systems, and both software and hardware, ensuring everything is up to date and functioning efficiently~Project leadership: Overseeing significant projects within the organization and ensuring they align with larger business initiatives, which requires handling business-critical IT tasks and systems administration~Technology evaluation and training: IT Managers continuously research and evaluate emerging technologies to recommend and implement effective solutions and upgrades. Additionally, they provide necessary training to staff, enhancing the overall tech proficiency within the organization',
       -- principalSkills
       'Active directory~Cybersecurity~Disaster recovery~IT strategy~Microsoft exchange~Network administration~Vendor management~VMware~Windows server',
       -- aiImpact
       'Gen AI may be able to assist in a few of the tasks for which this role is responsible, but the core skills for the role are likely to remain unaffected by Gen AI in the near-term. However, IT Managers may be able to leverage Gen AI to accelerate and standardize troubleshooting procedures and will need to consider how their teams use and support AI tools.',
       -- keyInsights
       'In thinking about professional development and upskilling plans, people currently in this role might consider how to use Gen AI to dramatically reduce time spent troubleshooting how to leverage Gen AI to increase productivity working with cybersecurity features, and how to spend more time developing IT strategies.',
       -- aiTransformation
       'Low'
FROM [dbo].[pathways] p
WHERE p.pathway_title = 'Infrastructure and Operations';

INSERT INTO [dbo].[JobRole] (
    id, title, pathwayId, jobLevel,
    jobDescription, principalTasks, principalSkills,
    aiImpact, keyInsights, aiTransformation
)
SELECT NEWID(),
       'IT Support Technician',
       p.pathway_id,
       'Entry level',
       -- jobDescription
       'IT Support Technicians monitor and maintain computer systems, install, and set up equipment and software for users, and troubleshoot technical issues. They collaborate with staff to determine system requirements, maintain records of transactions and activities. They also evaluate and recommend software or hardware improvements, develop training materials, and supervise workers on special projects.',
       -- principalTasks
       'Conduct office automation feasibility studies, including workflow analysis, space design, or cost comparison analysis~Set up equipment for worker use, performing or ensuring proper installation of cables, operating systems, or appropriate software~Read technical manuals, confer with users, or conduct computer diagnostics to investigate and resolve problems or to provide technical assistance and support~Answer user inquiries regarding computer software or hardware operation to resolve problems~Install and perform minor repairs to hardware, software, or peripheral equipment, following design or installation specifications~Confer with staff, users, and management to establish requirements for new systems or modifications~Enter commands and observe system functioning to verify correct operations and detect errors~Hire, supervise, and direct workers engaged in special project work, problem-solving, monitoring, and installation of data communication equipment and software~Maintain records of daily data communication transactions, problems and remedial actions taken, or installation activities~Prepare evaluations of software or hardware and recommend improvements or upgrades~Develop training materials and procedures, or train users in the proper use of hardware or software~Inspect equipment and read order sheets to prepare for delivery to users~Read trade magazines and technical manuals or attend conferences and seminars to maintain knowledge of hardware and software~Modify and customize commercial programs for internal needs~Oversee the daily performance of computer systems',
       -- principalSkills
       'Adaptability~Automation~Communication~Computer hardware~Critical problem solving~Customer service~Debugging~Detail oriented~End-user training~Help desk support~Information technology~Interpersonal communications~Issue tracking~Knowledge base maintenance~Leadership~Management~Microsoft office~Microsoft windows~Operating systems~Operations~Organizational skills~Peripheral devices~Planning~Project management~Research information~Software installation~Technical support~Testing methodologies~Troubleshooting~Virtual private networks~Windows servers~Writing',
       -- aiImpact
       'More than one out of ten skills will have increased relevance while a similar number may decrease in the near future.~While IT Support Technicians perform essential tasks, the repetitive nature of nearly half of these duties means they could be automated in the long term with AI advancements. As technology evolves, the remaining one third of tasks requiring human presence could be augmented.',
       -- keyInsights
       'Gen AI may have a moderate to transformative impact on IT Support Technicians. While human interaction and problem-solving skills will remain crucial, AI-powered tools have the potential to streamline many routine tasks and enhance the efficiency of issue resolution. Gen AI may increasingly assist with tasks such as question handling, initial responses, case status summarization, recommending knowledge articles, software patching, resolution summarization, and lower complexity ticket resolution. IT Support Technicians will need to adapt by developing new skills in AI tool utilization and focusing on complex troubleshooting and customer service interactions. Overall, AI can help IT Support Technician become even more strategic and customer centric. By embracing AI as a collaborative tool and developing the necessary skills, IT workers can provide better support experiences, solve more complex problems, and ultimately enhance the value they bring to their organizations. Understanding integration capabilities of Gen AI into existing systems will also be important for this role.',
       -- aiTransformation
       'Low'
FROM [dbo].[pathways] p
WHERE p.pathway_title = 'Infrastructure and Operations';

INSERT INTO [dbo].[JobRole] (
    id, title, pathwayId, jobLevel,
    jobDescription, principalTasks, principalSkills,
    aiImpact, keyInsights, aiTransformation
)
SELECT NEWID(),
       'Network Administrator',
       p.pathway_id,
       'Mid-level',
       -- jobDescription
       'Network Administrators install, configure, and maintain an organization’s network infrastructure, including routers, switches, and wireless access points. They monitor network performance, troubleshoot issues, and ensure security by managing access controls and applying updates. Additionally, they develop disaster recovery plans, provide technical support, train users, and document network configurations. They also stay updated on technological advancements and ensure compliance with organizational policies and legal regulations.',
       -- principalTasks
       'Install and configure network equipment, including routers, switches, and wireless access points~Develop plans and execute procedures for the disaster recovery/back up~Diagnose, troubleshoot, and resolve hardware, software, or other network and system problems~Manage access controls and network permissions for users~Regularly monitor the health and performance of the network, troubleshoot connectivity and performance problems, and provide ongoing optimization of the network~Analyze equipment performance records to determine the need for repair or replacement~Assist users with network-related inquiries and provide technical support to users for network-related issues~Perform routine network maintenance tasks and apply software updates and patches and firmware upgrades~Provide basic IT-related training to internal/external users on network use and security practices~Create and maintain detailed documentation related to network configurations~Gather data pertaining to customer needs, and use the information to identify, predict, interpret, and evaluate system and network requirements~Coordinate with vendors and with company personnel to facilitate purchases~Ensure that all network activities are compliant with organizational policies and legal regulations~Maintain an inventory of parts for emergency repairs~Keep abreast of technological advancements and integrate relevant updates into the network infrastructure',
       -- principalSkills
       'Auditing~Backup devices~CLI configuration~Communication~Coordinating~Customer service~Detail oriented~Disaster recovery~Help desk support~Information technology~Local area networks~Management~Network infrastructure~Network monitoring~Network performance management~Network protocols~Network routing~Network security~Network switches~Operating systems~Planning~Problem solving~Research information~System administration~Technical support~Troubleshooting~WAN protocols~Writing',
       -- aiImpact
       'Early Gen AI use-cases in Network Administration include documentation, help desk support, and network performance monitoring, help in configuration generation and validation, and disaster recovery. Network Administrators will need to develop AI literacy and prompt engineering to enhance traditional skills such as help desk support, IT knowledge, problem-solving, and technical support. Skills related to Command Line (CLI) Configuration, performance management, and writing may be automated. The job focus will shift towards higher-level tasks requiring human judgment on the network infrastructure, leveraging Gen AI for routine tasks, necessitating continuous learning and adaptation to new AI technologies.',
       -- keyInsights
       'In the immediate term, about one out of three skills are impacted by AI, with the majority being augmented rather than automated. In the long run, an additional quarter of skills could be automated, but the interactive and manual nature of the role will still require direct human involvement in nearly half of the skills. Early use-cases of Gen AI include documentation, help desk support, and integrating/embedding Gen AI technologies into the network for monitoring network performance, among others. LLMs can be integrated in systems to generate configurations and validate existing configurations, analyze logs, monitor performance and detect potential network and system problems to invoke Disaster Recovery (DR) protocols. Network Administrators will need to cultivate awareness of Gen AI technologies, as well as be equipped with strong prompt engineering skills to effectively interact with AI assistants.',
       -- aiTransformation
       'Low'
FROM [dbo].[pathways] p
WHERE p.pathway_title = 'Infrastructure and Operations';

INSERT INTO [dbo].[JobRole] (
    id, title, pathwayId, jobLevel,
    jobDescription, principalTasks, principalSkills,
    aiImpact, keyInsights, aiTransformation
)
SELECT NEWID(),
       'Network and IT Automation Engineer',
       p.pathway_id,
       'Mid-level',
       -- jobDescription
       'A Network and IT Automation Engineer is responsible for designing, implementing, and maintaining automated solutions to optimize network and IT operations. They collaborate with teams to select and integrate appropriate automation technologies, ensuring stability, security, and scalability of systems. Their role involves evaluating emerging technologies, developing automated testing and security measures, and establishing standards to meet organizational requirements. Additionally, they create application-specific automation scripts, monitor network performance, and implement Continuous Integration/Continuous Deployment (CI/CD) pipelines to streamline software delivery and infrastructure changes. Overall, their work aims to enhance efficiency, reliability, and responsiveness within network and IT environments.',
       -- principalTasks
       'Verify stability, interoperability, portability, security, or scalability of network and IT automation architecture~Collaborate with engineers or software developers to select and implement appropriate automation solutions or ensure the compatibility of automated components~Identify system data, hardware, or software components required to meet user needs~Communicate with staff or clients to understand specific system requirements~Automate testing to verify proper functioning of software patches and fixes~Develop and implement automated security measures~Design, document, and direct automated deployment processes~Develop automated systems for monitoring network performance, detecting anomalies, and triggering automated responses~Evaluate current or emerging technologies for network and IT automation, considering factors such as cost, portability, compatibility, or usability~Establish functional or system standards to address operational requirements, quality requirements, and design constraints~Investigate system component suitability for specified purposes and make recommendations regarding component use~Complete models and simulations, using automated tools, to analyze or predict system performance under different operating conditions~Develop efficient and effective network automation controllers~Evaluate existing systems to determine effectiveness and suggest changes to meet organizational requirements~Develop and maintain automated solutions for configuring and managing network devices~Develop application-specific automation scripts and software~Implement CI/CD pipelines and collaborate with DevOps teams to automate software delivery and infrastructure changes',
       -- principalSkills
       'Automation~Ci/CD~Communication~Configuration management~DevOps~Innovation~Management~Network automation~Network engineering~Network infrastructure~Network monitoring~Network security~Networking hardware~Operating systems~Operations~Planning~Scalability~Scripting~Software development~Test automation~Troubleshooting~Workflow management',
       -- aiImpact
       'Gen AI will significantly enhance the role of Network and IT Automation Engineers by helping in creating and optimizing automation scripts, improving security measures, and advancing CI/CD pipelines. AI-driven monitoring and predictive maintenance will boost network performance and reliability. AI Assistants and AI RAG-based systems are crucial, aiding engineers in decision-making and troubleshooting. Leveraging Gen AI to automate routine tasks and initial development efforts will allow these engineers to focus more on complex problem-solving, strategic planning and innovation. Maintaining and developing a deep understanding of business use cases to ensure the successful application of automated solutions will be an area for workers in this role to focus on.',
       -- keyInsights
       'Two-thirds of the skills are exposed to Gen AI, with the majority of them being augmented by AI tools. In the long run, an additional small fraction of skills could be automated, but the high consequence of errors associated with this work will still necessitate direct human involvement in nearly a quarter of the skills. These could be augmented with advanced Gen AI. Gen AI can help Network and IT Automation Engineers streamline processes and enhance efficiency, including summarizing data sheets and finding solutions that align with pre-defined requirements and generating starter code or component pieces to reduce initial coding effort. If integrated in the appropriate systems, LLMs can help with path verification, test development and execution. Network and IT Automation Engineers will need to be equipped with strong prompt engineering skills to effectively interact with AI assistants as well as understand how Gen AI can be leveraged in generating scripts and code snippets for automation. They are going to play a vital role in building retrieval augmented generation (RAG) capabilities to automate work.',
       -- aiTransformation
       'High'
FROM [dbo].[pathways] p
WHERE p.pathway_title = 'Infrastructure and Operations';

INSERT INTO [dbo].[JobRole] (
    id, title, pathwayId, jobLevel,
    jobDescription, principalTasks, principalSkills,
    aiImpact, keyInsights, aiTransformation
)
SELECT NEWID(),
       'Network Support Technician',
       p.pathway_id,
       'Entry level',
       -- jobDescription
       'Network Support Technicians ensure the effective operation and security of computer networks by conducting regular updates, monitoring performance, and responding to alerts. They provide technical support and basic training to users, perform routine maintenance and repairs, and handle the installation and configuration of network hardware and software. Additionally, they contribute to document technical solutions, work within compliance and security standards, and generate reports to keep stakeholders informed about network status and issues.',
       -- principalTasks
       'Conduct regular updates and patching of software and systems, checking for vulnerabilities to maintain security and functionality~Utilize network monitoring tools to evaluate and analyze network performance and respond to network alerts~Contribute to document technical solutions and troubleshooting procedures to resolve issues~Install network software, including security or firewall software~Provide technical support for computers and associated networks, including troubleshooting and resolving hardware, software, and network issues~Provide direct support to users, including on-site and remote assistance~Perform routine maintenance and standard repairs on network equipment such as routers, switches, modems, cables, and peripheral devices~Install and configure hardware or software systems or components, ensuring integration with existing network systems~Install or repair network cables, including fiber optic cables~Contribute to create and update technical documentation for network installations or changes to existing installations~Train users on basic procedures related to network applications software or related systems~Test repaired items to ensure proper operation~Install and configure wireless networking equipment~Generate reports on network status, incident management, and resolution outcomes to keep stakeholders informed~Utilize ticketing systems to log, track, and manage issues. Review the trouble ticket queue to identify issues that need to be addressed and provide timely updates in the ticketing system of the work performed~Create or revise user instructions, procedures, or manuals~Monitor and manage compliance with relevant security standards, ensuring that network activities meet required security benchmarks',
       -- principalSkills
       'Communication~Computer hardware~Computer networks~Customer service~Detail oriented~Help desk support~Issue tracking~Local area networks~Management~Network monitoring~Network routing~Network switches~Networking hardware~Operating systems~Peripheral devices~Technical support~Wide area networks edge connectivity~Writing',
       -- aiImpact
       'Gen AI has a limited impact on the skillsets of Network Support Technicians in the near term, as the role still involves many interactive and manual tasks. In the long run, AI technology maturity can significantly impact this role by automating away many manual and repetitive tasks. Currently, routine tasks like integration could extend to test building, network monitoring, and security compliance. The job focus will shift from routine tasks to managing Gen AI technologies in the workflows, requiring technicians to develop AI literacy and prompt engineering skills to interact effectively with AI assistants.',
       -- keyInsights
       'Currently about 1 out of 10 skills are likely to be impacted by Gen AI in the near term~Due to the low barriers to adoption, about two out of three skills could be automated in the long run as Gen AI technologies advance. However, the interactive and manual nature of the role will still require direct human involvement in nearly one out of five skills~Early use-cases of Gen AI include automating email responses to issues, issue tracking, and generating documentation of issue resolution, among others~Network Support Technicians will need to cultivate awareness of Gen AI technologies, as well as be equipped with strong prompt engineering skills to effectively interact with AI assistants.',
       -- aiTransformation
       'Low'
FROM [dbo].[pathways] p
WHERE p.pathway_title = 'Infrastructure and Operations';

INSERT INTO [dbo].[JobRole] (
    id, title, pathwayId, jobLevel,
    jobDescription, principalTasks, principalSkills,
    aiImpact, keyInsights, aiTransformation
)
SELECT NEWID(),
       'Senior Network Engineer',
       p.pathway_id,
       'Senior level',
       -- jobDescription
       'Senior Network Engineers design, implement, and maintain optimal network infrastructures and are skilled in networking technologies, hardware, and software. Their tasks include configuring network equipment, troubleshooting, optimizing performance, and ensuring security. They work with virtual servers, cloud technologies, and emerging standards. They collaborate with teams, lead junior engineers, stay updated on technological advancements, and foster a culture of innovation and automation.',
       -- principalTasks
       'Collaborate with architects to design and implement efficient networks~Build and maintain robust network infrastructure~Manage alignment of network infrastructure with technical requirements~Develop and verify disaster recovery plans~Maintain network compliance with industry standards~Review and implement updates and patches for network systems~Delegate and oversee network maintenance tasks~Provide technical advice on network equipment procurement~Implement automation workflows for network issues~Oversee development and maintenance of LAN/WAN and other services~Evaluate new technologies for network enhancement~Prepare and execute network test plans~Implement network security measures~Troubleshoot and resolve network technical problems~Review and ensure compliance with information security policies~Mentor junior engineers',
       -- principalSkills
       'Automation~Communication~Firewall~Innovation~Leadership~Management~Network architecture~Network design~Network engineering~Network infrastructure~Network management~Network monitoring~Network performance management~Network quality of service~Network security~Problem solving~Python~Routing protocols~Sd-wan~Scripting~Troubleshooting',
       -- aiImpact
       'The role of Senior Network Engineers will increasingly incorporate AI-driven tools for network monitoring, troubleshooting, configuration management, and security. AI will automate routine tasks like anomaly detection, log analysis, and generating network configurations, shifting the focus to higher-level strategic roles. Skills in Gen AI, predictive data analytics (ML), and cybersecurity will become vital. Cloud technologies and virtualization will continue to be essential, enhanced by AI’s optimization capabilities. AI-assisted configuration will progressively aid in creating and maintaining network and security configurations. Senior Network Engineers must understand the capabilities and limitations of various AI models and balance automation benefits with accurate risk evaluation and management. Learning agility will be key to keeping up with rapid AI advancements. Knowledge in responsible AI use and governance is necessary to ensure secure AI deployment. Overall, the role will emphasize strategic thinking, ethical oversight, and innovative problem-solving while maintaining core networking expertise.',
       -- keyInsights
       'AI has high transformation potential in areas like network monitoring, configuration management, and network security. It can assist in troubleshooting, network optimization, and R&D, but strategic tasks such as network planning, vendor communication, and mentorship will still require human expertise. Senior Network Engineers should develop skills in Gen AI, cybersecurity, and predictive analytics, and understand AI governance and ethical use. They must be able to evaluate AI solutions critically and ensure effective deployment that aligns with business objectives.',
       -- aiTransformation
       'High'
FROM [dbo].[pathways] p
WHERE p.pathway_title = 'Infrastructure and Operations';

INSERT INTO [dbo].[JobRole] (
    id, title, pathwayId, jobLevel,
    jobDescription, principalTasks, principalSkills,
    aiImpact, keyInsights, aiTransformation
)
SELECT NEWID(),
       'Systems Administrator',
       p.pathway_id,
       'Mid-level',
       -- jobDescription
       'A Systems Administrator (SysAdmin) manages and maintains an organization’s IT infrastructure, including hardware, software, and networks. They ensure system efficiency, perform upgrades, provide technical support, manage security protocols, and resolve IT issues to keep operations running smoothly. Their role is crucial for stable and secure IT functionality.',
       -- principalTasks
       'Maintain and administer systems~Performance monitoring and optimization~User access and permissions management~System troubleshooting~Network and system security~Security threat monitoring~Data backup and disaster recovery~Technical support~Hardware and software management~Automation of routine tasks~Infrastructure change management~Documentation maintenance and compliance~Resource planning and capacity management~Vendor and third-party coordination',
       -- principalSkills
       'Access management (Active directory, LDAP, IAM)~Backup devices~Cloud service (e.g., Microsoft Azure, AWS)~Configuration management (Ansible, Terraform, Puppet, Chef)~Cybersecurity~Disaster recovery~Local area networks (LANs)~Managing Linux and Windows servers~Operating systems (Linux, Windows 10; Unix)~Scripting (Python, PowerShell, Bash)~SQL~System administration~TCP/IP~Technical support~Virtualization',
       -- aiImpact
       'Gen AI will significantly automate routine tasks like log analysis, script generation, and basic troubleshooting. This will free up Systems Administrators from mundane work and allow them to focus on more complex and strategic issues. AI can analyze vast amounts of data and provide insights that help Systems Administrators make better decisions about system configuration, capacity planning, and security. The role of Systems Administrators will likely evolve into a more strategic and collaborative position, requiring a deeper understanding of business goals and the ability to leverage AI effectively to achieve them.',
       -- keyInsights
       'AI empowers Systems Administrators by automating routine tasks like log analysis and providing intelligent insights for faster problem resolution. However, human expertise remains essential for complex troubleshooting, critical decision-making in incidents, and innovative solutions to unforeseen challenges. While AI enhances efficiency, it''s the combination of human and AI capabilities that ensures the smooth operation and security of IT systems.',
       -- aiTransformation
       'High'
FROM [dbo].[pathways] p
WHERE p.pathway_title = 'Infrastructure and Operations';

INSERT INTO [dbo].[JobRole] (
    id, title, pathwayId, jobLevel,
    jobDescription, principalTasks, principalSkills,
    aiImpact, keyInsights, aiTransformation
)
SELECT NEWID(),
       'Systems Analyst',
       p.pathway_id,
       'Mid-level',
       -- jobDescription
       'Systems Analysts evaluate current IT systems to ensure they meet business and technical requirements, identifying areas for troubleshooting, upgrading, and maintenance. They design and deploy software solutions that enhance workflow and productivity, collaborating closely with developers and other IT workers. Systems Analysts ensure clear communication of system changes to workers and provide training and support to facilitate smooth adoption of new technologies.',
       -- principalTasks
       'System evaluation and improvement: Analyzing existing IT systems and business models, identifying inefficiencies or needs, and developing solutions to enhance business processes and system functionality~Technology integration and deployment: Designing, testing, and implementing new system solutions and overseeing the configuration and deployment of these solutions to ensure they meet business requirements~Ongoing system maintenance and support: Managing routine system maintenance, providing ongoing support, and troubleshooting, and updating systems as necessary to adapt to changing business conditions and technology advancements',
       -- principalSkills
       'Active directory~Business analysis~Microsoft SQL server~SharePoint~Software development cycle~Software documentation~SQL~Visio~Windows server',
       -- aiImpact
       'Gen AI may be able to help accomplish many of the tasks for which this role is responsible, leaving more time for people in this role to focus on higher value-added complementary skills. Specifically for Systems Analysts, this may involve leveraging Gen AI to draft documentation and accelerate troubleshooting processes.',
       -- keyInsights
       'In thinking about professional development and upskilling plans, people currently in this role might consider how to use Gen AI to dramatically reduce time spent troubleshooting, how to leverage Gen AI to increase productivity working with SQL, and how to spend more time specializing with specific types of data systems (e.g., healthcare data, etc.).',
       -- aiTransformation
       'Moderate'
FROM [dbo].[pathways] p
WHERE p.pathway_title = 'Infrastructure and Operations';

-- SOFTWARE DEVELOPMENT:
-- Entry level: AI / ML Engineer, Application Developer, Back-End Developer, Cloud Engineer, Front-End Developer, Full Stack Developer, Java Developer, Python Developer, Web Developer
-- Mid-level: Software Architect, Software Developer, Software Engineer
-- Senior level: Principal Software Engineer, Senior Software Development Engineer, Senior Software Engineer
INSERT INTO [dbo].[JobRole] (
    id, title, pathwayId, jobLevel,
    jobDescription, principalTasks, principalSkills,
    aiImpact, keyInsights, aiTransformation
)
SELECT NEWID(),
       'AI/ML Engineer',
       p.pathway_id,
       'Entry level',
       -- jobDescription
       'AI/ML Engineers analyze large datasets using statistical software, apply ML techniques to predict outcomes, and propose data-driven solutions to business problems. The role includes tasks such as cleaning and manipulating data, comparing models, creating visualizations to convey results, and presenting findings to stakeholders. Additionally, the role involves developing, deploying, and optimizing ML models, staying updated on advancements in the field.',
       -- principalTasks
       'Analyze, manipulate, or process large sets of data using statistical software~Apply feature selection algorithms to models predicting outcomes of interest, such as sales, attrition, and healthcare use~Clean and manipulate raw data using statistical software~Compare models using statistical performance metrics, such as loss functions or proportion of explained variance~Create graphs, charts, or other visualizations to convey the results of data analysis using specialized software~Deliver oral or written presentations of the results of mathematical modeling and data analysis to management or other end users~Identify business problems or management objectives that can be addressed through data analysis~Identify relationships and trends or any factors that could affect the results of research~Identify solutions to business problems, such as budgeting, staffing, and marketing decisions, using the results of data analysis~Propose solutions in engineering, science, and other fields using mathematical theories and techniques~Read scientific articles, conference papers, or other sources of research to identify emerging analytic trends and technologies~Recommend data-driven solutions to key stakeholders~Test, validate, and reformulate models to ensure accurate prediction of outcomes of interest~Write new functions or applications in programming languages to conduct analyses~Deploy and maintain ML models in production environments~Optimize and fine-tune ML models for performance~Implement and manage version control for ML models~Collaborate with software engineers and IT teams for seamless integration of ML solutions~Stay updated on advancements in ML frameworks, libraries, and tools~Conduct feasibility studies for the implementation of new ML technologies',
       -- principalSkills
       'Algorithms~Artificial intelligence~Big data~C++~Collaboration~Communication~Data analysis~Data engineering~Data pipelines~Data science~Data visualization~Feature selection~Hyperparameter optimization~Innovation~Java~Machine learning~Management~Mathematics~Operations~Presentations~Problem solving~Python~R~Research information~Software engineering~SQL~Statistics~Version control~Workflow management~Writing',
       -- aiImpact
       'The impact of Gen AI on the skillsets of AI/ML Engineers is significant. Gen AI will play a key role in code-writing assistance, experiment and research result summarization, report writing, and creating frameworks for feasibility studies. However, AI/ML Engineers will still need to validate and implement Gen AI''s code output, highlighting the importance of maintaining a deep technical understanding. AI/ML Engineers will need to adapt to a future where Gen AI plays a significant role in code-writing and task automation. This requires a shift in focus towards higher-level problem-solving, prompt engineering, and a deep understanding of LLM architecture to build AI tools or leverage them effectively while maintaining the integrity and quality of their work.',
       -- keyInsights
       'Approximately two-thirds of the skills will be impacted by Gen AI, with around half potentially becoming less relevant due to the possibility of automation. In the long run, another small fraction of skills may be automated, but a significant portion will still require a deep understanding of the business context, necessitating direct human involvement. These skills can be further enhanced with advanced Gen AI. AI/ML Engineers will need a deep, technical understanding of LLM architecture as they will be part of the teams building these models in the future. They will also need to be wary of risks of skill erosion—while Gen AI will be able to write code for them, they will still need to be able to validate and appropriately implement Gen AI’s code output.',
       -- aiTransformation
       'High'
FROM [dbo].[pathways] p
WHERE p.pathway_title = 'Software Development';

INSERT INTO [dbo].[JobRole] (
    id, title, pathwayId, jobLevel,
    jobDescription, principalTasks, principalSkills,
    aiImpact, keyInsights, aiTransformation
)
SELECT NEWID(),
       'Application Developer',
       p.pathway_id,
       'Mid-level',
       -- jobDescription
       'Application developers are responsible for designing, coding, and testing software applications for various platforms such as mobile, web, or desktop. They collaborate with other team members to ensure the functionality and usability of the applications meet the requirements and deliver a seamless user experience.',
       -- principalTasks
       '• Agile methodology: Employing agile methodologies such as scrum or kanban to manage the software development lifecycle and improve development processes~• Communication: Effectively communicating project status, proposals, and technical issues to team members and stakeholders in a clear and understandable manner~• Documentation maintenance: Creating and maintaining system and user documentation, ensuring that documentation is updated with each software or system change~• Interpersonal collaboration: Working with other developers, IT staff, and external stakeholders to ensure successful project outcomes while facilitating effective team collaboration~• Project management: Managing timelines, resources, and stakeholder expectations for application development projects while ensuring that deadlines and budget constraints are met~• Software architecture design: Designing and implementing robust software architecture to support enterprise or client-specific applications~• Software development: Writing, modifying, and debugging software for client applications using source debuggers and visual development environments to develop software baselines~• System integration: Integrating various software components and systems to work together seamlessly, ensuring system interoperability and functionality~• Technical knowledge application: Applying deep technical knowledge of programming languages, frameworks, and development tools to solve complex development challenges~• Testing and troubleshooting: Testing software to identify and resolve issues, bugs, and integration challenges, and enhancing application performance based on testing results',
       -- principalSkills
       'Agile methodology~Communication~Demonstrating responsibility~Development design~Documentation maintenance~Integration software~Interpersonal collaboration~Java~Problem solving~Project team management~Software development~Software product management~System architecture~Testing~Time management~Web development',
       -- aiImpact
       'AI impact on the Application Developer role might be moderate to high. While skills like testing and project team management remain less affected, AI can significantly automate documentation and assist with system architecture. Application Developers should focus on upskilling in areas like development design and software product management, where AI can complement their work. Key technical skills like integration software, software development, Java, and JavaScript are highly susceptible to AI automation.',
       -- keyInsights
       '• Impact on number of hours: Gen AI can potentially automate a significant portion of an Application Developer''s tasks, particularly in areas like documentation and software development~• New skills: Application Developers will need to develop skills in AI-related technologies such as TensorFlow, image signal processing, Azure Cognitive Services, AI model development, machine vision, and AI integration to stay competitive~• Skills in demand: Despite AI''s growing role, the importance of soft skills such as demonstrating responsibility, communication, and interpersonal collaboration will remain high, as these are crucial for effective teamwork and project management',
       -- aiTransformation
       'Moderate'
FROM [dbo].[pathways] p
WHERE p.pathway_title = 'Software Development';

INSERT INTO [dbo].[JobRole] (
    id, title, pathwayId, jobLevel,
    jobDescription, principalTasks, principalSkills,
    aiImpact, keyInsights, aiTransformation
)
SELECT NEWID(),
       'Back-End Developer',
       p.pathway_id,
       'Mid-level',
       -- jobDescription
       'Back-End Developers develop and maintain server-side logic and database structures. They collaborate with front-end developers to integrate user-facing elements with server-side logic and ensure high performance and responsiveness of back-end services and databases.',
       -- principalTasks
       '• Development and maintenance: Creating and maintaining the core application logic, databases, and server-side processes that power a website or application''s functionality.~• Integration services: Developing APIs and integration services to ensure that different systems and applications can communicate effectively, supporting front-end applications and other system integrations.~• Performance optimization: Optimizing the website or application for speed and efficiency, ensuring high performance and scalability of the database and backend systems.',
       -- principalSkills
       'AWS~Docker Products~Git~MongoDB~MySQL~Node.js~PostgreSQL~Python~React.js',
       -- aiImpact
       'Gen AI may be able to help accomplish many of the tasks for which this role is responsible, leaving more time for people in this role to focus on higher value-added complementary skills. Specifically for Back-End Developers, this may mean using Gen AI to accelerate coding and troubleshooting, particularly with tools like Python.',
       -- keyInsights
       'In thinking about professional development and upskilling plans, people currently in this role might consider how to use Gen AI to dramatically reduce time spent working with Python, how to leverage Gen AI to increase productivity working with object-oriented programming, and how to spend more time working on microservices.',
       -- aiTransformation
       'Moderate'
FROM [dbo].[pathways] p
WHERE p.pathway_title = 'Software Development';


INSERT INTO [dbo].[JobRole] (
    id, title, pathwayId, jobLevel,
    jobDescription, principalTasks, principalSkills,
    aiImpact, keyInsights, aiTransformation
)
SELECT NEWID(),
       'Cloud Engineer',
       p.pathway_id,
       'Entry level',
       -- jobDescription
       'Cloud Engineers are responsible for cloud infrastructure design and management, automation & optimization, and security & compliance. They design, implement, and manage cloud infrastructure solutions using platforms such as AWS, Azure, or Google Cloud, including setting up virtual networks, storage solutions, and computing resources. They develop and maintain automation scripts and tools to streamline cloud operations, improve system performance, and ensure efficient resource utilization, implementing Infrastructure as Code (IaC) practices using tools like terraform or cloud formation. They also ensure cloud environments adhere to security best practices and compliance standards by monitoring for vulnerabilities, implementing encryption protocols, and managing identity and access management (IAM) policies.',
       -- principalTasks
       'Automating cloud infrastructure: Creating and managing automation scripts and tools, such as Terraform or Ansible, to automate the deployment, scaling, and management of cloud infrastructure, ensuring efficient and consistent operations~Deploying and configuring cloud resources: Setting up and configuring virtual servers, storage systems, databases, and networking components on cloud platforms like Azure, AWS, or Google Cloud to support business applications and services~Monitoring and optimizing cloud performance: Monitoring cloud infrastructure for performance issues, security threats, and cost inefficiencies, implementing optimization strategies and troubleshooting problems to maintain optimal system performance and security',
       -- principalSkills
       'Ansible~AWS~Bash~Cloud compute~Kubernetes~Linux~Microsoft Azure~Powershell~Terraform',
       -- aiImpact
       'As Gen AI is adopted more broadly, these jobs will undergo reskilling, possibly leading to more innovation. Specifically for Cloud Engineers, this may mean understanding how to use Gen AI to increase productivity when generating automation scripts.',
       -- keyInsights
       'In thinking about professional development and upskilling plans, people currently in this role might consider how to use Gen AI to dramatically reduce time spent working with tools like Terraform, how to leverage Gen AI to increase productivity working with tools like Kubernetes, and how to spend more time working with cloud infrastructure design and development.',
       -- aiTransformation
       'High'
FROM [dbo].[pathways] p
WHERE p.pathway_title = 'Software Development';


INSERT INTO [dbo].[JobRole] (
    id, title, pathwayId, jobLevel,
    jobDescription, principalTasks, principalSkills,
    aiImpact, keyInsights, aiTransformation
)
SELECT NEWID(),
       'Front-End Developer',
       p.pathway_id,
       'Entry level',
       -- jobDescription
       'Front-End Developers develop and implement user interfaces for websites and web applications using technologies such as HTML, CSS, and JavaScript to create engaging and functional user experiences​. They collaborate with back-end developers and web designers to integrate designs, ensure responsive performance across devices, and optimize applications for speed and scalability and maintain up-to-date knowledge of industry trends and technologies, ensuring the continuous improvement of the user interface and staying current with best practices in web development.',
       -- principalTasks
       '• Design and user experience: Creating visually appealing and user-focused designs and ensuring that the website or application interfaces are intuitive and engaging for users~• Development and feature implementation: Building and integrating personalized and customized features into applications, translating design wireframes into functional web components using HTML, CSS, and JavaScript​~• Optimization and maintenance: Maintaining an up-to-date knowledge of the latest web technologies and industry trends and optimizing applications for maximum speed and scalability, ensuring all code is up to the standards for quality and efficiency technical knowledge',
       -- principalSkills
       'CSS~Git~HTML5~JavaScript~jQuery~Node.js~React.js~SASS~TypeScript',
       -- aiImpact
       'Gen AI may be able to help accomplish many of the tasks for which this role is responsible, leaving more time for people in this role to focus on higher value-added complementary skills. Specifically for Front-End Developers, this may involve automating simpler scripts and predicting user-friendly customizations and their underlying code.',
       -- keyInsights
       'In thinking about professional development and upskilling plans, people currently in this role might consider how to use Gen AI to dramatically reduce time spent working with CSS, how to leverage Gen AI to increase productivity working with JavaScript, and how to spend more time working with user interface design.',
       -- aiTransformation
       'Moderate'
FROM [dbo].[pathways] p
WHERE p.pathway_title = 'Software Development';

INSERT INTO [dbo].[JobRole] (
    id, title, pathwayId, jobLevel,
    jobDescription, principalTasks, principalSkills,
    aiImpact, keyInsights, aiTransformation
)
SELECT NEWID(),
       'Full-Stack Developer',
       p.pathway_id,
       'Entry level',
       -- jobDescription
       'Full Stack Developers develop and maintain both front-end and back-end components of web applications, ensuring seamless integration and functionality. They collaborate with cross-functional teams to design, implement, and optimize scalable and efficient software solutions. They stay updated with the latest industry trends and technologies to continuously improve and innovate on existing systems and processes.',
       -- principalTasks
       'Code quality and system performance: Maintaining high standards in code quality and system architecture, ensuring that applications perform reliably and efficiently, managing both the upkeep of existing systems and the introduction of new technologies~Project management: Handling end-to-end project ownership and building scalable and distributed solutions that address both front-end and back-end needs, ensuring the software delivers a positive user experience and supports business growth~Feature development and infrastructure enhancement: Developing new features and enhancing infrastructure to meet rapidly changing business and project requirements, not only through coding but also planning and conceptualizing new projects before actual deployment~Agile methodology: Implement and follow agile practices such as scrum to manage projects and improve development efficiency~Continuous integration and continuous delivery (CI/CD): Set up and manage CI/CD pipelines to automate testing and deployment processes~Documentation maintenance: Create and maintain software documentation to ensure that all processes and code are clearly documented~Interpersonal collaboration: Work collaboratively with other team members, including cross-functional collaboration to achieve project goals~Java programming: Write and optimize Java code by utilizing advanced features such as Java Enums, the Java Stream API, and the Java Files API~Problem solving: Address and resolve complex software issues and bugs, employing strong analytical and problem-solving skills~Software design patterns: Apply design patterns and architectural principles to develop maintainable and scalable software~Software development: Design, code, and debug applications in various software languages including Java~System integration: Integrate software components into a fully functional software system~Testing: Conduct software testing to ensure quality and identify defects, including development testing and unit testing',
       -- principalSkills
       'Angular~CSS~Git~HTML5~JavaScript~MongoDB~Node.JS~React.js~TypeScript~Adaptability~Agile methodology~Communication~Creativity~Demonstrating responsibility~Development design~Engineering software~Enterprise software~Interpersonal collaboration~Java~Leadership demonstration~Problem-solving~Software development~Software integration~Software product management~System architecture~Testing~Web development',
       -- aiImpact
       'Gen AI may be able to help accomplish many of the tasks for which this role is responsible, leaving more time for people in this role to focus on higher value-added complementary skills. Specifically for Full Stack Developers, this may involve automating simpler scripts and enhancing skills related full project management and strategic feature design.',
       -- keyInsights
       'In thinking about professional development and upskilling plans, people currently in this role might consider how to use Gen AI to dramatically reduce time spent working with CSS, how to leverage Gen AI to increase productivity working with JavaScript, and how to spend more time working on microservices.',
       -- aiTransformation
       'Moderate'
FROM [dbo].[pathways] p
WHERE p.pathway_title = 'Software Development';

INSERT INTO [dbo].[JobRole] (
    id, title, pathwayId, jobLevel,
    jobDescription, principalTasks, principalSkills,
    aiImpact, keyInsights, aiTransformation
)
SELECT NEWID(),
       'Java Developer',
       p.pathway_id,
       'Entry level',
       -- jobDescription
       'A Java developer is a software engineer specializing in developing applications using the Java programming language. They are responsible for designing, coding, and testing software solutions, as well as troubleshooting and maintaining existing Java-based applications.',
       -- principalTasks
       'Java programming: Write and optimize Java code by utilizing advanced features such as Java Enums, the Java Stream API, and the Java Files API~Problem solving: Address and resolve complex software issues and bugs, employing strong analytical and problem-solving skills~Software design patterns: Apply design patterns and architectural principles to develop maintainable and scalable software~Software development: Design, code, and debug applications in various software languages including Java~System integration: Integrate software components into a fully functional software system~Testing: Conduct software testing to ensure quality and identify defects, including development testing and unit testing~Agile methodology: Implement and follow agile practices such as scrum to manage projects and improve development efficiency~Documentation maintenance: Create and maintain software documentation to ensure that all processes and code are clearly documented~Interpersonal collaboration: Work collaboratively with other team members, including cross-functional collaboration to achieve project goals',
       -- principalSkills
       'Adaptability~Agile methodology~Communication~Creativity~Demonstrating responsibility~Development design~Engineering software~Enterprise software~Interpersonal collaboration~Java~Leadership demonstration~Problem-solving~Software development~Software integration~Software product management~System architecture~Testing~Web development',
       -- aiImpact
       'AI impact on the Java Developer role might be moderate to high. While skills like testing and engineering software are less affected, AI can significantly automate software development, integration, and assist with system architecture. Java Developers should focus on upskilling in areas like software product management and development design, where AI can complement their work. Key technical skills like Java and web development are highly susceptible to AI automation.',
       -- keyInsights
       'Impact on number of hours: Gen AI can significantly automate tasks related to Java programming, software integration, and development~New skills: Java developers will need to acquire skills in computer vision, natural language processing, TensorFlow, image signal processing, AI model development, cloud AI, prompt engineering, and AI optimization to stay competitive~Skills in demand: Soft skills such as demonstrating responsibility, problem solving, and communication will remain essential for Java Developers, as they often collaborate with cross-functional teams',
       -- aiTransformation
       'Moderate'
FROM [dbo].[pathways] p
WHERE p.pathway_title = 'Software Development';

INSERT INTO [dbo].[JobRole] (
    id, title, pathwayId, jobLevel,
    jobDescription, principalTasks, principalSkills,
    aiImpact, keyInsights, aiTransformation
)
SELECT NEWID(),
       'Principal Software Engineer',
       p.pathway_id,
       'Senior level',
       -- jobDescription
       'A Principal Software Engineer leads the design, development, and deployment of complex software systems, ensuring high performance and scalability. Responsibilities include setting technical direction, mentoring engineers, and collaborating with stakeholders on strategic projects. Expertise in system architecture, coding, and leadership skills are essential.',
       -- principalTasks
       'Lead software development efforts and mentor team members in best practices and techniques~Apply agile methodologies to software development processes for iterative and adaptive delivery~Utilize XML for data representation and configuration in software applications~Design and develop distributed systems to handle large-scale data processing and analysis~Develop Perl scripts for automation and system administration tasks in Unix/Linux environments~Design and implement object-oriented software solutions for complex business requirements~Develop software for embedded systems and IoT devices, optimizing for performance and reliability~Design and develop web applications using modern frameworks like Spring~Implement multithreading and concurrency mechanisms to improve application performance~Develop and execute test automation scripts to ensure software quality and reliability',
       -- principalSkills
       'Agile methodologies~C++~Debugging~Device drivers~Distributed systems~Embedded systems~Multithreading~Object oriented design~Perl~Shell scripting~SOA~Software design platforms~Software development~Spring framework~System architecture~Test automation~Tomcat~Web applications~Web services~XML',
       -- aiImpact
       'AI impact on the role might be moderate. Engineers will focus on upskilling in areas like advanced system architecture, strategic project leadership, and AI integration strategies. While AI can automate routine coding and optimize workflows, the human elements of creativity, mentorship, and complex decision-making remain essential.',
       -- keyInsights
       'AI can augment many aspects of the Principal Software Engineer role but cannot fully replace the essential human elements of creativity, mentorship, strategic thinking, and complex decision-making. System architecture, project leadership, security, innovation, and mentoring require human expertise, while AI tools can assist with performance optimization, code generation, and vulnerability detection.',
       -- aiTransformation
       'Moderate'
FROM [dbo].[pathways] p
WHERE p.pathway_title = 'Software Development';

INSERT INTO [dbo].[JobRole] (
    id, title, pathwayId, jobLevel,
    jobDescription, principalTasks, principalSkills,
    aiImpact, keyInsights, aiTransformation
)
SELECT NEWID(),
       'Python Developer',
       p.pathway_id,
       'Entry level',
       -- jobDescription
       'Python Developers analyze requirements and design system installations or modifications using Python, ensuring feasibility within time and cost constraints. They collaborate with stakeholders to gather information and coordinate project activities. Additionally, they develop, modify, and test software systems and stay updated on advancements in Python and related technologies.',
       -- principalTasks
       'Analyze requirements to recommend and plan the installation or modification of systems, leveraging Python for efficient and effective solutions~Analyze user needs and software requirements to determine feasibility of design within time and cost constraints~Confer with data processing or project managers to obtain information on limitations or capabilities for data processing projects~Confer with systems analysts, engineers, programmers and others to design systems and to obtain information on project limitations and capabilities, performance requirements and interfaces~Consult with customers and departments on project status, proposals, and technical issues, focusing on Python-based software system design and maintenance~Coordinate the installation of Python-based software systems~Design, develop and modify software systems using Python, leveraging scientific analysis and mathematical models to predict and measure outcomes and consequences of design~Determine system performance standards~Develop or direct Python-based software testing or validation procedures, programming, or documentation~Modify existing software to correct errors, adapt it to new hardware, or upgrade interfaces and improve performance~Obtain and evaluate information on factors such as reporting formats required, costs, or security needs to determine hardware configuration~Prepare reports or correspondence related to Python project specifications, activities, or status~Store, retrieve, and manipulate data for analysis of system capabilities and requirements~Supervise and assign work to programmers, designers, technologists, technicians, or other engineering or scientific personnel~Stay updated on the latest developments in Python and related technologies, incorporating new features and improvements into projects',
       -- principalSkills
       'Big data~Business requirements~Collaboration~Communication~Configuration management~Data engineering~Debugging~Machine learning~Management~Planning~Problem solving~Python~Research information~Software engineering~SQL~Test automation~Unit testing~Writing',
       -- aiImpact
       'Gen AI is set to significantly transform the skillsets required for Python Developers. In the near term, 61% of their skills will be impacted, with 22% of these skills being augmented to boost efficiency and 39% of skills that heavily relate to coding could be at risk of displacement. As such, developers will transition from a primary focus on writing code to understanding and addressing business problems, use cases, and success measures. They will play a critical role in integrating Gen AI solutions into business processes, requiring them to have a comprehensive understanding of both technical and business aspects.',
       -- keyInsights
       'More than half of the skills will likely be impacted by Gen AI in the near term, with about one-fifth of them being augmented to boost efficiency~In the long run, about one-sixth of skills could be automated, while nearly a quarter will still require direct human involvement, even with advanced Gen AI~Python Developers will need effective prompt engineering skills as well as a deep, technical understanding of LLM architecture as these workers will be responsible for designing, developing, and maintaining Gen AI applications, building core software automating tasks that will leverage Gen AI, and creating intelligent AI agents~Rather than simply focusing on writing code, Python Developers will now need to understand the core business problems, use cases and success measures as they develop software to address these items',
       -- aiTransformation
       'Moderate'
FROM [dbo].[pathways] p
WHERE p.pathway_title = 'Software Development';

INSERT INTO [dbo].[JobRole] (
    id, title, pathwayId, jobLevel,
    jobDescription, principalTasks, principalSkills,
    aiImpact, keyInsights, aiTransformation
)
SELECT NEWID(),
       'Senior Software Development Engineer',
       p.pathway_id,
       'Senior level',
       -- jobDescription
       'A Senior Software Development Engineer designs, develops, and maintains high-performance software systems, ensuring scalability and reliability. Responsibilities include advanced coding, system architecture, mentoring team members, and leading technical projects. Expertise in software engineering principles, problem-solving, and leadership skills are essential.',
       -- principalTasks
       'Utilize SQL for database querying and manipulation in software development projects~Apply agile methodologies to software development processes to enhance collaboration and flexibility~Use XML for data representation and configuration in software applications~Develop web services to enable communication between disparate systems and applications~Participate in scrum meetings and ceremonies to ensure project alignment and progress tracking~Implement Perl scripts for automation and system administration tasks~Gather and analyze requirements from stakeholders to inform software design and development~Manage software project lifecycles to ensure timely delivery and quality of deliverables~Write shell scripts to automate system tasks and operations in Unix/Linux environments~Utilize Hadoop for distributed storage and processing of large datasets in big data applications',
       -- principalSkills
       'Agile methodologies~C++~Git~Hadoop~Java~Linux~Multithreading~Object oriented design~Perl~Python~Requirements analysis~Scrum~Shell scripting~Software development life cycle~Software project management~SQL~Test automation~WCF~Web services~XML',
       -- aiImpact
       'AI impact on the Senior Software Development Engineer role might be moderate. Senior Software Development Engineers might focus on upskilling skills like advanced system architecture and leadership. While skills in coding and troubleshooting remain relevant, their demand for manual tasks will decline due to AI-assisted automation and optimization. The Senior Software Development Engineer role involves advanced technical, analytical, and mentoring tasks requiring human judgment, creativity, and interaction. AI can assist with code suggestions and optimizations but lacks the creativity and problem-solving abilities of a human engineer. AI can provide data-driven insights for architecture but cannot fully grasp complex system designs. AI can provide learning resources but cannot offer personalized guidance and support. AI can assist in tracking and optimizing workflows but cannot handle all aspects of project leadership. AI can provide insights and automation but requires human expertise for complex optimizations. AI can identify issues but may not fully understand complex problems or provide innovative solutions. AI can assist with vulnerability detection but cannot fully ensure security without human oversight. AI can suggest solutions based on data but lacks the creativity for groundbreaking innovation. Overall, AI can augment many aspects of the senior software development engineer role but cannot fully replace the essential human elements of creativity, mentorship, and complex problem-solving.',
       -- keyInsights
       'AI-driven system design: Leveraging AI tools to enhance system architecture and design~AI ethics and responsible AI: Understanding and ensuring the ethical use of AI in software development~AI literacy~AI-powered security measures: Developing and implementing AI-based security solutions',
       -- aiTransformation
       'Moderate'
FROM [dbo].[pathways] p
WHERE p.pathway_title = 'Software Development';

INSERT INTO [dbo].[JobRole] (
    id, title, pathwayId, jobLevel,
    jobDescription, principalTasks, principalSkills,
    aiImpact, keyInsights, aiTransformation
)
SELECT NEWID(),
       'Senior Software Engineer',
       p.pathway_id,
       'Senior level',
       -- jobDescription
       'A Senior Software Engineer designs, develops, and maintains complex software systems, ensuring scalability and performance. Responsibilities include code review, mentoring junior engineers, collaborating with cross-functional teams, and leading technical projects. Strong coding skills, problem-solving, and the ability to manage software development lifecycle are essential.',
       -- principalTasks
       'Develop and maintain Java-based applications and systems to meet project requirements~Apply agile methodologies to software development processes for improved efficiency~Utilize XML for data interchange and configuration in software applications~Implement web services to enable interoperability and communication between systems~Design and implement distributed systems to handle large-scale data processing and storage~Utilize Perl scripting for automation and system administration tasks~Apply object-oriented design principles to develop scalable and maintainable software solutions~Develop embedded systems software for specialized hardware platforms and devices~Design and implement web applications using modern frameworks like AngularJS~Debug and troubleshoot software issues to ensure product reliability and performance',
       -- principalSkills
       'Agile methodologies~Ajax~AngularJS~Design patterns~Eclipse~Git~Hibernate~Java~Json~MongoDB~Node.js~Object oriented design~Perl~Scrum~Shell scripting~Software development~Spring framework~Tomcat~Web services~XML',
       -- aiImpact
       'AI impact on the Senior Software Engineer role might be moderate. Senior Software Engineers might focus on upskilling skills like advanced programming and project management. While skills in code review and troubleshooting remain relevant, their demand for Senior Software Engineers will decline due to AI-assisted automation and optimization. The Senior Software Engineer role involves advanced technical, analytical, and mentoring tasks requiring human judgment, creativity, and interaction. AI can assist with code suggestions and optimizations but lacks the creativity and problem-solving abilities of a human engineer. AI can automate code quality checks but cannot fully replace human oversight and mentorship. AI can provide learning resources but cannot offer personalized guidance and support. AI can assist in tracking and optimizing workflows but cannot handle all aspects of project leadership. AI can facilitate communication but cannot replace human collaboration and relationship-building. AI can provide insights and automation but requires human expertise for complex optimizations. AI can identify issues but may not fully understand complex problems or provide innovative solutions. AI can assist with vulnerability detection but cannot fully ensure security without human oversight. Overall, AI can augment many aspects of the senior software engineer role but cannot fully replace the essential human elements of creativity, mentorship, and complex problem-solving.',
       -- keyInsights
       'AI-driven software development~AI-powered security measures~AI ethics and responsible AI: Understanding and ensuring the ethical use of AI in product development~AI literacy',
       -- aiTransformation
       'Moderate'
FROM [dbo].[pathways] p
WHERE p.pathway_title = 'Software Development';

INSERT INTO [dbo].[JobRole] (
    id, title, pathwayId, jobLevel,
    jobDescription, principalTasks, principalSkills,
    aiImpact, keyInsights, aiTransformation
)
SELECT NEWID(),
       'Software Architect',
       p.pathway_id,
       'Mid-level',
       -- jobDescription
       'Software Architects engineer end-to-end system software for a specific technology, product/platform, or market segment, including software structure and bounding box, firmware, drivers, frameworks, cross component, interfaces, interactions, interoperability, protocols, algorithms, and applications.',
       -- principalTasks
       'Pathfinding and providing technical direction for software development and validation~Engages with customers on technical requirements/discussions and interacts with technologists internally and within the industry to evaluate the feasibility of requirements and determine priorities for development~Creates specifications for software to be developed at various levels of the software stack, including software structure, interfaces, frameworks, protocols, algorithms and/or validation direction~Architecture definition~Architecture modeling~Communication of architectural intent~Customer problem solving~Full stack software frameworks~High level software design~Programming ability/languages~Prototyping~Requirement definition/design~Software debug~Software modeling, prototyping',
       -- principalSkills
       'Architecture definition~Architecture modeling~Communication of architectural intent~Customer problem solving~Full stack software frameworks~High level software design~Programming ability/languages~Prototyping~Requirement definition/design~Software debug~Software modeling, prototyping',
       -- aiImpact
       'Gen AI is a tool which will enhance the capabilities for software architecture, enabling engineers to work more efficiently in architecting software systems.',
       -- keyInsights
       'New Gen AI techniques enable:~Design assistance: suggesting design patterns or architectural components based on requirements~Technology selection of most appropriate techniques/frameworks~Performance optimization techniques~Risk analysis and security analysis~Scenario planning~Spec development and review~Documentation generation~Architecture diagram/visualization creation~New skills: AI ethics and responsible AI~AI literacy~LLM architecture and frameworks~Prompt engineering',
       -- aiTransformation
       'Moderate'
FROM [dbo].[pathways] p
WHERE p.pathway_title = 'Software Development';

INSERT INTO [dbo].[JobRole] (
    id, title, pathwayId, jobLevel,
    jobDescription, principalTasks, principalSkills,
    aiImpact, keyInsights, aiTransformation
)
SELECT NEWID(),
       'Software Developer',
       p.pathway_id,
       'Mid-level',
       -- jobDescription
       'Designs, develops, integrates, tests, validates, and/or debugs software across multiple layers of the software stack spanning firmware, drivers, operating systems, middleware, frameworks, algorithms, and applications/UI for a specific technology, product/platform, and/or market segment, including the development of software to enable specific features, capabilities, solutions and reference platforms.',
       -- principalTasks
       'Develops software at one level or across the stack, including firmware, drivers, OS, middleware, frameworks, algorithms, and applications~May specialize in specific technology domains including cloud, AI, HPC, graphics~Develops software to improve/enhance internal product development including manufacturing and product design~Develops software for improving or enabling customer designs to obtain the greatest value~Software debug/validation~Software integration~Collaborating with teams',
       -- principalSkills
       'Analytical thinking~Code review~Compliant development~Critical problem solving~DevSecOps~Effective communication~High-level software design~Programming ability/languages~Secure code development~Software debug~Software modeling~Software test engineering and test execution~Source control management~Systems thinking~Technical architecture design & governance~Data management~Identity & access management~Integration & interoperability~Performance optimization and total cost of ownership',
       -- aiImpact
       'Developers will embrace AI to automate code generation, leveraging Gen AI to work through complex problems, and automate testing.~AI will democratize the ability to write and check code which allows for more ideas but also has a risk in terms of its quality.~Employers must support their workers with tools, processes and people (enablement) to ensure that the code that makes it into production is secure, of high quality, and aids in the user experience - not AI just for AI’s sake.~As the barrier of entry to create code is lowered, other skills will become more important to ensure that code works, be able to check its quality, and think about down the line consequences of the code onto other elements of your product. This requires a deeper level of knowledge in architecture, systems thinking, etc.',
       -- keyInsights
       'Gartner has forecasted that, by 2028, as many as 3/4 enterprise Software Engineers will harness the power of AI code assistants, up from just one in 10 in 2023 (STAMFORD, Conn, 2024)~Gartner’s research found that the demand for no-code/low-code development platforms is expected to grow at least 5x faster than traditional application development through 2023~In 3-5 years, developers will evolve to think more about connected systems and architecture vs just coding. Junior developers especially will be able to focus on this',
       -- aiTransformation
       'Moderate'
FROM [dbo].[pathways] p
WHERE p.pathway_title = 'Software Development';

INSERT INTO [dbo].[JobRole] (
    id, title, pathwayId, jobLevel,
    jobDescription, principalTasks, principalSkills,
    aiImpact, keyInsights, aiTransformation
)
SELECT NEWID(),
       'Software Engineer',
       p.pathway_id,
       'Entry level',
       -- jobDescription
       'The entry level Software Engineer designs, develops, tests, and debugs responsive web applications using HTML/CSS and JavaScript. They gather user requirements, collaborate with UX/UI designers to create appealing and functional interfaces, maintain front-end and back-end applications, ensure security, optimize performance and SEO, stay current with emerging technologies, create reusable components, and participate in scrum rituals.',
       -- principalTasks
       'Participate in regular scrum ritual~Communicate with users to gather requirements and collaborate with and manage requests from UX/UI designers to reflect design intent~Contribute code to libraries and create reusable components~Create code in HTML/CSS and JavaScript~Design, develop, test, debug responsive web applications~Help maintain back-end and front-end applications and ensure web applications security~Optimize website for speed, performance and SEO~Stay up to date with emerging technologies and replace legacy technology with new ones~Use testing tools and frameworks to test and debug code and systems',
       -- principalSkills
       'Back-end development for websites~Building a webserver in Node.js~Consuming APIs~Delivery content via CMS and delivery platforms~Deploying in the cloud~Designing and creating basic functions and algorithms~DevOps~Front-end development for website including HTML5, CSS, JavaScript Git GitHub and version control~Implementing responsive images and typography~Organizing, creating, consuming, and rending data~Python~Querying media~Responsive design for mobile web development~Testing and debugging best practices and tools~Troubleshooting~Verbal and written communications',
       -- aiImpact
       'Software Engineering roles and the field at large have been an early target of disruptive artificial intelligence tools and products. That trend is accelerating. Today, workers and students of software engineering can leverage large language models (LLMs) to assist in drafting blocks of code with varying degrees of success and reliability. As these tools improve, software engineers will not only benefit from error reduction, greater efficiency, and faster testing, but also the integration of diverse AI solutions into their software. These integrations will facilitate individualized experiences for users. Additionally, Gen AI solutions which can create full web pages and applications with simple prose prompts are being developed. With the democratization and automation of code creation, software engineers will evolve towards strategic planning, increasingly complex problem solving, and AI-supported creative innovation.',
       -- keyInsights
       'Software development tools: Further advancements in AI-powered assistive technologies will help guide code development tasks and eventually take on large swaths of development with prompts and other design inputs~Quality assurance: Code review, testing, and analysis tools will help software engineers identify and resolve errors, security vulnerabilities, and inefficiencies more quickly and effectively~Interface development: Voice and chat-enabled software introduced new engineering considerations in software development, and additional AI-powered interactive advancements, like image/live video recognition and gesture controls will be impacted, especially as individualized user experiences become more popular',
       -- aiTransformation
       'High'
FROM [dbo].[pathways] p
WHERE p.pathway_title = 'Software Development';


INSERT INTO [dbo].[JobRole] (
    id, title, pathwayId, jobLevel,
    jobDescription, principalTasks, principalSkills,
    aiImpact, keyInsights, aiTransformation
)
SELECT NEWID(),
       'Web Developer',
       p.pathway_id,
       'Entry level',
       -- jobDescription
       'A Web Developer is responsible for the design and implementation of web applications. Web developers create well-designed, testable, and efficient code using best practices for web development, ensuring responsive and mobile-friendly designs. They maintain and enhance websites by maintaining, expanding, and scaling websites, addressing both front-end and back-end aspects, and ensuring website performance and reliability. They collaborate with teams and stakeholders and work closely with designers, content creators, and other stakeholders to ensure that the website meets both technical and user requirements, providing a positive user experience.',
       -- principalTasks
       'Website and application development: Designing and iterating websites, ensuring functionality, usability, and attractiveness, using standard technologies like HTML, CSS, and JavaScript~Testing and optimization: Testing websites to ensure they are bug-free and optimizing their performance to improve speed and efficiency, ensuring the best possible user experience~Maintenance and updates: Maintaining existing sites, making updates and adjustments as needed to ensure they stay current with technological advancements and continue to meet the needs of all user groups',
       -- principalSkills
       'CSS~HTML~JavaScript~jQuery~Node.js~PHP~React.js~SQL~WordPress',
       -- aiImpact
       'Gen AI may be able to help accomplish many of the tasks for which this role is responsible, leaving more time for people in this role to focus on higher value-added complementary skills. For Web Developers, this may mean leveraging tools like GitHub Copilot to make coding more efficient, or Applitools to conduct visual testing and monitoring.',
       -- keyInsights
       'In thinking about worker development and upskilling plans, people currently in this role might consider how to use Gen AI to dramatically reduce time spent working with CSS, how to leverage Gen AI to increase productivity working with JavaScript, and how to spend more time developing and maintaining web applications.',
       -- aiTransformation
       'Moderate'
FROM [dbo].[pathways] p
WHERE p.pathway_title = 'Software Development';


-- TESTING AND QUALITY ASSURANCE:
-- All roles are Entry level.
INSERT INTO [dbo].[JobRole] (
    id, title, pathwayId, jobLevel,
    jobDescription, principalTasks, principalSkills,
    aiImpact, keyInsights, aiTransformation
)
SELECT NEWID(),
       'Quality Assurance Analyst',
       p.pathway_id,
       'Entry level',
       -- jobDescription
       'A Quality Assurance Analyst is responsible for ensuring that software products and applications meet specified quality standards. They perform testing, identify defects, and collaborate with development teams to resolve issues and improve overall product quality.',
       -- principalTasks
       'Collaborate with development teams: Work closely with software developers and other project team members to ensure quality considerations are integrated throughout the development process~Conduct quality assurance testing: Perform thorough testing of products or systems to ensure compliance with standards and to identify any issues~Continuous process improvement: Analyze testing processes and results to identify areas for improvement and implement changes to enhance quality and efficiency~Develop test plans and strategies: Create comprehensive test plans that outline testing strategies and methodologies to ensure product quality~Document testing processes and results: Maintain detailed documentation of test cases, procedures, and outcomes to ensure traceability and compliance with standards~Ensure regulatory compliance: Ensure that all testing and quality assurance activities comply with relevant regulations and standards~Manage quality assurance projects: Oversee and coordinate quality assurance projects, ensuring that all aspects are executed according to plan~Perform audits and inspections: Conduct regular audits and inspections of systems and processes to ensure adherence to quality standards and identify areas for improvement~Train and support team members: Provide training and support to other team members on quality assurance practices and tools~Utilize quality assurance software tools: Employ various software tools and technologies to facilitate and enhance the quality assurance process',
       -- principalSkills
       'Auditing~Automation testing~Communication~Continuous process improvement~Demonstrating responsibility~Detail-oriented~Documentation maintenance~Integration software~Interpersonal collaboration~Microsoft excel~Problem solving~Regulatory compliance~Reporting~Test planning~Testing',
       -- aiImpact
       'AI impact on the Quality Assurance Analyst role might be moderate. While skills like testing and auditing are less affected, AI can significantly automate documentation and assist with regulatory compliance. Quality Assurance Analysts should focus on upskilling in areas like continuous process improvement, where AI can complement their work. Technical skills like automation testing and integration software are highly susceptible to AI automation.',
       -- keyInsights
       'Impact on hours: Gen AI can automate some tasks like documentation and testing, but core responsibilities like auditing and process improvement may be less affected~New skills: Quality Assurance Analysts should acquire emerging skills such as automated testing, speech recognition algorithms, conversational AI, and AI model development to stay relevant and in demand~Soft skills: Demonstrating responsibility, communication, and problem solving will remain essential for quality assurance analysts to effectively ensure product quality and collaborate with teams',
       -- aiTransformation
       'Moderate'
FROM [dbo].[pathways] p
WHERE p.pathway_title = 'Testing and Quality Assurance';

INSERT INTO [dbo].[JobRole] (
    id, title, pathwayId, jobLevel,
    jobDescription, principalTasks, principalSkills,
    aiImpact, keyInsights, aiTransformation
)
SELECT NEWID(),
       'Software Test and Debug',
       p.pathway_id,
       'Entry level',
       -- jobDescription
       'Integrates and debugs software across the stack including firmware, drivers, and operating systems for a specific product, platform, feature, or technology throughout the product lifecycle. Debugs software products using systematic tests to develop, apply, and maintain quality standards for company products.',
       -- principalTasks
       'Develops a software debug plan and associated methodologies~Analyzes issues, manages sightings from various validation streams, determines root cause, and drives or develops improvements~Drives project stress and stability and supports power, performance, and key KPI task forces~Develops, modifies, and executes software test plans, analyzes, and writes test standards and procedures~Analyzes test results to ensure correct functionality, determines root causes of failures, and recommends corrective action',
       -- principalSkills
       'Automation~Code review~Full stack software frameworks~HW-SW full stack debug~OS architecture internals~Scripting~Secure code development~Software debug~Software test automation~Software test environments~Source control management',
       -- aiImpact
       'New Gen AI techniques enable:~Automated error/bug detection in software code, reducing time engineers spend identifying and classifying bugs~Code suggestions for fixes in identified bugs by generating code suggestions for engineers to review and apply~Skill shift for test/debug engineers to focus more on software design, system architecture, and understanding complex interactions within code that are harder for Gen AI to detect today~Test plan generation~Gen AI is a tool which will enhance the capabilities for Software Test And Debug, enabling engineers to work more efficiently in detecting software bugs proactively.',
       -- keyInsights
       'Automated error/bug detection in software code, reducing time engineers spend identifying and classifying bugs~Code suggestions for fixes in identified bugs by generating code suggestions for engineers to review and apply~Skill shift for test/debug engineers to focus more on software design, system architecture, and understanding complex interactions within code that are harder for Gen AI to detect today~Test plan generation',
       -- aiTransformation
       'High'
FROM [dbo].[pathways] p
WHERE p.pathway_title = 'Testing and Quality Assurance';

INSERT INTO [dbo].[JobRole] (
    id, title, pathwayId, jobLevel,
    jobDescription, principalTasks, principalSkills,
    aiImpact, keyInsights, aiTransformation
)
SELECT NEWID(),
       'Technical Writer',
       p.pathway_id,
       'Entry level',
       -- jobDescription
       'A Technical Writer is responsible for creating and editing technical documentation, such as user manuals, instruction guides, and online help systems. They translate complex technical information into clear and concise language that is easily understandable for the intended audience.',
       -- principalTasks
       'Communication skills: Effectively communicate complex technical information to both technical and non-technical audiences~Documentation creation and maintenance: Develop and maintain clear, concise, and accurate documentation including manuals, guides, and online help content~Interpersonal collaboration: Work closely with technical staff, project managers, and other stakeholders to gather information and clarify technical details~Project management: Manage documentation projects, including planning, scheduling, and tracking progress to ensure timely delivery of materials~Quality assurance: Review and revise technical documents for quality assurance and ensure they meet industry standards and regulatory compliance~Research and analysis: Conduct thorough research to understand complex technical information and translate it into user-friendly text~Software and tools proficiency: Utilize various documentation tools and software like Microsoft Office, SharePoint, and content management systems to create and manage documents~Technical knowledge application: Apply technical knowledge to understand and document complex systems, software, and processes~Technical writing and editing: Write and edit technical materials, ensuring they are clear, comprehensive, and technically accurate~Training material development: Develop training materials and user manuals to assist end-users and internal staff in understanding products and systems',
       -- principalSkills
       'Communication~Demonstrating responsibility~Detail-oriented~Documentation maintenance~Interpersonal collaboration~Prioritization~Project team management~Regulatory compliance~Scientific research~Task coordination',
       -- aiImpact
       'AI impact on the Technical Writer role might be high. Documentation, which is a core skill for Technical Writers, can be significantly automated by AI. Other skills like scientific research, task coordination, and regulatory compliance are moderately affected. Technical Writers should focus on upskilling in areas like project team management, where AI can complement their work. Technical skills like user requirements documentation and conducting research are highly susceptible to AI automation.',
       -- keyInsights
       'Impact on number of hours: Gen AI can significantly automate tasks related to documentation, user requirements documentation, and research~New skills: Technical Writers will need to acquire skills in automated testing, AI model development, AI integration, cloud AI, and prompt engineering to stay competitive~Skills in demand: Soft skills such as demonstrating responsibility, communication, and interpersonal collaboration will remain essential for Technical Writers, as they often work closely with subject matter experts and development teams',
       -- aiTransformation
       'High'
FROM [dbo].[pathways] p
WHERE p.pathway_title = 'Testing and Quality Assurance';


COMMIT TRAN;
