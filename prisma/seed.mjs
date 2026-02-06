import skillsData_v2 from "../data/skills_v2.mjs";
import partnerProvidersAndPrograms from "../data/partnerProvidersAndPrograms.mjs";
import { v4 as uuidv4 } from "uuid";
import { faker } from "@faker-js/faker";
import { users } from "../app/lib/placeholder-data.mjs";
import getPrismaClient from "../app/lib/prismaClient.mjs";
import fs from "fs";
import { fileURLToPath } from "url";
import path from "node:path";
import partnerCompanies from "../data/partnerCompanies.mjs";

faker.seed(123); // set seed so generated data is deterministic
const prisma = getPrismaClient();

// Get the current directory name
const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

/////////////////////////////////////////////////
////// Arrays to simulate realistic data ////////
/////////////////////////////////////////////////

const roles = ["EDUCATOR", "JOBSEEKER", "EMPLOYER", "CASE_MANAGER"];
const edPrograms = [
  "None",
  "High school",
  "College",
  "Training program/bootcamp",
  "Pre-apprenticeship",
  "Other",
];
const degreeTypes = [
  "Certificate",
  "Associate",
  "Bachelor",
  "Master",
  "Doctorate",
];
const subcategoriesData = [
  { skill_category: "Agile Software Development" },
  { skill_category: "Application Programming Interfaces (API)" },
  { skill_category: "Artificial Intelligence and Machine Learning (AI/ML)" },
  { skill_category: "Augmented and Virtual Reality (AR/VR)" },
  { skill_category: "Backup Software" },
  { skill_category: "Basic Technical Knowledge" },
  { skill_category: "Blockchain" },
  { skill_category: "C and C++" },
  { skill_category: "Cloud Computing" },
  { skill_category: "Cloud Solutions" },
  { skill_category: "Collaborative Software" },
  { skill_category: "Computer Hardware" },
  { skill_category: "Computer Science" },
  { skill_category: "Configuration Management" },
  { skill_category: "Content Management Systems" },
  { skill_category: "Cybersecurity" },
  { skill_category: "Data Collection" },
  { skill_category: "Data Management" },
  { skill_category: "Data Storage" },
  { skill_category: "Database Architecture and Administration" },
  { skill_category: "Databases" },
  { skill_category: "Distributed Computing" },
  { skill_category: "Enterprise Application Management" },
  { skill_category: "Enterprise Information Management" },
  { skill_category: "Extensible Languages and XML" },
  { skill_category: "Extraction, Transformation, and Loading (ETL)" },
  { skill_category: "Firmware" },
  { skill_category: "General Networking" },
  { skill_category: "Geospatial Information and Technology" },
  { skill_category: "Identity and Access Management" },
  { skill_category: "Integrated Development Environments (IDEs)" },
  { skill_category: "Internet of Things (IoT)" },
  { skill_category: "iOS Development" },
  { skill_category: "IT Automation" },
  { skill_category: "IT Management" },
  { skill_category: "Java" },
  { skill_category: "JavaScript and jQuery" },
  { skill_category: "Log Management" },
  { skill_category: "Mainframe Technologies" },
  { skill_category: "Malware Protection" },
  { skill_category: "Microsoft Development Tools" },
  { skill_category: "Microsoft Windows" },
  { skill_category: "Middleware" },
  { skill_category: "Mobile Development" },
  { skill_category: "Network Protocols" },
  { skill_category: "Network Security" },
  { skill_category: "Networking Hardware" },
  { skill_category: "Networking Software" },
  { skill_category: "Operating Systems" },
  { skill_category: "Other Programming Languages" },
  { skill_category: "Query Languages" },
  { skill_category: "Scripting" },
  { skill_category: "Scripting Languages" },
  { skill_category: "Search Engines" },
  { skill_category: "Servers" },
  { skill_category: "Software Development" },
  { skill_category: "Software Development Tools" },
  { skill_category: "Software Quality Assurance" },
  { skill_category: "System Design and Implementation" },
  { skill_category: "Systems Administration" },
  { skill_category: "Technical Support and Services" },
  { skill_category: "Telecommunications" },
  { skill_category: "Test Automation" },
  { skill_category: "Version Control" },
  { skill_category: "Video and Web Conferencing" },
  { skill_category: "Virtualization and Virtual Machines" },
  { skill_category: "Web Content" },
  { skill_category: "Web Design and Development" },
  { skill_category: "Web Services" },
  { skill_category: "Wireless Technologies" },
  { skill_category: "Soft Skill" },
  { skill_category: "Unspecified" },
  { skill_category: "Business Intelligence" },
]; // Lightcast IT subcategories data

// // replaced with real data from Dynamics (programs table)
// const techEdMajors = [
//     {name: "None", program_id: uuidv4()},
//     {name: "Computer Science", program_id: uuidv4()},
//     {name: "Information Technology", program_id: uuidv4()},
//     {name: "Software Engineering", program_id: uuidv4()},
//     {name: "Cybersecurity", program_id: uuidv4()},
//     {name: "Data Science", program_id: uuidv4()},
//     {name: "Artificial Intelligence", program_id: uuidv4()},
//     {name: "Network Administration", program_id: uuidv4()},
//     {name: "Cloud Computing", program_id: uuidv4()},
//     {name: "Mobile Application Development", program_id: uuidv4()},
//     {name: "Web Development", program_id: uuidv4()},
//     {name: "Database Management", program_id: uuidv4()},
//     {name: "Game Development", program_id: uuidv4()},
//     {name: "Digital Forensics", program_id: uuidv4()},
//     {name: "IT Project Management", program_id: uuidv4()},
//     {name: "Systems Analysis", program_id: uuidv4()},
//     {name: "Computer Engineering", program_id: uuidv4()},
//     {name: "Robotics", program_id: uuidv4()},
//     {name: "Embedded Systems", program_id: uuidv4()},
//     {name: "Computer Graphics", program_id: uuidv4()},
//     {name: "Information Systems", program_id: uuidv4()},
//     {name: "Business Information Technology", program_id: uuidv4()},
//     {name: "Health Informatics", program_id: uuidv4()},
//     {name: "Human-Computer Interaction", program_id: uuidv4()},
//     {name: "Augmented Reality Development", program_id: uuidv4()},
//     {name: "Virtual Reality Development", program_id: uuidv4()},
//     {name: "Blockchain Technology", program_id: uuidv4()},
//     {name: "Machine Learning", program_id: uuidv4()},
//     {name: "Big Data Analytics", program_id: uuidv4()},
//     {name: "IT Support Specialist", program_id: uuidv4()},
//     {name: "DevOps Engineering", program_id: uuidv4()},
//     {name: "IT Networking", program_id: uuidv4()},
//     {name: "Software Quality Assurance", program_id: uuidv4()},
//     {name: "Ethical Hacking", program_id: uuidv4()},
//     {name: "Programming Languages", program_id: uuidv4()},
//     {name: "Technical Writing", program_id: uuidv4()},
//     {name: "IT Entrepreneurship", program_id: uuidv4()},
//     {name: "IT Consulting", program_id: uuidv4()},
//     {name: "Geographic Information Systems (GIS)", program_id: uuidv4()},
//     {name: "Bioinformatics", program_id: uuidv4()},
//     {name: "Quantum Computing", program_id: uuidv4()},
//     {name: "Computer and Network Security", program_id: uuidv4()},
//     {name: "Multimedia Technology", program_id: uuidv4()},
//     {name: "Internet of Things (IoT)", program_id: uuidv4()},
//     {name: "Artificial Intelligence and Machine Learning", program_id: uuidv4()},
//     {name: "IT Service Management", program_id: uuidv4()},
//     {name: "Information Assurance", program_id: uuidv4()},
//     {name: "Software Architecture", program_id: uuidv4()},
//     {name: "Mobile and Web Design", program_id: uuidv4()},
//     {name: "Technology Management", program_id: uuidv4()},
//     {name: "Computer Systems Technology", program_id: uuidv4()},
//     {name: "Technical Studies in IT", program_id: uuidv4()}
// ];

const highSchools = [
  "Alan T. Sugiyama High School",
  "Ballard High School",
  "Bellevue",
  "Bellevue Digital Discovery",
  "Big Picture School",
  "Bridges Transition",
  "Chief Sealth International High School",
  "Cleveland High School",
  "Franklin High School",
  "Garfield High School",
  "Hazen High School",
  "Ingraham High School",
  "Interagency Detention School",
  "Interagency Open Doors",
  "Interagency Programs",
  "Interlake",
  "International School",
  "Lincoln High School",
  "Lindbergh High School",
  "Middle College High School",
  "Nathan Hale High School",
  "Newport",
  "Nova High School",
  "Private School Servicea",
  "Rainier Beach High School",
  "Renton High School",
  "Roosevelt High School",
  "Sammamish",
  "Seattle World School",
  "The Center School",
  "West Seattle High School",
  "Yakima High School",
];

const colleges = [
  "Bates Technical College",
  "Bellevue College",
  "Bellingham Technical College",
  "Big Bend Community College",
  "Cascadia College",
  "Centralia College",
  "Clark College",
  "Clover Park Technical College",
  "Columbia Basin College, Pasco",
  "Columbia Basin College, Richland",
  "Edmonds College",
  "Everett Community College",
  "Green River College, Auburn",
  "Green River College, Enumclaw",
  "Green River College, Kent",
  "Hack Reactor",
  "Highline College, Des Moines",
  "Highline College, Federal Way",
  "Lake Washington Institute of Technology, Redmond",
  "Lake Washington Institute of Technology, Kirkland",
  "Lower Columbia College",
  "North Seattle College",
  "Olympic College, Bremerton",
  "Olympic College, Poulsbo",
  "Olympic College, Shelton",
  "Peninsula College, Port Angeles",
  "Peninsula College, Port Townsend",
  "Peninsula College, Forks",
  "Pierce College",
  "Renton Technical College",
  "Seattle Central College",
  "San Jose State University",
  "Saint Martins University",
  "Seattle Pacific University",
  "Shoreline Community College",
  "Skagit Valley College",
  "South Puget Sound Community College, Olympia",
  "South Puget Sound Community College, Lacey",
  "South Seattle College",
  "Spokane Community College",
  "Spokane Falls Community College",
  "Tacoma Community College",
  "Tufts University",
  "Walla Walla Community College",
  "Washington State University",
  "Wenatchee Valley College, Wenatchee",
  "Wenatchee Valley College, Omak",
  "Whatcom College",
  "Whatcom Community College",
  "Yakima Valley College, Yakima",
  "Yakima Valley College, Grandview",
  "University of Washington, Tacoma",
  "University of Washington",
  "University of Washington, Bothell",
  "Vancouver Island University",
  "Seattle University",
  "Other",
];

const highestDegreeType = [
  "Primary Education",
  "High School",
  "Associates",
  "Bachelors",
  "Masters",
  "Doctorate",
  "GED",
  "Vocational Qualification / Certification",
  "No Formal Education",
];

const programEnrollmentStatus = [
  "Admitted, not yet enrolled",
  "Currently active in program",
  "Graduated / Completed",
  "Withdrawn / terminated",
];

const itOccupationTechnologyAreas = [
  { id: "f23b7623-60ba-4a5b-a0a4-6cb588dbf6bd", name: "Other" },
  { id: "f18b7623-60ba-4a5b-a0a4-6cb588bdf6db", name: "Cybersecurity" },
  { id: "7e3b01fc-7c6a-4baf-b755-e47b07ad9191", name: "Cloud Computing" },
  { id: "48d5b1e9-2f36-4c2a-89bb-3b6b063fdd77", name: "Data Science" },
  {
    id: "92ad3c59-62e6-4e84-b908-f3f4c8b089be",
    name: "Artificial Intelligence",
  },
  {
    id: "ad4f37e4-6e7f-4110-aba3-6dd591e4d733",
    name: "Network Administration",
  },
  { id: "b77c5d72-2d8a-47e5-a13d-5d7a7893be09", name: "Software Development" },
  { id: "a7c1a1a1-e07e-43b8-a8eb-59b80f5c7a99", name: "Database Management" },
  { id: "4b303f74-d3f1-4c25-9e32-3cc585b47814", name: "DevOps" },
  { id: "d2560874-32d3-4bc4-a5da-7b2b0dba62a0", name: "Web Development" },
  {
    id: "1e7ec76f-4b90-47d7-b9b1-d9ac38fd8d63",
    name: "Mobile App Development",
  },
  { id: "7634a5fb-2398-4657-aab5-203c1fc84168", name: "IT Support" },
  { id: "907a2f50-becb-472f-b045-03f22cc92611", name: "System Analysis" },
  { id: "7f61d839-d63a-44d7-8ef9-45726f401f16", name: "IT Project Management" },
  { id: "c4d5c8a8-79d2-4429-960b-4991f1175462", name: "Machine Learning" },
  { id: "dd832f38-9020-42f7-b59c-fb39f9a4b28f", name: "Big Data Analytics" },
  { id: "bb832f38-8172-5681-c43b-ab29f9a4b29e", name: "N/A Not an IT role" },
];

const techAreasWithCategories = [
  {
    category: "Cybersecurity",
    subcategories: [
      { name: "Identity and Access Management" },
      { name: "Network Security" },
      { name: "Malware Protection" },
      { name: "Log Management" },
      { name: "Penetration Testing", newEntry: true },
      { name: "Security Auditing", newEntry: true },
      { name: "Incident Response", newEntry: true },
      { name: "Digital Forensics", newEntry: true },
    ],
  },
  {
    category: "Cloud Computing",
    subcategories: [
      { name: "Cloud Solutions" },
      { name: "Distributed Computing" },
      { name: "Data Storage" },
      { name: "Virtualization and Virtual Machines" },
      { name: "Serverless Computing", newEntry: true },
      { name: "Cloud Security", newEntry: true },
      { name: "Cloud Migration", newEntry: true },
      { name: "Platform as a Service (PaaS)", newEntry: true },
      { name: "Infrastructure as a Service (IaaS)", newEntry: true },
    ],
  },
  {
    category: "Data Science",
    subcategories: [
      { name: "Data Collection" },
      { name: "Data Management" },
      { name: "Data Storage" },
      { name: "Big Data Analytics" },
      { name: "ETL (Extraction, Transformation, and Loading)" },
      { name: "Data Mining", newEntry: true },
      { name: "Statistical Analysis", newEntry: true },
      { name: "Data Visualization", newEntry: true },
      { name: "Predictive Modeling", newEntry: true },
    ],
  },
  {
    category: "Artificial Intelligence",
    subcategories: [
      { name: "Artificial Intelligence and Machine Learning (AI/ML)" },
      { name: "Natural Language Processing (NLP)", newEntry: true },
      { name: "Deep Learning", newEntry: true },
      { name: "Computer Vision", newEntry: true },
      { name: "Robotics", newEntry: true },
      { name: "AI Ethics", newEntry: true },
      { name: "Reinforcement Learning", newEntry: true },
      { name: "Neural Networks", newEntry: true },
    ],
  },
  {
    category: "Network Administration",
    subcategories: [
      { name: "General Networking" },
      { name: "Networking Hardware" },
      { name: "Networking Software" },
      { name: "Network Protocols" },
      { name: "Telecommunications" },
      { name: "Wireless Networks", newEntry: true },
      { name: "Network Monitoring", newEntry: true },
      { name: "Software-Defined Networking (SDN)", newEntry: true },
      { name: "Voice over IP (VoIP)", newEntry: true },
    ],
  },
  {
    category: "Software Development",
    subcategories: [
      { name: "Agile Software Development" },
      { name: "Application Programming Interfaces (API)" },
      { name: "C and C++" },
      { name: "Java" },
      { name: "JavaScript and jQuery" },
      { name: "Scripting Languages" },
      { name: "Other Programming Languages" },
      { name: "Software Development Tools" },
      { name: "Middleware" },
      { name: "Operating Systems" },
      { name: "Integrated Development Environments (IDEs)" },
      { name: "Version Control" },
      { name: "Unit Testing", newEntry: true },
      { name: "Software Architecture", newEntry: true },
      { name: "Microservices", newEntry: true },
      { name: "Full Stack Development", newEntry: true },
      { name: "Mobile Development" },
      { name: "DevOps" },
    ],
  },
  {
    category: "Database Management",
    subcategories: [
      { name: "Database Architecture and Administration" },
      { name: "Databases" },
      { name: "Query Languages" },
      { name: "Data Warehousing", newEntry: true },
      { name: "Relational Databases (SQL)", newEntry: true },
      { name: "NoSQL Databases", newEntry: true },
      { name: "Data Modeling", newEntry: true },
      { name: "Database Security", newEntry: true },
      { name: "Database Performance Tuning", newEntry: true },
    ],
  },
  {
    category: "DevOps",
    subcategories: [
      { name: "Configuration Management" },
      { name: "IT Automation" },
      { name: "Test Automation" },
      { name: "Backup Software" },
      { name: "Version Control" },
      {
        name: "Continuous Integration/Continuous Delivery (CI/CD)",
        newEntry: true,
      },
      { name: "Containerization (Docker/Kubernetes)", newEntry: true },
      { name: "Infrastructure as Code (IaC)", newEntry: true },
      { name: "Monitoring and Logging", newEntry: true },
    ],
  },
  {
    category: "Web Development",
    subcategories: [
      { name: "Web Design and Development" },
      { name: "Web Services" },
      { name: "Web Content" },
      { name: "Search Engines" },
      { name: "Content Management Systems" },
      { name: "Frontend Development", newEntry: true },
      { name: "Backend Development", newEntry: true },
      { name: "Web Frameworks (React, Angular, Vue)", newEntry: true },
      { name: "Responsive Design", newEntry: true },
      { name: "Progressive Web Apps (PWA)", newEntry: true },
    ],
  },
  {
    category: "Mobile App Development",
    subcategories: [
      { name: "Mobile Development" },
      { name: "iOS Development" },
      { name: "Android Development", newEntry: true },
      { name: "Cross-Platform Mobile Development", newEntry: true },
      { name: "Mobile User Experience (UX)", newEntry: true },
      { name: "Mobile Security", newEntry: true },
      { name: "App Store Optimization", newEntry: true },
    ],
  },
  {
    category: "IT Support",
    subcategories: [
      { name: "Technical Support and Services" },
      { name: "Computer Hardware" },
      { name: "Basic Technical Knowledge" },
      { name: "Help Desk Support", newEntry: true },
      { name: "IT Troubleshooting", newEntry: true },
      { name: "IT Service Management (ITSM)", newEntry: true },
      { name: "Remote Support", newEntry: true },
      { name: "End-User Training", newEntry: true },
      { name: "Ticketing Systems", newEntry: true },
    ],
  },
  {
    category: "System Analysis",
    subcategories: [
      { name: "System Design and Implementation" },
      { name: "Systems Administration" },
      { name: "IT Management" },
      { name: "Enterprise Application Management" },
      { name: "Enterprise Information Management" },
      { name: "Business Process Modeling", newEntry: true },
      { name: "Systems Integration", newEntry: true },
      { name: "Requirements Analysis", newEntry: true },
      { name: "Systems Testing", newEntry: true },
    ],
  },
  {
    category: "IT Project Management",
    subcategories: [
      { name: "IT Management" },
      { name: "Collaborative Software" },
      { name: "Agile Project Management", newEntry: true },
      { name: "Waterfall Project Management", newEntry: true },
      { name: "Scrum", newEntry: true },
      { name: "Kanban", newEntry: true },
      { name: "Risk Management", newEntry: true },
      { name: "Stakeholder Management", newEntry: true },
      { name: "Budgeting and Scheduling", newEntry: true },
    ],
  },
  {
    category: "Machine Learning",
    subcategories: [
      { name: "Artificial Intelligence and Machine Learning (AI/ML)" },
      { name: "Deep Learning", newEntry: true },
      { name: "Data Collection" },
      { name: "Supervised Learning", newEntry: true },
      { name: "Unsupervised Learning", newEntry: true },
      { name: "Reinforcement Learning", newEntry: true },
      { name: "Neural Networks", newEntry: true },
      { name: "Feature Engineering", newEntry: true },
      { name: "Model Deployment", newEntry: true },
    ],
  },
  {
    category: "Big Data Analytics",
    subcategories: [
      { name: "Data Management" },
      { name: "Big Data Analytics" },
      { name: "Data Storage" },
      { name: "Hadoop", newEntry: true },
      { name: "Spark", newEntry: true },
      { name: "NoSQL", newEntry: true },
      { name: "Data Lakes", newEntry: true },
      { name: "Data Warehousing", newEntry: true },
      { name: "Real-Time Analytics", newEntry: true },
    ],
  },
  {
    category: "Blockchain",
    subcategories: [
      { name: "Blockchain" },
      { name: "Distributed Ledger Technology (DLT)", newEntry: true },
      { name: "Smart Contracts", newEntry: true },
      { name: "Cryptography", newEntry: true },
      { name: "Blockchain Development", newEntry: true },
      { name: "Decentralized Applications (DApps)", newEntry: true },
      { name: "Blockchain Security", newEntry: true },
      { name: "Consensus Mechanisms", newEntry: true },
      { name: "Tokenomics", newEntry: true },
    ],
  },
  {
    category: "Other",
    subcategories: [
      { name: "Blockchain" },
      { name: "Geospatial Information and Technology" },
      { name: "Firmware" },
      { name: "Virtualization and Virtual Machines" },
      { name: "Video and Web Conferencing" },
      { name: "Wireless Technologies" },
      { name: "Backup Software" },
      { name: "Mainframe Technologies" },
      { name: "Search Engines" },
      { name: "Telecommunications" },
    ],
  },
];

const predefinedResponsibilities = [
  "Develop and maintain software applications.",
  "Collaborate with cross-functional teams.",
  "Participate in code reviews.",
  "Write and maintain technical documentation.",
  "Troubleshoot and debug issues.",
  "Implement new features based on user feedback.",
  "Ensure code quality and performance.",
  "Manage project timelines and deliverables.",
  "Conduct testing and quality assurance.",
  "Provide technical support to team members.",
];

const itProjectTitles = [
  "Website Redesign",
  "Mobile App Development",
  "Cloud Migration",
  "Cybersecurity Implementation",
  "Database Optimization",
  "AI/ML Model Development",
  "Network Infrastructure Upgrade",
  "E-commerce Platform Development",
  "DevOps Pipeline Automation",
  "Enterprise Software Integration",
  "Customer Relationship Management (CRM) System",
  "Data Analytics Platform",
  "Content Management System (CMS)",
  "API Development and Integration",
  "IoT Solution Deployment",
  "Blockchain Implementation",
  "Virtualization Project",
  "Backup and Disaster Recovery Plan",
  "IT Security Audit",
  "User Authentication and Authorization System",
  "Big Data Processing",
  "Microservices Architecture Implementation",
  "Automated Testing Framework",
  "Legacy System Modernization",
  "Unified Communications Solution",
  "Artificial Intelligence Chatbot",
  "Business Intelligence Dashboard",
  "IT Service Management (ITSM) Tool",
  "Robotic Process Automation (RPA)",
  "Cloud-Based Collaboration Suite",
  "Network Security Enhancement",
  "Supply Chain Management System",
  "Predictive Analytics Solution",
  "Virtual Reality (VR) Application",
  "Augmented Reality (AR) Application",
  "Video Conferencing System Deployment",
  "Remote Work Infrastructure",
  "Server Consolidation",
  "Software-as-a-Service (SaaS) Development",
  "Customer Data Platform (CDP)",
  "IT Asset Management System",
  "Project Management Tool",
  "Electronic Health Record (EHR) System",
  "Healthcare Information System",
  "Fleet Management System",
  "IT Compliance Management",
  "Performance Monitoring Solution",
  "Help Desk System Implementation",
  "Scalable Storage Solution",
];

const developmentTeamRoles = [
  "Lead Developer",
  "Project Manager",
  "Backend Developer",
  "Frontend Developer",
  "Full Stack Developer",
  "Quality Assurance Engineer",
  "UI/UX Designer",
  "Product Owner",
  "Scrum Master",
  "DevOps Engineer",
  "Database Administrator",
  "Business Analyst",
  "Technical Writer",
  "System Architect",
  "Mobile Developer",
  "Security Specialist",
  "Release Manager",
  "Support Engineer",
  "Data Scientist",
  "Machine Learning Engineer",
];

const waStateCountiesWithZipCodes = [
  {
    county: "Adams",
    zipCodes: ["99341", "99344", "99326", "99328", "99330"],
  },
  {
    county: "Asotin",
    zipCodes: ["99401", "99402", "99403"],
  },
  {
    county: "Benton",
    zipCodes: [
      "99320",
      "99336",
      "99337",
      "99338",
      "99350",
      "99352",
      "99353",
      "99354",
    ],
  },
  {
    county: "Chelan",
    zipCodes: [
      "98801",
      "98811",
      "98815",
      "98816",
      "98817",
      "98821",
      "98822",
      "98826",
      "98828",
      "98831",
      "98847",
    ],
  },
  {
    county: "Clallam",
    zipCodes: [
      "98305",
      "98324",
      "98326",
      "98331",
      "98350",
      "98357",
      "98362",
      "98363",
      "98381",
      "98382",
    ],
  },
  {
    county: "Clark",
    zipCodes: [
      "98601",
      "98604",
      "98606",
      "98607",
      "98629",
      "98642",
      "98660",
      "98661",
      "98662",
      "98663",
      "98664",
      "98665",
      "98666",
      "98668",
      "98671",
      "98674",
      "98675",
      "98682",
      "98683",
      "98684",
      "98685",
      "98686",
      "98687",
    ],
  },
  {
    county: "Columbia",
    zipCodes: ["99328", "99361"],
  },
  {
    county: "Cowlitz",
    zipCodes: ["98603", "98611", "98625", "98626", "98632", "98645", "98674"],
  },
  {
    county: "Douglas",
    zipCodes: [
      "98802",
      "98807",
      "98816",
      "98821",
      "98822",
      "98824",
      "98829",
      "98830",
      "98843",
      "98845",
      "98858",
    ],
  },
  {
    county: "Ferry",
    zipCodes: ["99121", "99138", "99140", "99150", "99166"],
  },
  {
    county: "Franklin",
    zipCodes: ["99301", "99330", "99335", "99343"],
  },
  {
    county: "Garfield",
    zipCodes: ["99347"],
  },
  {
    county: "Grant",
    zipCodes: [
      "98823",
      "98824",
      "98832",
      "98837",
      "98848",
      "98851",
      "98853",
      "98857",
      "98860",
      "99321",
      "99344",
      "99349",
      "99357",
    ],
  },
  {
    county: "Grays Harbor",
    zipCodes: [
      "98520",
      "98526",
      "98535",
      "98536",
      "98537",
      "98541",
      "98547",
      "98550",
      "98552",
      "98557",
      "98559",
      "98562",
      "98563",
      "98566",
      "98568",
      "98569",
      "98575",
      "98583",
      "98587",
    ],
  },
  {
    county: "Island",
    zipCodes: ["98239", "98249", "98253", "98260", "98277", "98278", "98282"],
  },
  {
    county: "Jefferson",
    zipCodes: ["98320", "98325", "98339", "98358", "98365", "98368", "98376"],
  },
  {
    county: "King",
    zipCodes: [
      "98001",
      "98002",
      "98003",
      "98004",
      "98005",
      "98006",
      "98007",
      "98008",
      "98009",
      "98010",
      "98011",
      "98013",
      "98014",
      "98015",
      "98019",
      "98022",
      "98023",
      "98024",
      "98025",
      "98027",
      "98028",
      "98029",
      "98030",
      "98031",
      "98032",
      "98033",
      "98034",
      "98035",
      "98038",
      "98039",
      "98040",
      "98041",
      "98042",
      "98045",
      "98047",
      "98050",
      "98051",
      "98052",
      "98053",
      "98055",
      "98056",
      "98057",
      "98058",
      "98059",
      "98062",
      "98063",
      "98064",
      "98065",
      "98070",
      "98071",
      "98072",
      "98073",
      "98074",
      "98075",
      "98077",
      "98082",
      "98083",
      "98087",
      "98089",
      "98092",
      "98093",
      "98101",
      "98102",
      "98103",
      "98104",
      "98105",
      "98106",
      "98107",
      "98108",
      "98109",
      "98110",
      "98111",
      "98112",
      "98113",
      "98114",
      "98115",
      "98116",
      "98117",
      "98118",
      "98119",
      "98121",
      "98122",
      "98124",
      "98125",
      "98126",
      "98127",
      "98129",
      "98131",
      "98132",
      "98133",
      "98134",
      "98136",
      "98138",
      "98139",
      "98141",
      "98144",
      "98145",
      "98146",
      "98148",
      "98151",
      "98154",
      "98155",
      "98158",
      "98160",
      "98161",
      "98164",
      "98166",
      "98168",
      "98170",
      "98174",
      "98175",
      "98177",
      "98178",
      "98181",
      "98185",
      "98188",
      "98190",
      "98191",
      "98194",
      "98195",
      "98198",
      "98199",
    ],
  },
  {
    county: "Kitsap",
    zipCodes: [
      "98310",
      "98311",
      "98312",
      "98314",
      "98315",
      "98322",
      "98337",
      "98340",
      "98342",
      "98345",
      "98346",
      "98353",
      "98359",
      "98364",
      "98366",
      "98367",
      "98370",
      "98378",
      "98380",
      "98383",
      "98384",
      "98386",
      "98393",
    ],
  },
  {
    county: "Kittitas",
    zipCodes: [
      "98922",
      "98925",
      "98926",
      "98934",
      "98940",
      "98941",
      "98943",
      "98946",
      "98950",
    ],
  },
  {
    county: "Klickitat",
    zipCodes: [
      "98602",
      "98605",
      "98613",
      "98617",
      "98619",
      "98620",
      "98623",
      "98628",
      "98635",
      "98650",
      "98670",
      "98672",
      "98673",
    ],
  },
  {
    county: "Lewis",
    zipCodes: [
      "98336",
      "98355",
      "98356",
      "98377",
      "98522",
      "98531",
      "98532",
      "98533",
      "98538",
      "98539",
      "98542",
      "98544",
      "98564",
      "98565",
      "98570",
      "98572",
      "98582",
      "98585",
      "98591",
      "98593",
      "98596",
      "98597",
    ],
  },
  {
    county: "Lincoln",
    zipCodes: [
      "99008",
      "99009",
      "99029",
      "99122",
      "99134",
      "99144",
      "99159",
      "99185",
    ],
  },
  {
    county: "Mason",
    zipCodes: [
      "98524",
      "98528",
      "98546",
      "98548",
      "98555",
      "98560",
      "98584",
      "98588",
      "98592",
    ],
  },
  {
    county: "Okanogan",
    zipCodes: [
      "98812",
      "98814",
      "98819",
      "98827",
      "98829",
      "98833",
      "98834",
      "98840",
      "98841",
      "98844",
      "98846",
      "98849",
      "98855",
      "98856",
      "98859",
      "99155",
    ],
  },
  {
    county: "Pacific",
    zipCodes: [
      "98527",
      "98535",
      "98547",
      "98554",
      "98586",
      "98614",
      "98624",
      "98631",
      "98637",
      "98640",
      "98641",
      "98644",
    ],
  },
  {
    county: "Pend Oreille",
    zipCodes: ["99119", "99139", "99152", "99156", "99180"],
  },
  {
    county: "Pierce",
    zipCodes: [
      "98303",
      "98304",
      "98321",
      "98323",
      "98327",
      "98328",
      "98329",
      "98330",
      "98332",
      "98333",
      "98335",
      "98338",
      "98348",
      "98349",
      "98351",
      "98352",
      "98354",
      "98360",
      "98371",
      "98372",
      "98373",
      "98374",
      "98375",
      "98385",
      "98387",
      "98388",
      "98390",
      "98391",
      "98394",
      "98395",
      "98396",
      "98397",
      "98398",
      "98401",
      "98402",
      "98403",
      "98404",
      "98405",
      "98406",
      "98407",
      "98408",
      "98409",
      "98411",
      "98412",
      "98413",
      "98415",
      "98416",
      "98417",
      "98418",
      "98419",
      "98421",
      "98422",
      "98424",
      "98430",
      "98431",
      "98433",
      "98438",
      "98439",
      "98442",
      "98443",
      "98444",
      "98445",
      "98446",
      "98447",
      "98448",
      "98450",
      "98455",
      "98460",
      "98464",
      "98465",
      "98466",
      "98467",
      "98471",
      "98481",
      "98490",
      "98493",
      "98496",
      "98497",
      "98498",
      "98499",
    ],
  },
  {
    county: "San Juan",
    zipCodes: [
      "98222",
      "98243",
      "98245",
      "98250",
      "98261",
      "98279",
      "98280",
      "98286",
      "98297",
    ],
  },
  {
    county: "Skagit",
    zipCodes: [
      "98221",
      "98232",
      "98233",
      "98235",
      "98237",
      "98238",
      "98240",
      "98255",
      "98257",
      "98263",
      "98267",
      "98273",
      "98274",
      "98283",
      "98284",
    ],
  },
  {
    county: "Skamania",
    zipCodes: [
      "98603",
      "98605",
      "98610",
      "98623",
      "98639",
      "98648",
      "98651",
      "98671",
    ],
  },
  {
    county: "Snohomish",
    zipCodes: [
      "98012",
      "98020",
      "98021",
      "98026",
      "98036",
      "98037",
      "98043",
      "98046",
      "98072",
      "98082",
      "98087",
      "98201",
      "98203",
      "98204",
      "98205",
      "98206",
      "98207",
      "98208",
      "98213",
      "98223",
      "98224",
      "98241",
      "98252",
      "98256",
      "98258",
      "98259",
      "98270",
      "98271",
      "98272",
      "98275",
      "98287",
      "98290",
      "98291",
      "98292",
      "98293",
      "98294",
      "98296",
      "98298",
    ],
  },
  {
    county: "Spokane",
    zipCodes: [
      "99001",
      "99003",
      "99004",
      "99005",
      "99006",
      "99008",
      "99009",
      "99011",
      "99012",
      "99014",
      "99016",
      "99018",
      "99019",
      "99020",
      "99021",
      "99022",
      "99023",
      "99025",
      "99026",
      "99027",
      "99029",
      "99030",
      "99031",
      "99032",
      "99036",
      "99037",
      "99039",
      "99040",
      "99110",
      "99122",
      "99134",
      "99156",
      "99201",
      "99202",
      "99203",
      "99204",
      "99205",
      "99206",
      "99207",
      "99208",
      "99209",
      "99210",
      "99211",
      "99212",
      "99213",
      "99214",
      "99215",
      "99216",
      "99217",
      "99218",
      "99219",
      "99220",
      "99223",
      "99224",
      "99228",
      "99251",
      "99252",
      "99256",
      "99258",
      "99260",
      "99299",
    ],
  },
  {
    county: "Stevens",
    zipCodes: [
      "99006",
      "99009",
      "99013",
      "99017",
      "99026",
      "99101",
      "99110",
      "99114",
      "99126",
      "99129",
      "99131",
      "99137",
      "99141",
      "99148",
      "99151",
      "99157",
      "99160",
      "99167",
      "99181",
    ],
  },
  {
    county: "Thurston",
    zipCodes: [
      "98501",
      "98502",
      "98503",
      "98504",
      "98505",
      "98506",
      "98507",
      "98508",
      "98509",
      "98511",
      "98512",
      "98513",
      "98516",
      "98530",
      "98531",
      "98540",
      "98556",
      "98576",
      "98597",
    ],
  },
  {
    county: "Wahkiakum",
    zipCodes: ["98612", "98621", "98647"],
  },
  {
    county: "Walla Walla",
    zipCodes: ["99324", "99329", "99348", "99360", "99362"],
  },
  {
    county: "Whatcom",
    zipCodes: [
      "98225",
      "98226",
      "98227",
      "98228",
      "98229",
      "98230",
      "98231",
      "98240",
      "98244",
      "98247",
      "98248",
      "98262",
      "98264",
      "98266",
      "98276",
      "98281",
      "98295",
    ],
  },
  {
    county: "Whitman",
    zipCodes: [
      "99033",
      "99102",
      "99104",
      "99111",
      "99113",
      "99125",
      "99128",
      "99130",
      "99133",
      "99136",
      "99143",
      "99149",
      "99158",
      "99161",
      "99163",
      "99164",
      "99170",
      "99171",
      "99174",
      "99176",
      "99179",
      "99185",
    ],
  },
  {
    county: "Yakima",
    zipCodes: [
      "98901",
      "98902",
      "98903",
      "98904",
      "98907",
      "98908",
      "98909",
      "98920",
      "98921",
      "98923",
      "98930",
      "98932",
      "98933",
      "98935",
      "98936",
      "98937",
      "98938",
      "98939",
      "98942",
      "98944",
      "98947",
      "98948",
      "98951",
      "98952",
      "98953",
    ],
  },
];

const itCertifications = [
  {
    name: "AWS Certified Solutions Architect",
    issuing_org: "Amazon Web Services",
    credential_url:
      "https://aws.amazon.com/certification/certified-solutions-architect-associate/",
    credential_id: "AWS-CSA-001",
    logo_url:
      "https://d1.awsstatic.com/certification/badges/AWS-Certified-Solutions-Architect-Associate_badge_150x150.e359ae4a6d4d82c3e31d4f9104c8d389b56a2423.png",
  },
  {
    name: "Certified Information Systems Security Professional (CISSP)",
    issuing_org: "ISC2",
    credential_url: "https://www.isc2.org/Certifications/CISSP",
    credential_id: "CISSP-002",
    logo_url:
      "https://www.isc2.org/-/media/ISC2/Certifications/CISSP/CISSP-Logo.ashx",
  },
  {
    name: "Certified Ethical Hacker (CEH)",
    issuing_org: "EC-Council",
    credential_url:
      "https://www.eccouncil.org/programs/certified-ethical-hacker-ceh/",
    credential_id: "CEH-003",
    logo_url:
      "https://www.eccouncil.org/wp-content/uploads/2021/08/CEH-V11.png",
  },
  {
    name: "Cisco Certified Network Associate (CCNA)",
    issuing_org: "Cisco",
    credential_url:
      "https://www.cisco.com/c/en/us/training-events/training-certifications/certifications/associate/ccna.html",
    credential_id: "CCNA-004",
    logo_url:
      "https://www.cisco.com/c/dam/en_us/training-events/certifications/professional/ccna-500.png",
  },
  {
    name: "CompTIA A+",
    issuing_org: "CompTIA",
    credential_url: "https://www.comptia.org/certifications/a",
    credential_id: "CompTIA-A-005",
    logo_url:
      "https://www.comptia.org/Content/Images/CompTIA-Badges/Badge-CompTIA-A.png",
  },
  {
    name: "CompTIA Network+",
    issuing_org: "CompTIA",
    credential_url: "https://www.comptia.org/certifications/network",
    credential_id: "CompTIA-N-006",
    logo_url:
      "https://www.comptia.org/Content/Images/CompTIA-Badges/Badge-CompTIA-Network.png",
  },
  {
    name: "CompTIA Security+",
    issuing_org: "CompTIA",
    credential_url: "https://www.comptia.org/certifications/security",
    credential_id: "CompTIA-S-007",
    logo_url:
      "https://www.comptia.org/Content/Images/CompTIA-Badges/Badge-CompTIA-Security.png",
  },
  {
    name: "Google Cloud Professional Data Engineer",
    issuing_org: "Google",
    credential_url: "https://cloud.google.com/certification/data-engineer",
    credential_id: "GCP-DE-008",
    logo_url:
      "https://cloud.google.com/images/certifications/data-engineer-cpd.png",
  },
  {
    name: "Google Cloud Professional Cloud Architect",
    issuing_org: "Google",
    credential_url: "https://cloud.google.com/certification/cloud-architect",
    credential_id: "GCP-CA-009",
    logo_url:
      "https://cloud.google.com/images/certifications/cloud-architect-cpd.png",
  },
  {
    name: "Microsoft Certified: Azure Fundamentals",
    issuing_org: "Microsoft",
    credential_url:
      "https://docs.microsoft.com/en-us/learn/certifications/azure-fundamentals/",
    credential_id: "MS-AF-010",
    logo_url:
      "https://query.prod.cms.rt.microsoft.com/cms/api/am/imageFileData/RWRuDe",
  },
  {
    name: "Microsoft Certified: Azure Solutions Architect Expert",
    issuing_org: "Microsoft",
    credential_url:
      "https://docs.microsoft.com/en-us/learn/certifications/azure-solutions-architect/",
    credential_id: "MS-ASAE-011",
    logo_url:
      "https://query.prod.cms.rt.microsoft.com/cms/api/am/imageFileData/RE2PjDI",
  },
  {
    name: "Microsoft Certified: Azure Administrator Associate",
    issuing_org: "Microsoft",
    credential_url:
      "https://docs.microsoft.com/en-us/learn/certifications/azure-administrator/",
    credential_id: "MS-AAA-012",
    logo_url:
      "https://query.prod.cms.rt.microsoft.com/cms/api/am/imageFileData/RWBLOt",
  },
  {
    name: "Certified Information Security Manager (CISM)",
    issuing_org: "ISACA",
    credential_url: "https://www.isaca.org/credentialing/cism",
    credential_id: "CISM-013",
    logo_url:
      "https://www.isaca.org/-/media/images/isacadp/logo/logo-cism-250.png",
  },
  {
    name: "Certified Information Systems Auditor (CISA)",
    issuing_org: "ISACA",
    credential_url: "https://www.isaca.org/credentialing/cisa",
    credential_id: "CISA-014",
    logo_url:
      "https://www.isaca.org/-/media/images/isacadp/logo/logo-cisa-250.png",
  },
  {
    name: "Project Management Professional (PMP)",
    issuing_org: "PMI",
    credential_url: "https://www.pmi.org/certifications/project-management-pmp",
    credential_id: "PMP-015",
    logo_url:
      "https://www.pmi.org/-/media/pmi/images/certification-logos/logo-pmp.png",
  },
  {
    name: "Certified ScrumMaster (CSM)",
    issuing_org: "Scrum Alliance",
    credential_url:
      "https://www.scrumalliance.org/get-certified/scrum-master-track/certified-scrummaster",
    credential_id: "CSM-016",
    logo_url: "https://www.scrumalliance.org/Content/Images/Home/CSM-Logo.png",
  },
  {
    name: "VMware Certified Professional (VCP)",
    issuing_org: "VMware",
    credential_url:
      "https://www.vmware.com/education-services/certification/vcp.html",
    credential_id: "VCP-017",
    logo_url:
      "https://mylearn.vmware.com/global/images/certification/VCP-DCV.png",
  },
  {
    name: "Oracle Certified Java Programmer",
    issuing_org: "Oracle",
    credential_url:
      "https://education.oracle.com/java-se-11-programmer-i/pexam_1Z0-815",
    credential_id: "OCJP-018",
    logo_url:
      "https://education.oracle.com/education/javacert/ocp/ocp-certification-seal.png",
  },
  {
    name: "Red Hat Certified System Administrator (RHCSA)",
    issuing_org: "Red Hat",
    credential_url: "https://www.redhat.com/en/services/certification/rhcsa",
    credential_id: "RHCSA-019",
    logo_url:
      "https://www.redhat.com/cms/managed-files/styles/xlarge/s3/rhcert.png",
  },
  {
    name: "ITIL Foundation Certification",
    issuing_org: "AXELOS",
    credential_url:
      "https://www.axelos.com/certifications/itil-certifications/itil-foundation",
    credential_id: "ITIL-020",
    logo_url:
      "https://www.axelos.com/brand-assets/images/logos/itil-master-axelos.png",
  },
];

const socialMediaPlatforms = [
  { platform: "Facebook", social_logo_url: faker.internet.url() },
  { platform: "X (Twitter)", social_logo_url: faker.internet.url() },
  { platform: "Instagram", social_logo_url: faker.internet.url() },
  { platform: "LinkedIn", social_logo_url: faker.internet.url() },
  { platform: "Snapchat", social_logo_url: faker.internet.url() },
  { platform: "Pinterest", social_logo_url: faker.internet.url() },
  { platform: "TikTok", social_logo_url: faker.internet.url() },
  { platform: "Reddit", social_logo_url: faker.internet.url() },
  { platform: "YouTube", social_logo_url: faker.internet.url() },
  { platform: "WhatsApp", social_logo_url: faker.internet.url() },
  { platform: "WeChat", social_logo_url: faker.internet.url() },
  { platform: "Telegram", social_logo_url: faker.internet.url() },
  { platform: "Tumblr", social_logo_url: faker.internet.url() },
  { platform: "Quora", social_logo_url: faker.internet.url() },
  { platform: "Viber", social_logo_url: faker.internet.url() },
  { platform: "Discord", social_logo_url: faker.internet.url() },
  { platform: "Twitch", social_logo_url: faker.internet.url() },
  { platform: "Flickr", social_logo_url: faker.internet.url() },
  { platform: "Medium", social_logo_url: faker.internet.url() },
  { platform: "Clubhouse", social_logo_url: faker.internet.url() },
];

const industrySectors = [
  "Agriculture",
  "Automotive",
  "Banking and Financial Services",
  "Biotechnology",
  "Construction",
  "Consumer Goods",
  "Education",
  "Energy",
  "Government",
  "Healthcare",
  "Information Technology",
  "Insurance",
  "Manufacturing",
  "Media and Entertainment",
  "Nonprofit",
  "Pharmaceuticals",
  "Real Estate",
  "Retail",
  "Telecommunications",
  "Transportation and Logistics",
  "Travel and Hospitality",
  "Utilities",
  "Other",
];

const programs = [
  "AOS - Computer Applications Software Support",
  "Application Development",
  "Associate in Computer Science DTA/MRP",
  "Bachelor of Applied Science - Cybersecurity & Forensics",
  "Bachelor of Applied Science - Cybersecurity",
  "Bachelor of Applied Science - Data Analytics",
  "Bachelor of Applied Science - Data Management and Analysis",
  "Bachelor of Applied Science - Information Technology: Application Development",
  "Bachelor of Applied Science - Information Technology: Computing and Software Development",
  "Bachelor of Applied Science - Information Technology: Networking-Systems",
  "Bachelor of Applied Science - IT Networking - Cybersecurity",
  "Bachelor of Applied Science - IT Networking: Information Systems and Technology",
  "Bachelor of Applied Science - Information Technology",
  "Bachelor of Applied Science - Information Technology: Networking",
  "Bachelor of Applied Science - Application Development",
  "Bachelor of Applied Science - Computer Network Engineering",
  "Bachelor of Applied Science - Information Systems",
  "Bachelor of Applied Science - Information Systems & Technology",
  "Bachelor of Applied Science - Information Technology: Cybersecurity and Networking",
  "Bachelor of Applied Science-Information Technology: Software Development",
  "Bachelor of Science Computer Science",
  "Business Applications Specialist",
  "Business Technology",
  "Cloud Network Technology",
  "Computer Applications Technology",
  "Computer Information Systems",
  "Computer Network Engineering",
  "Computer Network Engineering (JBLM)",
  "Computer Networking",
  "Computer Programming",
  "Computer Science",
  "Computer Science DTA/MRP",
  "Computer Security and Network Technology",
  "Computer Support Specialist",
  "Computer Technology - Network Administration",
  "Computing and Software Development",
  "Computer Support",
  "Cyber Defense and Digital Forensics",
  "Cybersecurity",
  "Cybersecurity & Computer Forensics",
  "Cybersecurity and Network Administration",
  "Cybersecurity and Networking",
  "Data Analyst",
  "Data Analysis and Software Development",
  "Database Administrator",
  "Database Management & Design",
  "Design",
  "Digital Design",
  "Digital Entertainment Design & Production",
  "Digital Forensics and Investigations",
  "Digital Media Arts",
  "Graphic Design and Web Design",
  "Info Tech - Network Administrator",
  "Info Tech - Support Specialist",
  "Info Tech - Web Technologist",
  "Information Systems",
  "Information Systems Project Coordinator",
  "Information Tech Systems",
  "Information Technology",
  "Information Technology - General",
  "Information Technology - Interactive Web Design",
  "Information Technology - Networking (IT-NW)",
  "Information Technology - Security (IT-SEC)",
  "Information Technology - Software Development (IT-SW)",
  "Information Technology - Support Specialist",
  "Information Technology Computer Support",
  "Information Technology Specialist",
  "Information Technology Systems",
  "Information Technology Systems Administration",
  "Information Technology: Application Development",
  "Information Technology: Application Development-Mobile Platforms",
  "IT Support",
  "IT Support Technician",
  "IT Systems Specialist",
  "Microsoft Technologies",
  "Mobile Technology Expert",
  "Multimedia & Interactive Technology-Web Designer",
  "Multimedia & Interactive Technology-Web Developer",
  "Multimedia Communications",
  "Multimedia Communications - Graphics",
  "Network Administrator",
  "Network and Server Administration Specialist",
  "Network Design & Administration",
  "Network Infrastructure Technology (NIT)",
  "Network Operations & Systems Security",
  "Network Security Engineer",
  "Network Services and Computing Systems",
  "Network Technologies",
  "Network Technology and Administration",
  "Networking",
  "Networking and Cybersecurity",
  "Online Marketing & Social Media Architect",
  "Programming",
  "Programming and IT Support",
  "Programming and Software Development",
  "Software Design",
  "Software Development",
  "Systems Administration",
  "User-Centered Design",
  "Visual Communications",
  "Web Application and Cloud Developer",
  "Web Applications Programming Technology - Programming Emphasis",
  "Web Applications Programming Technology - Web Emphasis",
  "Web Design",
  "Web Developer",
  "Web Development",
  "XR (Extended Reality) Development",
];

const itJobTitles = [
  "Software Engineer",
  "Data Scientist",
  "System Administrator",
  "Network Engineer",
  "IT Support Specialist",
  "Cybersecurity Analyst",
  "DevOps Engineer",
  "Cloud Architect",
  "Database Administrator",
  "Front End Developer",
  "Back End Developer",
  "Full Stack Developer",
  "UX/UI Designer",
  "Product Manager",
  "IT Project Manager",
  "QA Engineer",
  "Business Analyst",
  "Solutions Architect",
  "Machine Learning Engineer",
  "Mobile App Developer",
  "Technical Support Engineer",
  "IT Consultant",
  "Site Reliability Engineer",
  "Systems Analyst",
  "Technical Writer",
  "Information Security Manager",
  "Data Analyst",
  "Software Architect",
  "Scrum Master",
  "IT Operations Manager",
  "BI Developer",
  "AI Engineer",
  "IT Director",
  "Technical Recruiter",
  "Salesforce Developer",
  "ERP Consultant",
  "Network Administrator",
  "Help Desk Technician",
  "Penetration Tester",
  "Release Manager",
  "IT Auditor",
  "Big Data Engineer",
  "IoT Specialist",
  "Blockchain Developer",
  "IT Trainer",
  "Game Developer",
  "AR/VR Developer",
  "IT Asset Manager",
  "E-commerce Specialist",
];

const frontendProjectSkills = [
  {
    skill_id: "356e0040-8400-49a0-b772-6f6475776612",
    skill_name: "JavaScript",
    skill_info_url:
      "https://lightcast.io/open-skills/skills/KS1200771D9CR9LB4MWW/javascript-programming-language",
  },
  {
    skill_id: "38943cce-679d-408f-9fb1-6d054012e54f",
    skill_name: ".NET Assemblies",
    skill_info_url:
      "https://lightcast.io/open-skills/skills/KS126XS6CQCFGC3NG79X",
  },
];

const companySizeOptions = [
  "1-10",
  "11-50",
  "51-200",
  "201-500",
  "501-1000",
  "1001-5000",
];

const CareerPrepTrack = ["ACCELERATED", "STANDARD", "EXTENDED"];

const CareerPrepStatus = [
  "Applied", // submitting assessment will be Applied
  "Creating Plan",
  "Meeting Scheduled",
  "Met Career Navigator",
  "Sent Enrollment Form",
  "Enrolled",
  "Completed",
  "Rejected",
  "Withdrawn", // additional option from what was given.
];

const EmploymentTypes = [
  "Full-time",
  "Part-time",
  "Contract",
  "Seasonal",
  "Earn and Learn",
  "Other",
];

const EarnLearnTypes = [
  "Registered Apprenticeship",
  "Non-registered Apprenticeship",
  "Internship",
  "Customized Training",
  "Incumbent Worker Training",
  "Other (Transitional Jobs, Cooperatives, Practicums, Residences, or Fellowships)",
];

export const OccupationCodes = [
  "Computer Systems Analysts (15-1211)",
  "Information Security Analysts (15-1212)",
  "Computer and Information Research Scientists (15-1221)",
  "Computer Network Support Specialists (15-1231)",
  "Computer User Support Specialists (15-1232)",
  "Computer Network Architects (15-1241)",
  "Database Administrators (15-1242)",
  "Database Architects (15-1243)",
  "Network and Computer Systems Administrators (15-1244)",
  "Computer Programmers (15-1251)",
  "Software Developers (15-1252)",
  "Software Quality Assurance Analysts and Testers (15-1253)",
  "Web Developers (15-1254)",
  "Web and Digital Interface Designers (15-1255)",
  "Operations Research Analysts (15-2031)",
  "Data Scientists (15-2051)",
  "Computer Hardware Engineers (17-2061)",
  "Electronics Engineers (17-2072)",
  "Electronics Repairers (49-2094)",
  "HVAC Mechanics (49-9021)",
  "OTHER Computer Occupations (15-1299)",
];

export const TimeUntilCompletion = [
  "N/A",
  "0-3 months",
  "3-6 months",
  "6-9 months",
  "9-12 months",
  "12+ months",
];

/////////////////////////////////////////////////
////////////   helper functions  ////////////////
/////////////////////////////////////////////////

// Helper function to format date to ISO-8601 to match data type in db
function formatISODate(date) {
  return new Date(date).toISOString();
}

function generatePhoneNumber() {
  return faker.number.int({ min: 1000000000, max: 9999999999 }).toString();
}

function generateProblemSolvedDescription(numSentences = 3) {
  return faker.lorem.sentences(numSentences);
}

function generateResponsibilities(numResponsibilities = 3) {
  const responsibilities = [];
  for (let i = 0; i < numResponsibilities; i++) {
    const randomIndex = faker.number.int({
      min: 0,
      max: predefinedResponsibilities.length - 1,
    });
    responsibilities.push(predefinedResponsibilities[randomIndex]);
  }
  return responsibilities.join("\n");
}

function generateSalesPitch(firstName, lastName) {
  const jobTitle = faker.person.jobTitle();
  const companyName = faker.company.name();
  const yearsOfExperience = faker.number.int({ min: 1, max: 20 });
  const skills = [
    faker.hacker.adjective() + " " + faker.hacker.noun(),
    faker.hacker.adjective() + " " + faker.hacker.noun(),
    faker.hacker.adjective() + " " + faker.hacker.noun(),
  ];
  return `
    Hi, my name is ${firstName} ${lastName}. I am a highly skilled ${jobTitle} with over ${yearsOfExperience} years of experience in the industry.
    I have a proven track record of success at ${companyName}, where I contributed to numerous high-profile projects.
    My key skills include ${skills.join(", ")}.
  `;
}

function generateSSN() {
  const ssn = faker.number.int({ min: 100000000, max: 999999999 }).toString();
  return `${ssn.substring(0, 3)}-${ssn.substring(3, 5)}-${ssn.substring(5, 9)}`;
}

function generateCompensation(isInternship) {
  if (isInternship) {
    const stipend = faker.finance.amount({
      min: 1000,
      max: 5000,
      dec: 0,
      autoFormat: true,
    }); // Generate a stipend amount between $1000 and $5000
    return `$${stipend} stipend`;
  } else {
    const minSalary = faker.finance.amount({
      min: 50000,
      max: 70000,
      dec: 0,
      autoFormat: true,
    }); // Generate a minimum salary between $50,000 and $70,000
    const maxSalary = faker.finance.amount({
      min: 80000,
      max: 120000,
      dec: 0,
      autoFormat: true,
    }); // Generate a maximum salary between $80,000 and $100,000
    return `$${minSalary} - $${maxSalary} / year`;
  }
}

function getRandomUserPhoto() {
  const gender = faker.helpers.arrayElement(["men", "women"]);
  const number = faker.number.int({ min: 0, max: 99 });
  return `https://randomuser.me/api/portraits/${gender}/${number}.jpg`;
}

function getRandomLogo() {
  const domain = faker.helpers.arrayElement([
    "google.com",
    "apple.com",
    "microsoft.com",
    "amazon.com",
    "facebook.com",
    "twitter.com",
    "linkedin.com",
    "instagram.com",
    "salesforce.com",
    "oracle.com",
    "adobe.com",
    "netflix.com",
    "spotify.com",
    "uber.com",
    "lyft.com",
    "tesla.com",
    "airbnb.com",
    "dropbox.com",
    "slack.com",
    "zoom.us",
    "stripe.com",
    "paypal.com",
    "shopify.com",
    "github.com",
    "bitbucket.org",
    "asana.com",
    "atlassian.com",
    "squareup.com",
    "intuit.com",
    "zendesk.com",
    "hubspot.com",
  ]);
  return `https://logo.clearbit.com/${domain}`;
}

/////////////////////////////////////////////////
/////////////   seed functions  /////////////////
/////////////////////////////////////////////////

async function seedMockUsers(numUsers = 4) {
  console.log("Seeding Users...");
  const waLocations = await prisma.postalGeoData.findMany({
    where: {
      stateCode: "WA",
    },
    select: {
      zip: true,
    },
  });
  if (numUsers <= 4) {
    for (let idx = 0; idx < numUsers; idx++) {
      await prisma.user.create({
        data: {
          id: uuidv4(),
          first_name: users[idx].firstName,
          last_name: users[idx].lastName,
          birthdate: formatISODate(users[idx].birthDate),
          email: users[idx].email,
          // password: hashedPassword,
          role: users[idx].role,
          phone: null,
          gender: null,
          race: null,
          photo_url: getRandomUserPhoto(),
          locationData: {
            connect: {
              zip: faker.helpers.arrayElement(waLocations).zip,
            },
          },
          createdAt: new Date(),
        },
      });
    }
  } else {
    for (let idx = 0; idx < numUsers; idx++) {
      const fName = faker.person.firstName();
      const lName = faker.person.lastName();
      const filteredRoles = roles.filter((role) => role !== "CASE_MANAGER");
      await prisma.user.create({
        data: {
          id: uuidv4(),
          first_name: fName,
          last_name: lName,
          birthdate: faker.date.birthdate({ min: 18, max: 65, mode: "age" }),
          email: faker.internet.email({ firstName: fName, lastName: lName }),
          role: faker.helpers.arrayElement(filteredRoles),
          phone: generatePhoneNumber(),
          photo_url: getRandomUserPhoto(),
          locationData: {
            connect: {
              zip: faker.helpers.arrayElement(waLocations).zip,
            },
          },
          createdAt: new Date().toISOString(),
        },
      });
    }
  }
  const fName = faker.person.firstName();
  const lName = faker.person.lastName();
  await prisma.user.create({
    data: {
      id: uuidv4(),
      first_name: fName,
      last_name: lName,
      birthdate: faker.date.birthdate({ min: 18, max: 65, mode: "age" }),
      email: faker.internet.email({ firstName: fName, lastName: lName }),
      role: "CASE_MANAGER",
      phone: generatePhoneNumber(),
      photo_url: getRandomUserPhoto(),
      locationData: {
        connect: {
          zip: faker.helpers.arrayElement(waLocations).zip,
        },
      },
      createdAt: new Date().toISOString(),
    },
  });
  console.log(`Seeded ${numUsers + 1} users.\n`);
}

export const EduProviderPathways = {
  // TODO: align with ICT Job Group Families
  SoftwareDeveloper: "Software Development",
  ITCloudSupport: "Infrastructure and Operations",
  Cybersecurity: "Cybersecurity",
  DataAnalytics: "Data Science",
  ProfessionSkillsTraining: "Profession Skills Training",
  BusinessMgmt: "Business and Management",
  Design: "Design and User Experience",
  Tester: "Testing and Quality Assurance",
};
async function seedPartnerPathways() {
  const pathways = [
    EduProviderPathways.SoftwareDeveloper,
    EduProviderPathways.ITCloudSupport,
    EduProviderPathways.Cybersecurity,
    EduProviderPathways.DataAnalytics,
    EduProviderPathways.ProfessionSkillsTraining,
    EduProviderPathways.BusinessMgmt,
    EduProviderPathways.Design,
    EduProviderPathways.Tester,
  ];

  console.log("Seeding Pathways...");
  const uuids = [
    "0645cc89-e942-48b4-a34a-f7ad7e87dec3",
    "79608104-d50e-4d0f-b541-2a9de7bc0f89",
    "a54f3940-301c-4e2e-85e8-bcaf244c89bb",
    "b28fbd79-c3ea-47b5-9bbf-6f7f8f9c6009",
    "79608104-c3ea-47b5-9bbf-6f7f8f9c6009",
    "c45fce80-c3ea-47b5-b541-6f7f8f9c6009",
    "a46fbd79-c3ea-47b5-9bbf-6f7f8f9c6009",
    "56308104-c3ea-47b5-9bbf-6f7f8f9c6009",
    "478fce80-c3ea-47b5-b541-6f7f8f9c6009",
  ];

  let idx = 0;
  for (const path of pathways) {
    if (!path) continue; // Skip any undefined or commented-out entries
    await prisma.pathways.create({
      data: {
        pathway_id: uuids[idx],
        pathway_title: path,
      },
    });
    idx++;
  }
  console.log(`Seeded ${pathways.filter(Boolean).length} Pathways.\n`);
}

async function seedTechnologyAreas() {
  console.log("Seeding Technology Areas...");
  for (const area of itOccupationTechnologyAreas) {
    await prisma.technology_areas.create({
      data: {
        id: area.id,
        title: area.name,
      },
    });
  }
  console.log(
    `Seeded ${itOccupationTechnologyAreas.length} technology areas.\n`,
  );
}

async function seedGeneralEdProviders() {
  try {
    console.log("Seeding General Education Providers...");
    // Insert high schools
    const highSchoolResult = await prisma.edu_providers.createMany({
      data: highSchools.map((school) => ({
        name: school,
        edu_type: "High school",
      })),
    });

    // Insert colleges
    const collegeResult = await prisma.edu_providers.createMany({
      data: colleges.map((college) => ({
        name: college,
        edu_type: "College",
      })),
    });

    console.log(`Seeded ${highSchoolResult.count} High schools.`);
    console.log(`Seeded ${collegeResult.count} Colleges.`);
    console.log(
      `Finished seeding ${highSchoolResult.count + collegeResult.count} general WA state training providers.\n`,
    );
  } catch (error) {
    console.error("Error inserting data:", error);
  } finally {
    await prisma.$disconnect();
  }
}

async function seedPartnerEdProvidersAndPrograms() {
  try {
    console.log("Seeding Partner Education Providers and Programs...");

    for (const provider of partnerProvidersAndPrograms) {
      const eduProvider = await prisma.edu_providers.upsert({
        where: {
          name: provider?.eduProvider,
        },
        update: {
          name: provider?.eduProvider ? provider.eduProvider : null,
          edu_type: provider?.edu_type ? provider.edu_type : null,
          contact: provider?.contact ? provider.contact : null,
          contact_email: provider?.contactEmail ? provider.contactEmail : null,
          edu_url: provider?.url ? provider.url : null,
          mission: provider?.missionStatement
            ? provider.missionStatement
            : null,
          providerDescription: provider?.providerDescription
            ? provider.providerDescription
            : null,
          setsApartStatement: provider?.setsApartStatement
            ? provider.setsApartStatement
            : null,
          screeningCriteria: provider?.screeningCriteria
            ? provider.screeningCriteria
            : null,
          recruitingSources: provider?.recruitingSources
            ? provider.recruitingSources
            : null,
          programCount: provider?.programCount ? provider.programCount : null,
          cost: provider?.cost ? provider.cost : null,
          isCoalitionMember: true,
          isAdminReviewed: true,
        },
        create: {
          name: provider?.eduProvider ? provider.eduProvider : null,
          edu_type: provider?.edu_type ? provider.edu_type : null,
          contact: provider?.contact ? provider.contact : null,
          contact_email: provider?.contactEmail ? provider.contactEmail : null,
          edu_url: provider?.url ? provider.url : null,
          mission: provider?.missionStatement
            ? provider.missionStatement
            : null,
          providerDescription: provider?.providerDescription
            ? provider.providerDescription
            : null,
          setsApartStatement: provider?.setsApartStatement
            ? provider.setsApartStatement
            : null,
          screeningCriteria: provider?.screeningCriteria
            ? provider.screeningCriteria
            : null,
          recruitingSources: provider?.recruitingSources
            ? provider.recruitingSources
            : null,
          programCount: provider?.programCount ? provider.programCount : null,
          cost: provider?.cost ? provider.cost : null,
          isCoalitionMember: true,
          isAdminReviewed: true,
        },
      });
      console.log(`Created edu_provider: ${eduProvider.name}`);

      for (const program of provider.programs) {
        // Find the program in the programs table
        let existingProgram = await prisma.programs.findUnique({
          where: { title: program.name },
        });

        // If the program doesn't exist, create it
        if (!existingProgram) {
          existingProgram = await prisma.programs.create({
            data: {
              title: program.name,
            },
          });
          console.log(`Created program: ${existingProgram.title}`);
        }

        // Create provider_programs entry
        // Check if provider_program already exists to avoid duplicates
        let existingProviderProgram = await prisma.provider_programs.findFirst({
          where: {
            edu_provider_id: eduProvider.id,
            program_id: existingProgram.id,
          },
        });

        if (!existingProviderProgram) {
          await prisma.provider_programs.create({
            data: {
              training_program_id: uuidv4(), // Generate a new UUID
              edu_provider_id: eduProvider.id,
              program_id: existingProgram.id,
              // Map other fields if available in your schema
              costSummary: program.cost ? program.cost : null,
              targetedJobRoles:
                program.targetedJobRoles.length > 0
                  ? program.targetedJobRoles.join(", ")
                  : null, // Convert array to string
              programDescription: program.programDescription
                ? program.programDescription
                : null,
              months: program.months ? program.months : null,
              hoursPerWeek: program.hoursPerWeek ? program.hoursPerWeek : null,
              targetPopulation: program.targetPopulation
                ? program.targetPopulation
                : null,
              serviceArea: program.serviceArea ? program.serviceArea : null,
              pathways:
                program.pathways.length > 0 ? program.pathways.join("~") : null, // Convert array to string
            },
          });
          console.log(
            `Created provider_program linking provider "${eduProvider.name}" and program "${existingProgram.title}"`,
          );
        } else {
          console.log(
            `Provider_program already exists for provider "${eduProvider.name}" and program "${existingProgram.title}"`,
          );
        }
      }
    }

    console.log("Finished seeding Partner Education Providers and Programs.\n");
  } catch (error) {
    console.error("Error inserting data:", error);
  } finally {
    await prisma.$disconnect();
  }
}

async function seedGeneralPrograms() {
  try {
    console.log("Seeding General Programs...");
    // Insert high schools
    const programsResult = await prisma.programs.createMany({
      data: programs.map((program) => ({
        title: program,
      })),
    });
    console.log(`Seeded ${programsResult.count} general programs.\n`);
  } catch (error) {
    console.error("Error inserting data:", error);
  } finally {
    await prisma.$disconnect();
  }
}

async function seedPartnerPrograms() {
  try {
    console.log("Seeding Provider Programs...");

    // Extract unique program names from partnerProvidersAndPrograms
    const programsData = partnerProvidersAndPrograms.flatMap((provider) =>
      provider.programs.map((program) => ({
        title: program.name,
      })),
    );
    // Filter out duplicate program names
    const uniquePrograms = Array.from(
      new Map(programsData.map((program) => [program.title, program])).values(),
    );

    // Check for existing programs in the database
    const existingPrograms = await prisma.programs.findMany({
      select: { title: true },
    });
    const existingProgramNames = new Set(existingPrograms.map((p) => p.title));

    // Add only new programs to the database
    const newPrograms = uniquePrograms.filter(
      (program) => !existingProgramNames.has(program.title),
    );

    if (newPrograms.length > 0) {
      const programsResult = await prisma.programs.createMany({
        data: newPrograms,
      });
      console.log(`Seeded ${programsResult.count} new programs.`);
    } else {
      console.log("No new programs to seed.");
    }
  } catch (error) {
    console.error("Error inserting data:", error);
  } finally {
    await prisma.$disconnect();
  }
}

async function SeedMockEdProvidersAddresses() {
  console.log(`Seeding Institution Addresses...`);
  const edInstitutions = await prisma.edu_providers.findMany({
    select: {
      id: true,
      name: true, // needed to filter out the unknown. In case a jobseeker does not enter an institution.
    },
  });
  const waAddresses = await prisma.postalGeoData.findMany({
    where: {
      stateCode: "WA",
    },
  });
  const addresses = edInstitutions
    .filter((institution) => institution.name !== "No data")
    .map((institution) => {
      const locationInfo = faker.helpers.arrayElement(waAddresses);
      return {
        edu_address_id: uuidv4(),
        edu_provider_id: institution.id,
        street1: faker.location.streetAddress(),
        street2: faker.location.secondaryAddress(),
        zip: locationInfo.zip,
      };
    });

  for (const address of addresses) {
    await prisma.edu_addresses.create({
      data: address,
    });
  }
  console.log(`Seeded ${addresses.length} Institution Addresses.\n`);
}

async function seedSubcategories() {
  console.log("Seeding IT skill subcategories from Lightcast...");
  const subcategoryPromises = subcategoriesData.map((category) => {
    return prisma.skill_subcategories.create({
      data: {
        skill_subcategory_id: uuidv4(),
        subcategory_name: category.skill_category,
        subcategory_description: "",
      },
    });
  });

  const subcategories = await Promise.all(subcategoryPromises);
  console.log(`Seeded ${subcategories.length} IT skill subcategories.\n`);
  return subcategories;
}

async function seedSkills() {
  const subcategories = await prisma.skill_subcategories.findMany();
  console.log("Seeding skills...");
  let skillsCount = 0;
  const skillsToCreate = subcategories.flatMap((subcategory) => {
    const relatedSkills = skillsData_v2.filter(
      (s) =>
        s.skill_category.toLowerCase().trim() ===
        subcategory.subcategory_name.toLowerCase().trim(),
    );

    return relatedSkills.map((skill) => {
      // Check if the skill is in the manual skills array
      const manualSkill = frontendProjectSkills.find(
        (ms) =>
          ms.skill_name.toLowerCase().trim() ===
          skill.skill.toLowerCase().trim(),
      );
      skillsCount++;
      if (manualSkill) {
        return {
          skill_id: manualSkill.skill_id,
          skill_name: manualSkill.skill_name,
          skill_info_url: manualSkill.skill_info_url,
          skill_subcategory_id: subcategory.skill_subcategory_id,
        };
      } else {
        return {
          skill_id: uuidv4(),
          skill_name: skill.skill,
          skill_info_url: skill.info_url,
          skill_subcategory_id: subcategory.skill_subcategory_id,
        };
      }
    });
  });

  await prisma.skills.createMany({
    data: skillsToCreate,
  });

  console.log(`Seeded ${skillsCount} skills.\n`);
}

async function seedJobSeekers() {
  const jobSeekers = await prisma.user.findMany({
    where: {
      role: "JOBSEEKER",
    },
  });
  // Fetch pathways, excluding the "Other" pathway if in a development environment
  const isProduction = process.env.NODE_ENV === "production"; // Check the environment
  const pathways = await prisma.pathways.findMany({
    where: isProduction ? {} : { pathway_title: { not: "Other" } }, // Exclude "Other" in development
    select: {
      pathway_id: true,
    },
  });
  console.log("Seeding jobseekers...");
  for (const jobSeeker of jobSeekers) {
    const isEnrolledEdProgram = Math.random() < 0.6; // 60% chance of being enrolled in ed program.
    const edLevel = isEnrolledEdProgram
      ? faker.helpers.arrayElement(edPrograms)
      : "None";
    let currentJobTitle;
    if (isEnrolledEdProgram && edLevel !== "None") {
      currentJobTitle =
        Math.random() < 0.4 ? faker.person.jobTitle() : "Student";
    } else {
      currentJobTitle = faker.person.jobTitle();
    }
    const assignedPool = faker.helpers.arrayElement([
      "Recommended",
      "Job Ready",
      "Not Job Ready",
    ]);
    const jobSeekerData = {
      jobseeker_id: uuidv4(),
      user_id: jobSeeker.id,
      targeted_pathway: faker.helpers.arrayElement(pathways).pathway_id,
      is_enrolled_ed_program: isEnrolledEdProgram,
      highest_level_of_study_completed:
        faker.helpers.arrayElement(highestDegreeType),
      current_grade_level:
        edLevel === "High school" || edLevel === "College"
          ? faker.helpers.arrayElement([
              "freshman",
              "sophomore",
              "junior",
              "senior",
            ])
          : undefined,
      current_enrolled_ed_program: edLevel,
      intern_hours_required:
        edLevel === "College" || edLevel === "Pre-apprenticeship"
          ? faker.number.int({
              min: 75,
              max: 300,
            })
          : 0,
      intro_headline: generateSalesPitch(
        jobSeeker.first_name,
        jobSeeker.last_name,
      ),
      current_job_title: currentJobTitle,
      years_work_exp: faker.number.int({ min: 0, max: 3 }), // years of experience
      portfolio_url: faker.internet.url(),
      video_url: faker.internet.url(),
      assignedPool: assignedPool,
      careerPrepTrackRecommendation:
        assignedPool === "Recommended"
          ? null // Assign null for 'Recommended' jobseekers
          : assignedPool === "Job Ready"
            ? faker.datatype.boolean() // 50/50 split
              ? CareerPrepTrack[0]
              : CareerPrepTrack[1]
            : assignedPool === "Not Job Ready" && faker.datatype.boolean() // 50/50 split
              ? CareerPrepTrack[2]
              : null,
      employment_type_sought: faker.helpers.arrayElement([
        "Full-time",
        "Part-time",
        "Internship",
        "Contract",
        "Any",
      ]),
    };

    await prisma.jobseekers.create({
      data: jobSeekerData,
    });
  }
  console.log(`Created ${jobSeekers.length} jobseekers.\n`);
}

async function seedJobSeekersPrivateData() {
  try {
    const jobseekers = await prisma.jobseekers.findMany();
    console.log("Seeding jobseeker private data...");

    for (const js of jobseekers) {
      await prisma.jobseekers_private_data.create({
        data: {
          jobseeker_private_data_id: uuidv4(),
          jobseeker_id: js.jobseeker_id,
          ssn: generateSSN(),
          is_authorized_to_work_in_usa: faker.datatype.boolean()
            ? Boolean(faker.number.int({ min: 0, max: 1 }))
            : undefined,
          job_sponsorship_required: faker.datatype.boolean()
            ? Boolean(faker.number.int({ min: 0, max: 1 }))
            : undefined,
          is_veteran: faker.helpers.arrayElement(["yes", "no", "undisclosed"]),
          disability_status: faker.helpers.arrayElement([
            "yes",
            "none",
            "undisclosed",
          ]),
          disability: faker.helpers.arrayElement([
            "cognitive",
            "emotional",
            "hearing",
            "mental",
            "physical",
            "visual",
            "other",
            "unknown",
            "yes",
            "no",
            "undisclosed",
          ]),
        },
      });
    }

    console.log(
      `Seeded ${jobseekers.length} entries for jobseeker private data.\n`,
    );
  } catch (error) {
    console.error("Error seeding jobseeker private data:", error);
  } finally {
    await prisma.$disconnect();
  }
}

async function seedJobSeekerSkills() {
  console.log(`Seeding Jobseeker skills...`);
  const jobseekers = await prisma.jobseekers.findMany();
  const skills = await prisma.skills.findMany();
  let skillCount = 0;

  for (const js of jobseekers) {
    const usedSkills = new Set();
    for (let i = 0; i < 5; i++) {
      let skill;

      do {
        skill = faker.helpers.arrayElement(skills);
      } while (usedSkills.has(skill.skill_id));

      usedSkills.add(skill.skill_id);

      await prisma.jobseeker_has_skills.create({
        data: {
          jobseeker_id: js.jobseeker_id,
          skill_id: skill.skill_id,
        },
      });
      skillCount++;
    }
  }
  console.log(`Seeded ${skillCount} Jobseeker skills.\n`);
}

async function seedJobSeekersEducation() {
  let edCount = 0;
  const jobseekers = await prisma.jobseekers.findMany();

  const edProviders = await prisma.edu_providers.findMany({
    where: {
      edu_type: "College",
    },
    select: {
      id: true,
      edu_type: true,
    },
  });

  console.log("Seeding jobseeker education...");
  const programs = await prisma.programs.findMany();
  for (const jobseeker of jobseekers) {
    const numEntries = jobseeker.is_enrolled_ed_program
      ? faker.number.int({
          min: 1,
          max: 3,
        })
      : faker.number.int({ min: 0, max: 3 });

    for (let i = 0; i < numEntries; i++) {
      const edProviderId = faker.helpers.arrayElement(edProviders).id;
      const startDate = faker.date.past({ years: 15 });
      const endDate = faker.date.between({ from: startDate, to: new Date() });
      const isEnrolled = Boolean(faker.number.int({ min: 0, max: 1 }));
      const jobseekerEducationData = {
        id: uuidv4(),
        isEnrolled: isEnrolled,
        startDate: startDate,
        gradDate: endDate,
        enrollmentStatus: isEnrolled
          ? faker.helpers.arrayElement([
              "Admitted, not yet enrolled",
              "Currently active in program",
            ])
          : faker.helpers.arrayElement([
              "Graduated / Completed",
              "Withdrawn / terminated",
            ]),
        degreeType: faker.helpers.arrayElement(degreeTypes),
        edLevel: "College",
        jobseekers: {
          connect: {
            jobseeker_id: jobseeker.jobseeker_id,
          },
        },
        eduProviders: {
          connect: {
            id: edProviderId,
          },
        },
        program: {
          connect: {
            id: faker.helpers.arrayElement(programs).id,
          },
        },
      };

      await prisma.jobseekers_education.create({
        data: jobseekerEducationData,
      });
      edCount++;
    }
  }
  console.log(`Created ${edCount} jobseeker education records.\n`);
}

async function seedJobseekerWorkExperiences() {
  try {
    const jobseekers = await prisma.jobseekers.findMany();
    const industry_sectors = await prisma.industry_sectors.findMany({
      select: {
        industry_sector_id: true,
      },
    });
    const tech_areas = await prisma.technology_areas.findMany({
      select: {
        id: true,
      },
    });
    console.log("Seeding work experiences...");
    let workExpCount = 0;
    const promises = jobseekers.map((js) => {
      const workExperiencePromises = [];
      // Create two work experiences for each jobseeker
      for (let i = 0; i < 2; i++) {
        const startDate = faker.date.past({ years: 5 });
        const isCurrentJob = Math.random() < 0.2; // 20% chance of being current job

        workExperiencePromises.push(
          prisma.workExperience.create({
            data: {
              workId: uuidv4(),
              jobseekerId: js.jobseeker_id,
              techAreaId: faker.helpers.arrayElement(tech_areas).id,
              sectorId:
                faker.helpers.arrayElement(industry_sectors).industry_sector_id,
              company: faker.company.name(),
              isInternship: faker.datatype.boolean(),
              jobTitle: faker.person.jobTitle(),
              isCurrentJob: isCurrentJob,
              startDate: startDate,
              endDate: isCurrentJob
                ? null
                : faker.date.between({ from: startDate, to: new Date() }),
              responsibilities: generateResponsibilities(
                faker.number.int({ min: 3, max: 6 }),
              ),
            },
          }),
        );
      }
      workExpCount += workExperiencePromises.length;
      return Promise.all(workExperiencePromises);
    });
    await Promise.all(promises);
    console.log(`Seeded ${workExpCount} work experiences.\n`);
  } catch (error) {
    console.error("Error seeding work experiences:", error);
  } finally {
    await prisma.$disconnect();
  }
}

async function seedProjectExperiences() {
  try {
    let projectCount = 0;
    const jobseekers = await prisma.jobseekers.findMany();
    console.log(`Seeding project experiences...`);
    const promises = jobseekers.map((js) => {
      const projectExperiencePromises = [];

      // Create three project experiences for each jobseeker
      for (let i = 0; i < 3; i++) {
        const startDate = faker.date.past({ years: 2 });
        const completionDate = faker.date.between({
          from: startDate,
          to: new Date(),
        });
        projectExperiencePromises.push(
          prisma.projectExperiences.create({
            data: {
              projectId: uuidv4(),
              jobseekerId: js.jobseeker_id,
              projTitle: faker.helpers.arrayElement(itProjectTitles),
              projectRole: faker.helpers.arrayElement(developmentTeamRoles),
              startDate: startDate,
              completionDate: completionDate,
              problemSolvedDescription: generateProblemSolvedDescription(
                faker.number.int({ min: 3, max: 12 }),
              ),
              teamSize: faker.number.int({ min: 3, max: 10 }),
              repoUrl: faker.internet.url(),
              demoUrl: faker.internet.url(),
            },
          }),
        );
      }
      projectCount += projectExperiencePromises.length;
      return Promise.all(projectExperiencePromises);
    });
    console.log(`Seeded ${projectCount} project experiences.\n`);
    await Promise.all(promises);
  } catch (error) {
    console.error("Error seeding project experiences:", error);
  } finally {
    await prisma.$disconnect();
  }
}

async function seedProjectSkills() {
  console.log(`Seeding Project skills...`);
  const projects = await prisma.projectExperiences.findMany();
  const skills = await prisma.skills.findMany();
  let skillCount = 0;

  for (const p of projects) {
    const usedSkills = new Set();
    for (let i = 0; i < 3; i++) {
      let skill;
      do {
        skill = faker.helpers.arrayElement(skills);
      } while (usedSkills.has(skill.skill_id));

      usedSkills.add(skill.skill_id);

      await prisma.project_has_skills.create({
        data: {
          proj_exp_id: p.projectId,
          skill_id: skill.skill_id,
        },
      });

      skillCount++;
    }
  }

  console.log(`Seeded ${skillCount} Project skills.\n`);
}

async function seedJobSeekerCertificates() {
  try {
    let certCount = 0;
    const jobseekers = await prisma.jobseekers.findMany();
    console.log(`Seeding jobseeker certificates...`);
    const promises = jobseekers.map((js) => {
      const certificatePromises = [];
      // Create a copy of the certifications array
      const availableCertifications = [...itCertifications];

      // Create 3 certificates for each jobseeker
      for (let i = 0; i < 3; i++) {
        const issueDate = faker.date.past({ years: 5 });
        const expirationDate = faker.date.future({
          years: 2,
          refDate: issueDate,
        });
        // Randomly select a certification and remove it from the available list
        const certificationIndex = faker.number.int({
          min: 0,
          max: availableCertifications.length - 1,
        });
        const certification = availableCertifications.splice(
          certificationIndex,
          1,
        )[0];

        certificatePromises.push(
          prisma.certificates.create({
            data: {
              certId: uuidv4(),
              jobSeekerId: js.jobseeker_id,
              name: certification.name,
              logoUrl: certification.logo_url,
              issuingOrg: certification.issuing_org,
              credentialId: certification.credential_id,
              credentialUrl: certification.credential_url,
              issueDate: issueDate,
              expiryDate: expirationDate,
            },
          }),
        );
      }
      certCount += certificatePromises.length;
      return Promise.all(certificatePromises);
    });

    await Promise.all(promises);
    console.log(`Seeded ${certCount} jobseeker certificates.\n`);
  } catch (error) {
    console.error("Error seeding jobseeker certificates:", error);
  } finally {
    await prisma.$disconnect();
  }
}

async function seedIndustrySectors() {
  console.log(`Seeding Industry Sectors...`);
  for (const sector of industrySectors) {
    await prisma.industry_sectors.create({
      data: {
        industry_sector_id: uuidv4(),
        sector_title: sector,
      },
    });
  }
  console.log(`Seeded ${industrySectors.length} Industry Sectors.\n`);
}

async function seedMockCompanies() {
  console.log("Seeding Mock companies...");
  const sectors = await prisma.industry_sectors.findMany();
  const cfaAdmin = await prisma.user.create({
    data: {
      id: uuidv4(),
      first_name: "CFA",
      last_name: "ADMIN",
      birthdate: faker.date.birthdate({ min: 18, max: 65, mode: "age" }),
      email: "admin@computingforall.org",
      role: "ADMIN",
      phone: generatePhoneNumber(),
      photo_url: getRandomUserPhoto(),
      locationData: {
        connect: {
          zip: "98004",
        },
      },
      createdAt: new Date().toISOString(),
    },
  });
  for (let i = 0; i < 5; i++) {
    await prisma.companies.create({
      data: {
        createdBy: cfaAdmin.id, // hacking employerId to get it to work will not be related employer
        company_id: uuidv4(),
        industry_sector_id:
          faker.helpers.arrayElement(sectors).industry_sector_id,
        company_name: faker.company.name(),
        company_logo_url: getRandomLogo(),
        about_us: faker.lorem.sentences(2),
        company_email: faker.internet.email(),
        year_founded: faker.number.int({ min: 1900, max: 2024 }),
        company_website_url: faker.internet.url(),
        company_video_url: faker.internet.url(),
        company_phone: generatePhoneNumber(),
        company_mission: faker.lorem.sentences(3),
        company_vision: faker.lorem.sentences(3),
        size: faker.helpers.arrayElement(companySizeOptions),
        estimated_annual_hires: faker.number.int({ min: 1, max: 10 }),
      },
    });
  }
  console.log(`Finished seeding ${5} Mock companies.\n`);
}

async function seedPartnerCompanies() {
  console.log("Seeding Partner Companies...");
  for (const company of partnerCompanies) {
    let industrySector = await prisma.industry_sectors.findFirst({
      where: {
        sector_title: company.industrySector,
      },
    });
    // check if company exists in the database
    let existingCompany = await prisma.companies.findUnique({
      where: { company_name: company.name },
    });

    let newCompany;
    // if not, create the company
    if (!existingCompany) {
      newCompany = await prisma.companies.create({
        data: {
          company_id: uuidv4(),
          company_name: company.name,
          company_logo_url: company.companyLogoUrl,
          about_us: company.aboutUs,
          company_email: company.email,
          year_founded: 0,
          company_website_url: company.websiteUrl,
          company_mission: company.mission,
          company_vision: company.vision,
          size: company.size,
          estimated_annual_hires: company.estimatedAnnualHires,
          is_approved: true,
          industry_sectors: {
            connect: {
              industry_sector_id: industrySector.industry_sector_id,
            },
          },
        },
      });
    } else {
      newCompany = existingCompany;
    }
    // Add company addresses for each zip code in locationsByZip
    if (company.locationsByZip && company.locationsByZip.length > 0) {
      for (const zip of company.locationsByZip) {
        await prisma.company_addresses.create({
          data: {
            company_address_id: uuidv4(),
            company_id: newCompany.company_id, // Use the created company's ID
            zip: zip,
          },
        });
      }
    }
  }
}

async function seedEmployers() {
  console.log(`Seeding Employers...`);
  const companies = await prisma.companies.findMany({
    select: {
      company_id: true,
    },
  });
  const employers = await prisma.user.findMany({
    where: {
      role: "EMPLOYER",
    },
  });
  for (const e of employers) {
    await prisma.employers.create({
      data: {
        employer_id: uuidv4(),
        user_id: e.id,
        company_id: faker.helpers.arrayElement(companies).company_id,
        job_title: faker.person.jobTitle(),
        work_address_id: null,
        linkedin_url: null,
      },
    });
  }
  console.log(`Seeded ${employers.length} Employers.\n`);
}

async function seedCompanyAddresses() {
  const companies = await prisma.companies.findMany();
  const waLocationData = await prisma.postalGeoData.findMany({
    where: {
      stateCode: "WA",
    },
    select: {
      zip: true,
    },
  });
  for (const c of companies) {
    await prisma.company_addresses.create({
      data: {
        company_address_id: uuidv4(),
        company_id: c.company_id,
        zip: faker.helpers.arrayElement(waLocationData).zip,
      },
    });
  }
}

async function seedCompanyTestimonials() {
  console.log(`Seeding Company Testimonials...`);
  let count = 0;

  const companies = await prisma.companies.findMany();
  for (const c of companies) {
    const employer = await prisma.employers.findFirst({
      where: {
        company_id: c.company_id,
      },
    });
    for (let i = 0; i < 3; i++) {
      await prisma.company_testimonials.create({
        data: {
          testimonial_id: uuidv4(),
          company_id: c.company_id,
          employer_id: employer.employer_id,
          text: faker.lorem.sentences(2),
          author: faker.person.fullName(),
        },
      });
    }
    count++;
  }
  console.log(`Seeded ${count} Company Testimonials.\n`);
}

// async function seedSocialMediaPlatforms() {
//     console.log(`Seeding social media platforms...`);
//     const socialPromises = socialMediaPlatforms.map(async platform => {
//         await prisma.social_media_platforms.create({
//             data: {
//                 social_platform_id: uuidv4(),
//                 platform: platform.platform,
//                 social_logo_url: platform.social_logo_url,
//             }
//         });
//     });
//
//     // Wait for all promises to complete
//     await Promise.all(socialPromises);
//     console.log(`Seeded ${socialPromises.length} social media platforms.\n`);
// }

// async function seedCompanySocialLinks() {
//     console.log(`Seeding Company Social Links...`)
//     const companies = await prisma.companies.findMany();
//     const platforms = await prisma.social_media_platforms.findMany();
//     let count = 0;
//     for (const c of companies) {
//         const employer = await prisma.employers.findFirst({
//             where: {
//                 company_id: c.company_id
//             }
//         })
//         for (let i = 0; i < 3; i++) {
//             let platform = platforms.pop();
//             await prisma.company_social_links.create({
//                 data: {
//                     social_media_id: uuidv4(),
//                     employer_id: employer.employer_id,
//                     company_id: c.company_id,
//                     social_platform_id: platform.social_platform_id,
//                     social_url: `https://www.${platform.platform.toLowerCase()}/${c.company_name.toLowerCase().replace(/[\s\W]/g, '')}`,
//                 }
//             });
//             count++;
//         }
//     }
//     console.log(`Seeded ${count} Company Social Links.\n`)
// }

async function seedJobPostings() {
  try {
    console.log(`Seeding Job Postings...`);
    const employers = await prisma.employers.findMany();
    const techAreas = await prisma.technology_areas.findMany({
      select: {
        id: true,
      },
    });
    const sectors = await prisma.industry_sectors.findMany({
      select: {
        industry_sector_id: true,
      },
    });

    let totalJobPostings = 0;
    for (const e of employers) {
      for (let i = 0; i < 3; i++) {
        const companyAddresses = await prisma.company_addresses.findMany({
          where: {
            company_id: e.company_id,
          },
        });
        try {
          // 40% chance job post is an internship
          const isInternship = Math.random() < 0.4;
          // paid if not internship, internships have a 50% chance of being paid
          const isPaid = !isInternship ? true : Math.random() < 0.5;
          const regionInfo =
            waStateCountiesWithZipCodes[
              faker.number.int({
                min: 0,
                max: waStateCountiesWithZipCodes.length - 1,
              })
            ];
          const employmentType = faker.helpers.arrayElement(EmploymentTypes);
          await prisma.job_postings.create({
            data: {
              job_posting_id: uuidv4(),
              company_id: e.company_id,
              employer_id: e.employer_id,
              location_id:
                faker.helpers.arrayElement(companyAddresses).company_address_id,
              sector_id: faker.helpers.arrayElement(sectors).industry_sector_id,
              tech_area_id: faker.helpers.arrayElement(techAreas).id,
              job_title: faker.helpers.arrayElement(itJobTitles),
              job_description: faker.lorem.sentences(
                faker.number.int({ min: 2, max: 5 }),
              ),
              is_internship: isInternship,
              is_paid: isPaid,
              employment_type: employmentType,
              location: faker.helpers.arrayElement([
                "on-site",
                "remote",
                "hybrid",
              ]),
              salary_range:
                isPaid > 0
                  ? generateCompensation(isInternship)
                  : "unpaid internship",
              county: regionInfo.county,
              zip: faker.helpers.arrayElement(regionInfo.zipCodes),
              publish_date: faker.date.soon(),
              unpublish_date: faker.date.future(),
              job_post_url: faker.internet.url(),
              assessment_url: faker.internet.url(),
              earn_and_learn_type:
                employmentType != "Earn and Learn"
                  ? employmentType
                  : faker.helpers.arrayElement(EarnLearnTypes),
              occupation_code: faker.helpers.arrayElement(OccupationCodes),
            },
          });
          totalJobPostings++; // Increment the total job postings counter
        } catch (innerError) {
          console.error(
            `Error seeding job posting for employer: ${e.employer_id}.\n`,
            innerError,
          );
        }
      }
    }
    console.log(`Seeded ${totalJobPostings} Job Postings in total.\n`);
  } catch (error) {
    console.error("Error seeding job postings:", error);
    throw error; // Rethrow the error to be caught by the caller
  } finally {
    await prisma.$disconnect();
  }
}

async function seedPostalGeoData(
  jsonFilePath,
  logFrequency = 10,
  batchSize = 1000,
) {
  console.log(
    "Seeding Postal Geo Data (zip, city, state, stateId, geographic coords)...",
  );

  let jsonData = JSON.parse(
    fs.readFileSync(path.resolve(__dirname, jsonFilePath), "utf-8"),
  );
  // Filter data to only include entries where state_code is "WA" for dev
  jsonData = jsonData.filter((item) => item.stateCode === "WA");

  let totalInserted = 0;
  let batchCount = 0;

  // Function to process each batch
  const processBatch = async (batch) => {
    try {
      const result = await prisma.postalGeoData.createMany({
        data: batch,
      });
      const insertedCount = result.count || batch.length; // Get inserted count, fallback to batch length
      totalInserted += insertedCount; // Increment the total inserted count
    } catch (error) {
      console.error("Error inserting batch:", error);
    }
  };

  // Process data in batches
  for (let i = 0; i < jsonData.length; i += batchSize) {
    const batch = jsonData.slice(i, i + batchSize);
    await processBatch(batch);
    batchCount++;
    // Log every `logFrequency` batches
    if (batchCount % logFrequency === 0) {
      console.log(`\tInserted ${batchCount * batchSize} records so far...`);
    }
  }

  // Report total inserted records
  console.log(`Seeded ${totalInserted} postalGeoData records in total.\n`);
  await prisma.$disconnect();
}

/**
 * Seeds foundational tables with initial data.
 * Uses the following methods to populate tables in production environment:
 * - seedPathways
 * - seedTechnologyAreas
 * - seedIndustrySectors
 * - seedSubcategories
 * - seedSkills
 * - seedPostalGeoData
 * - seedPrograms
 * - seedEduProviders
 * - seedCompanies
 *
 * @return {Promise<void>} A promise that resolves when all tables are successfully seeded.
 */
async function seedFoundationalTables() {
  await seedPartnerPathways(); // TODO: add pathway subcategories (i.e. Software Dev consists of Web Dev, Mobile Dev etc.)
  await seedTechnologyAreas();
  await seedIndustrySectors();
  await seedSubcategories();
  await seedSkills(); // TODO: associate skills with a pathway
  await seedPostalGeoData("../data/postal_geo_data.json"); // use in production
  await seedGeneralPrograms();
  await seedPartnerPrograms();
  await seedGeneralEdProviders(); // TODO: get updated list of training provider partners to use in production
  await seedPartnerEdProvidersAndPrograms();
  await seedPartnerCompanies(); // TODO: add additional partner companies
}

/**
 * Seeds mock data for jobseekers including jobseekers, private data, skills, education, work experiences,
 * certificates, project experiences, and project skills.
 **/
async function seedMockJobseekerData() {
  // TODO: add self-assessments and associate with a pathway
  // TODO: add jobseeker self-assessment and info session questions
  await seedJobSeekers();
  await seedJobSeekersPrivateData();
  await seedJobSeekerSkills();
  await seedJobSeekersEducation();
  await seedJobseekerWorkExperiences();
  await seedJobSeekerCertificates();
  await seedProjectExperiences();
  await seedProjectSkills();
}

/**
 * Seeds mock employer data into the database by using helper functions to populate employers, company addresses,
 * company testimonials, company social links, and job postings.
 *
 * @return {Promise<void>} A Promise that resolves when all mock employer data has been successfully seeded.
 */
async function seedMockEmployerData() {
  await seedMockCompanies(); // TODO: get a list of pre-approved companies to use in production
  await seedEmployers();
  await seedCompanyAddresses();
  // await seedCompanyTestimonials();
  // await seedCompanySocialLinks();
  await seedJobPostings();
}

/////////////////////////////////////////////////

/////////////////////////////////////////////////
//////////////   career prep  ///////////////////
/////////////////////////////////////////////////

async function seedCareerPrepStudents() {
  console.log("Seeding Career Prep Students");

  const potentialStudents = await prisma.jobseekers.findMany({
    where: {
      careerPrepTrackRecommendation: {
        not: null,
      },
    },
  });

  for (const ps of potentialStudents) {
    // Only create an assessment for approximately 75% of the students
    if (faker.datatype.boolean({ probability: 0.75 })) {
      await prisma.careerPrepAssessment.create({
        data: {
          assessmentDate: new Date(),
          pronouns: faker.helpers.arrayElement([
            "he/him",
            "they/them",
            "she/her",
            "she/her/they",
          ]),
          experienceWithApplying: faker.datatype.boolean({ probability: 0.5 }),
          experienceWithInterview: faker.datatype.boolean({ probability: 0.5 }),
          prevWorkExperience: faker.datatype.boolean({ probability: 0.75 }),
          expectedEduCompletion:
            faker.helpers.arrayElement(TimeUntilCompletion),
          Jobseeker: {
            connect: {
              jobseeker_id: ps.jobseeker_id,
            },
          },
        },
      });
    }
  }

  console.log(
    `Finished seeding approximately 75% of ${potentialStudents.length} Career Prep students.\n`,
  );
}

async function seedCaseMgmt() {
  console.log("Seeding Case Management Records");

  const careerPrepStudents = await prisma.careerPrepAssessment.findMany({
    include: {
      Jobseeker: true,
    },
  });
  const caseManagers = await prisma.user.findMany({
    where: {
      role: "CASE_MANAGER",
    },
    take: 1,
  });
  for (const s of careerPrepStudents) {
    if (faker.datatype.boolean({ probability: 0.75 })) {
      await prisma.caseMgmt.create({
        data: {
          prepEnrollmentStatus: faker.helpers.arrayElement(CareerPrepStatus),
          prepStartDate: faker.date.recent({
            days: 5,
            refDate: Date.now().toString(),
          }),
          prepExpectedEndDate: faker.date.soon({
            days: 20,
            refDate: new Date(
              new Date().setMonth(new Date().getMonth() + 3),
            ).toISOString(),
          }),
          prepActualEndDate: faker.date.soon({
            days: 5,
            refDate: new Date(
              new Date().setMonth(new Date().getMonth() + 3),
            ).toISOString(),
          }),
          PrepAssessment: {
            connect: {
              jobseekerId: s.jobseekerId,
            },
          },
          CaseManager: {
            connect: {
              id: faker.helpers.arrayElement(caseManagers).id,
            },
          },
        },
      });
    }
  }
  console.log(
    `Finished seeding approximately 75% of ${careerPrepStudents.length} Career Prep students for Case Management.\n`,
  );
}

async function seedCaseMgmtNotes() {
  console.log("Seeding Case Management Notes");

  const managedPrepStudents = await prisma.caseMgmt.findMany();

  for (const mps of managedPrepStudents) {
    const notes = Array.from({ length: 3 }).map(() => ({
      date: faker.datatype.boolean({ probability: 0.9 })
        ? faker.date.soon({ days: 14, refDate: Date.now() })
        : null,
      noteType: faker.helpers.arrayElement(["General", "Meeting", "Follow-up"]),
      noteContent: faker.datatype.boolean()
        ? faker.lorem.sentences(3, "\n")
        : faker.lorem.paragraphs({ min: 1, max: 3 }, "\r\n"),
      PrepAssessment: {
        connect: {
          jobseekerId: mps.jobseekerId,
        },
      },
      Author: {
        connect: {
          id: mps.managerId,
        },
      },
    }));

    await Promise.all(
      notes.map((note) => prisma.caseMgmtNotes.create({ data: note })),
    );
  }

  console.log("Finished seeding Case management notes.\n");
}

/////////////////////////////////////////////////

/**
 * Asynchronously runs seeding process for database with fundamental data and mock user information.
 *
 * @return {Promise<void>} A Promise that resolves when the seeding process is completed.
 */
async function main() {
  console.log(`Start seeding ...\n`);
  await seedFoundationalTables();
  if (process.env.NODE_ENV === "production") {
    console.log("Skipping seeding of mock data...");
    console.log("Finished seeding foundational tables.\n");
    return;
  }

  await SeedMockEdProvidersAddresses();
  await seedMockUsers(125);
  await seedMockJobseekerData();
  await seedMockEmployerData();
  await seedCareerPrepStudents();
  await seedCaseMgmt();
  await seedCaseMgmtNotes();
  console.log("Finished seeding.\n");
}

main()
  .catch((e) => {
    console.error(e);
    process.exit(1);
  })
  .finally(async () => {
    await prisma.$disconnect();
  });
