# Ground Truth Labeling Examples — Week 4 Eval Harness

> **Purpose:** 5 hand-labeled examples for the team to use as a template when building the full 20–30 record dataset at `agents/eval/extraction_ground_truth.json`. Each pair should label 2–3 postings using the ground truth labeling tool.
>
> **Format decision:** JSON file, not Postgres. The eval harness loads ground truth from a fixture file and compares it against extraction output. The `extracted_intelligence` table stores agent output — ground truth stays in a separate JSON file so it's version-controlled and human-reviewable.

---

## Dataset Composition (5 of 20–30 target)

| # | Role | GenAI Skills? | Traditional? | Ambiguous Items |
|---|------|:------------:|:------------:|-----------------|
| 1 | Senior Data Engineer | No | Yes | Python, SQL, Excel |
| 2 | ML/GenAI Platform Engineer | Yes | No | Python, Kubernetes |
| 3 | Business Analyst | No | Yes | Excel, leadership, Python |
| 4 | DevOps Engineer | No | Yes | Python, leadership |
| 5 | AI Solutions Architect | Yes | No | Python, leadership |

**Checks:**
- GenAI roles: 2/5 (40%) — within ~30–40% target
- Traditional roles (no AI/ML): 3/5 — on track for 5–8 in full dataset
- Ambiguous items: Excel (3×), leadership (3×), Python (5×) — covered

---

## JSON Records

Paste these into `agents/eval/extraction_ground_truth.json` as the starting array:

```json
[
  {
    "ground_truth_id": "gt-001",
    "title": "Senior Data Engineer",
    "company": "Raytheon Technologies",
    "city": "El Paso",
    "state": "Texas",
    "description": "We are seeking a Senior Data Engineer to design and maintain scalable data pipelines. You will work with cross-functional teams to build ETL processes, optimize SQL queries, and ensure data quality across our analytics platform. The ideal candidate has experience with cloud data warehouses, strong Python skills, and can communicate technical concepts to non-technical stakeholders.",
    "requirements": "5+ years of data engineering experience. Proficiency in Python and SQL. Experience with Apache Spark or Databricks. Familiarity with AWS services (S3, Redshift, Glue). Strong understanding of data modeling and warehousing concepts. Experience with CI/CD pipelines. Advanced Excel skills for ad-hoc analysis. Bachelor's degree in Computer Science or related field.",
    "responsibilities": "Design and implement scalable data pipelines using Python and Apache Spark. Optimize SQL queries and database performance. Collaborate with data scientists and analysts to deliver clean datasets. Maintain documentation for data architecture decisions. Mentor junior engineers on best practices.",
    "skills": [
      {
        "label": "Python",
        "type": "Technical",
        "confidence": 1.0,
        "required_flag": true,
        "esco_uri": "http://data.europa.eu/esco/skill/bab65147-22f1-4493-86e3-4e8e8464e954",
        "is_genai_extension": false,
        "source_span": {
          "text": "Python",
          "field_source": "requirements",
          "start_char": 0,
          "end_char": 6
        },
        "labeler_note": "Ambiguous — could be Tool. Classified as Technical because listing treats it as a core competency, not a specific tool instance."
      },
      {
        "label": "SQL",
        "type": "Technical",
        "confidence": 1.0,
        "required_flag": true,
        "esco_uri": "http://data.europa.eu/esco/skill/c2e3a25b-5c53-4519-a8a6-e67b72599748",
        "is_genai_extension": false,
        "source_span": {
          "text": "SQL",
          "field_source": "requirements",
          "start_char": 0,
          "end_char": 3
        },
        "labeler_note": null
      },
      {
        "label": "Data Modeling",
        "type": "Domain",
        "confidence": 1.0,
        "required_flag": true,
        "esco_uri": null,
        "is_genai_extension": false,
        "source_span": {
          "text": "Data Modeling",
          "field_source": "requirements",
          "start_char": 0,
          "end_char": 13
        },
        "labeler_note": "No direct ESCO match — expect step 6 (raw_skill). Enrichment phase may resolve."
      },
      {
        "label": "Data Warehousing",
        "type": "Domain",
        "confidence": 1.0,
        "required_flag": true,
        "esco_uri": null,
        "is_genai_extension": false,
        "source_span": {
          "text": "Data Warehousing",
          "field_source": "requirements",
          "start_char": 0,
          "end_char": 16
        },
        "labeler_note": null
      },
      {
        "label": "ETL",
        "type": "Technical",
        "confidence": 1.0,
        "required_flag": true,
        "esco_uri": null,
        "is_genai_extension": false,
        "source_span": {
          "text": "ETL",
          "field_source": "requirements",
          "start_char": 0,
          "end_char": 3
        },
        "labeler_note": "Acronym — agent should expand or match as-is."
      },
      {
        "label": "Communication",
        "type": "Soft",
        "confidence": 1.0,
        "required_flag": false,
        "esco_uri": null,
        "is_genai_extension": false,
        "source_span": {
          "text": "Communication",
          "field_source": "requirements",
          "start_char": 0,
          "end_char": 13
        },
        "labeler_note": "Inferred from 'communicate technical concepts to non-technical stakeholders'. Not listed as a requirement."
      },
      {
        "label": "Mentoring",
        "type": "Soft",
        "confidence": 1.0,
        "required_flag": false,
        "esco_uri": null,
        "is_genai_extension": false,
        "source_span": {
          "text": "Mentoring",
          "field_source": "requirements",
          "start_char": 0,
          "end_char": 9
        },
        "labeler_note": "From 'Mentor junior engineers'. Soft skill, not explicit requirement."
      },
      {
        "label": "Excel",
        "type": "Tool",
        "confidence": 1.0,
        "required_flag": true,
        "esco_uri": null,
        "is_genai_extension": false,
        "source_span": {
          "text": "Excel",
          "field_source": "requirements",
          "start_char": 0,
          "end_char": 5
        },
        "labeler_note": "Ambiguous — some classify as Technical. Classified as Tool because it's a specific software product (Microsoft Excel)."
      }
    ],
    "tools": [
      {
        "tool_name": "Apache Spark",
        "category": "framework",
        "confidence": 1.0,
        "source_span": {
          "text": "Apache Spark",
          "field_source": "requirements",
          "start_char": 0,
          "end_char": 12
        },
        "is_genai_tool": false
      },
      {
        "tool_name": "Databricks",
        "category": "platform",
        "confidence": 1.0,
        "source_span": {
          "text": "Databricks",
          "field_source": "requirements",
          "start_char": 0,
          "end_char": 10
        },
        "is_genai_tool": false
      },
      {
        "tool_name": "AWS S3",
        "category": "platform",
        "confidence": 1.0,
        "source_span": {
          "text": "AWS S3",
          "field_source": "requirements",
          "start_char": 0,
          "end_char": 6
        },
        "is_genai_tool": false
      },
      {
        "tool_name": "AWS Redshift",
        "category": "database",
        "confidence": 1.0,
        "source_span": {
          "text": "AWS Redshift",
          "field_source": "requirements",
          "start_char": 0,
          "end_char": 12
        },
        "is_genai_tool": false
      },
      {
        "tool_name": "AWS Glue",
        "category": "platform",
        "confidence": 1.0,
        "source_span": {
          "text": "AWS Glue",
          "field_source": "requirements",
          "start_char": 0,
          "end_char": 8
        },
        "is_genai_tool": false
      },
      {
        "tool_name": "Excel",
        "category": "other",
        "confidence": 1.0,
        "source_span": {
          "text": "Excel",
          "field_source": "requirements",
          "start_char": 0,
          "end_char": 5
        },
        "is_genai_tool": false
      }
    ]
  },
  {
    "ground_truth_id": "gt-002",
    "title": "ML/GenAI Platform Engineer",
    "company": "Booz Allen Hamilton",
    "city": "El Paso",
    "state": "Texas",
    "description": "Join our AI Center of Excellence to build and maintain the infrastructure powering generative AI applications for federal clients. You will design retrieval-augmented generation (RAG) pipelines, manage vector databases, and ensure prompt engineering best practices across teams. This role bridges ML ops with the emerging GenAI stack.",
    "requirements": "3+ years experience in ML engineering or ML ops. Hands-on experience with LLM APIs (OpenAI, Anthropic, or Azure OpenAI). Proficiency in Python. Experience with vector databases (Pinecone, Weaviate, or pgvector). Understanding of RAG architectures and prompt engineering patterns. Kubernetes and Docker for model serving. Active Secret clearance or ability to obtain.",
    "responsibilities": "Build and maintain RAG pipelines for document Q&A systems. Manage Pinecone vector database clusters and embedding pipelines. Develop prompt templates and evaluate LLM output quality. Containerize and deploy ML models using Docker and Kubernetes. Implement AI output validation checks and guardrails. Collaborate with data scientists on foundation model selection for new use cases.",
    "skills": [
      {
        "label": "Prompt Engineering",
        "type": "Technical",
        "confidence": 1.0,
        "required_flag": true,
        "esco_uri": "http://data.europa.eu/esco/skill/11111111-digital-content-creation",
        "is_genai_extension": true,
        "source_span": {
          "text": "Prompt Engineering",
          "field_source": "requirements",
          "start_char": 0,
          "end_char": 18
        },
        "labeler_note": "GenAI Extension Layer skill #1 → maps to ESCO 'Digital content creation' parent cluster."
      },
      {
        "label": "RAG (Retrieval-Augmented Generation)",
        "type": "Technical",
        "confidence": 1.0,
        "required_flag": true,
        "esco_uri": "http://data.europa.eu/esco/skill/22222222-information-retrieval",
        "is_genai_extension": true,
        "source_span": {
          "text": "RAG (Retrieval-Augmented Generation)",
          "field_source": "requirements",
          "start_char": 0,
          "end_char": 36
        },
        "labeler_note": "GenAI Extension Layer skill #2 → maps to ESCO 'Information retrieval' parent cluster."
      },
      {
        "label": "AI Output Validation",
        "type": "Technical",
        "confidence": 1.0,
        "required_flag": false,
        "esco_uri": "http://data.europa.eu/esco/skill/66666666-quality-assurance",
        "is_genai_extension": true,
        "source_span": {
          "text": "AI Output Validation",
          "field_source": "requirements",
          "start_char": 0,
          "end_char": 20
        },
        "labeler_note": "GenAI Extension Layer skill #6 → maps to ESCO 'Quality assurance'. Inferred from 'AI output validation checks and guardrails' in responsibilities."
      },
      {
        "label": "Foundation Model Selection",
        "type": "Technical",
        "confidence": 1.0,
        "required_flag": false,
        "esco_uri": "http://data.europa.eu/esco/skill/88888888-technology-evaluation",
        "is_genai_extension": true,
        "source_span": {
          "text": "Foundation Model Selection",
          "field_source": "requirements",
          "start_char": 0,
          "end_char": 26
        },
        "labeler_note": "GenAI Extension Layer skill #8 → maps to ESCO 'Technology evaluation'. From 'foundation model selection for new use cases'."
      },
      {
        "label": "Vector Database Management",
        "type": "Technical",
        "confidence": 1.0,
        "required_flag": true,
        "esco_uri": "http://data.europa.eu/esco/skill/99999999-database-management",
        "is_genai_extension": true,
        "source_span": {
          "text": "Vector Database Management",
          "field_source": "requirements",
          "start_char": 0,
          "end_char": 26
        },
        "labeler_note": "GenAI Extension Layer skill #9 → maps to ESCO 'Database management'."
      },
      {
        "label": "Python",
        "type": "Technical",
        "confidence": 1.0,
        "required_flag": true,
        "esco_uri": "http://data.europa.eu/esco/skill/bab65147-22f1-4493-86e3-4e8e8464e954",
        "is_genai_extension": false,
        "source_span": {
          "text": "Python",
          "field_source": "requirements",
          "start_char": 0,
          "end_char": 6
        },
        "labeler_note": "Ambiguous — listed as core competency, classified Technical."
      },
      {
        "label": "ML Ops",
        "type": "Domain",
        "confidence": 1.0,
        "required_flag": true,
        "esco_uri": null,
        "is_genai_extension": false,
        "source_span": {
          "text": "ML Ops",
          "field_source": "requirements",
          "start_char": 0,
          "end_char": 6
        },
        "labeler_note": "Compound domain skill — may resolve via embedding similarity (step 4) or fall to step 6."
      },
      {
        "label": "Containerization",
        "type": "Technical",
        "confidence": 1.0,
        "required_flag": true,
        "esco_uri": null,
        "is_genai_extension": false,
        "source_span": {
          "text": "Containerization",
          "field_source": "requirements",
          "start_char": 0,
          "end_char": 16
        },
        "labeler_note": "Inferred from Docker/Kubernetes requirement. Agent may extract 'Docker' as Tool and miss this as a skill."
      }
    ],
    "tools": [
      {
        "tool_name": "Docker",
        "category": "devops",
        "confidence": 1.0,
        "source_span": {
          "text": "Docker",
          "field_source": "requirements",
          "start_char": 0,
          "end_char": 6
        },
        "is_genai_tool": false
      },
      {
        "tool_name": "Kubernetes",
        "category": "devops",
        "confidence": 1.0,
        "source_span": {
          "text": "Kubernetes",
          "field_source": "requirements",
          "start_char": 0,
          "end_char": 10
        },
        "is_genai_tool": false
      },
      {
        "tool_name": "Pinecone",
        "category": "database",
        "confidence": 1.0,
        "source_span": {
          "text": "Pinecone",
          "field_source": "requirements",
          "start_char": 0,
          "end_char": 8
        },
        "is_genai_tool": true
      },
      {
        "tool_name": "Weaviate",
        "category": "database",
        "confidence": 1.0,
        "source_span": {
          "text": "Weaviate",
          "field_source": "requirements",
          "start_char": 0,
          "end_char": 8
        },
        "is_genai_tool": true
      },
      {
        "tool_name": "pgvector",
        "category": "database",
        "confidence": 1.0,
        "source_span": {
          "text": "pgvector",
          "field_source": "requirements",
          "start_char": 0,
          "end_char": 8
        },
        "is_genai_tool": true
      },
      {
        "tool_name": "OpenAI API",
        "category": "ai_tool",
        "confidence": 1.0,
        "source_span": {
          "text": "OpenAI API",
          "field_source": "requirements",
          "start_char": 0,
          "end_char": 10
        },
        "is_genai_tool": true
      },
      {
        "tool_name": "Anthropic API",
        "category": "ai_tool",
        "confidence": 1.0,
        "source_span": {
          "text": "Anthropic API",
          "field_source": "requirements",
          "start_char": 0,
          "end_char": 13
        },
        "is_genai_tool": true
      },
      {
        "tool_name": "Azure OpenAI",
        "category": "ai_tool",
        "confidence": 1.0,
        "source_span": {
          "text": "Azure OpenAI",
          "field_source": "requirements",
          "start_char": 0,
          "end_char": 12
        },
        "is_genai_tool": true
      }
    ]
  },
  {
    "ground_truth_id": "gt-003",
    "title": "Business Analyst",
    "company": "El Paso Electric",
    "city": "El Paso",
    "state": "Texas",
    "description": "El Paso Electric is seeking a Business Analyst to support our IT modernization initiative. You will gather requirements from business stakeholders, translate them into technical specifications, and work with development teams to deliver solutions. Strong analytical thinking, Excel proficiency, and the ability to lead cross-functional meetings are essential.",
    "requirements": "3+ years as a Business Analyst or similar role. Advanced Excel skills including pivot tables, VLOOKUP, and macros. Experience with SQL for data extraction and reporting. Familiarity with Jira or Azure DevOps for project tracking. Strong written and verbal communication skills. Experience creating process flow diagrams using Visio or Lucidchart. Python scripting a plus but not required. PMP or CBAP certification preferred.",
    "responsibilities": "Gather and document business requirements through stakeholder interviews. Create detailed functional specifications and user stories in Jira. Build Excel-based dashboards and reports for executive leadership. Write SQL queries to extract data for ad-hoc analysis. Lead weekly cross-functional status meetings. Maintain requirements traceability matrix.",
    "skills": [
      {
        "label": "Requirements Gathering",
        "type": "Domain",
        "confidence": 1.0,
        "required_flag": true,
        "esco_uri": null,
        "is_genai_extension": false,
        "source_span": {
          "text": "Requirements Gathering",
          "field_source": "requirements",
          "start_char": 0,
          "end_char": 22
        },
        "labeler_note": null
      },
      {
        "label": "SQL",
        "type": "Technical",
        "confidence": 1.0,
        "required_flag": true,
        "esco_uri": "http://data.europa.eu/esco/skill/c2e3a25b-5c53-4519-a8a6-e67b72599748",
        "is_genai_extension": false,
        "source_span": {
          "text": "SQL",
          "field_source": "requirements",
          "start_char": 0,
          "end_char": 3
        },
        "labeler_note": null
      },
      {
        "label": "Excel",
        "type": "Tool",
        "confidence": 1.0,
        "required_flag": true,
        "esco_uri": null,
        "is_genai_extension": false,
        "source_span": {
          "text": "Excel",
          "field_source": "requirements",
          "start_char": 0,
          "end_char": 5
        },
        "labeler_note": "Ambiguous — classified as Tool (specific product). Heavy usage here: pivot tables, VLOOKUP, macros, dashboards."
      },
      {
        "label": "Leadership",
        "type": "Soft",
        "confidence": 1.0,
        "required_flag": false,
        "esco_uri": null,
        "is_genai_extension": false,
        "source_span": {
          "text": "Leadership",
          "field_source": "requirements",
          "start_char": 0,
          "end_char": 10
        },
        "labeler_note": "Ambiguous — inferred from 'Lead weekly cross-functional status meetings'. Not an explicit requirement."
      },
      {
        "label": "Communication",
        "type": "Soft",
        "confidence": 1.0,
        "required_flag": true,
        "esco_uri": null,
        "is_genai_extension": false,
        "source_span": {
          "text": "Communication",
          "field_source": "requirements",
          "start_char": 0,
          "end_char": 13
        },
        "labeler_note": "Explicitly listed: 'Strong written and verbal communication skills'."
      },
      {
        "label": "Python",
        "type": "Technical",
        "confidence": 1.0,
        "required_flag": false,
        "esco_uri": "http://data.europa.eu/esco/skill/bab65147-22f1-4493-86e3-4e8e8464e954",
        "is_genai_extension": false,
        "source_span": {
          "text": "Python",
          "field_source": "requirements",
          "start_char": 0,
          "end_char": 6
        },
        "labeler_note": "Ambiguous — 'Python scripting a plus but not required'. Clearly optional (required_flag=false)."
      },
      {
        "label": "Process Modeling",
        "type": "Domain",
        "confidence": 1.0,
        "required_flag": true,
        "esco_uri": null,
        "is_genai_extension": false,
        "source_span": {
          "text": "Process Modeling",
          "field_source": "requirements",
          "start_char": 0,
          "end_char": 16
        },
        "labeler_note": "Inferred from 'process flow diagrams'. Agent may extract as 'Business Process Modeling' — both acceptable."
      }
    ],
    "tools": [
      {
        "tool_name": "Excel",
        "category": "other",
        "confidence": 1.0,
        "source_span": {
          "text": "Excel",
          "field_source": "requirements",
          "start_char": 0,
          "end_char": 5
        },
        "is_genai_tool": false
      },
      {
        "tool_name": "Jira",
        "category": "platform",
        "confidence": 1.0,
        "source_span": {
          "text": "Jira",
          "field_source": "requirements",
          "start_char": 0,
          "end_char": 4
        },
        "is_genai_tool": false
      },
      {
        "tool_name": "Azure DevOps",
        "category": "platform",
        "confidence": 1.0,
        "source_span": {
          "text": "Azure DevOps",
          "field_source": "requirements",
          "start_char": 0,
          "end_char": 12
        },
        "is_genai_tool": false
      },
      {
        "tool_name": "Visio",
        "category": "other",
        "confidence": 1.0,
        "source_span": {
          "text": "Visio",
          "field_source": "requirements",
          "start_char": 0,
          "end_char": 5
        },
        "is_genai_tool": false
      },
      {
        "tool_name": "Lucidchart",
        "category": "other",
        "confidence": 1.0,
        "source_span": {
          "text": "Lucidchart",
          "field_source": "requirements",
          "start_char": 0,
          "end_char": 10
        },
        "is_genai_tool": false
      }
    ],
    "certifications": [
      {
        "label": "PMP",
        "required_flag": false
      },
      {
        "label": "CBAP",
        "required_flag": false
      }
    ]
  },
  {
    "ground_truth_id": "gt-004",
    "title": "DevOps Engineer",
    "company": "SAIC",
    "city": "El Paso",
    "state": "Texas",
    "description": "SAIC is hiring a DevOps Engineer to support infrastructure automation for defense programs at Fort Bliss. You will build and maintain CI/CD pipelines, manage cloud infrastructure using Infrastructure as Code, and ensure system reliability through monitoring and incident response. This is a hands-on role requiring strong Linux administration and scripting skills.",
    "requirements": "4+ years of DevOps or SRE experience. Strong Linux systems administration. Proficiency in Python or Bash scripting for automation. Experience with Terraform or CloudFormation for IaC. Hands-on experience with Jenkins or GitLab CI/CD. Container orchestration with Kubernetes and Docker. Monitoring and alerting with Prometheus and Grafana. AWS or Azure cloud certifications preferred. Active Secret clearance required.",
    "responsibilities": "Design and maintain CI/CD pipelines using Jenkins and GitLab CI. Automate infrastructure provisioning with Terraform across AWS environments. Manage Kubernetes clusters for microservice deployments. Implement monitoring dashboards using Prometheus and Grafana. Respond to production incidents and conduct post-mortems. Mentor team members on DevOps best practices and tooling.",
    "skills": [
      {
        "label": "Linux Administration",
        "type": "Technical",
        "confidence": 1.0,
        "required_flag": true,
        "esco_uri": null,
        "is_genai_extension": false,
        "source_span": {
          "text": "Linux Administration",
          "field_source": "requirements",
          "start_char": 0,
          "end_char": 20
        },
        "labeler_note": null
      },
      {
        "label": "Python",
        "type": "Technical",
        "confidence": 1.0,
        "required_flag": true,
        "esco_uri": "http://data.europa.eu/esco/skill/bab65147-22f1-4493-86e3-4e8e8464e954",
        "is_genai_extension": false,
        "source_span": {
          "text": "Python",
          "field_source": "requirements",
          "start_char": 0,
          "end_char": 6
        },
        "labeler_note": "Ambiguous — listed alongside Bash as 'scripting' tools. Classified Technical because it's a core competency here."
      },
      {
        "label": "Infrastructure as Code",
        "type": "Domain",
        "confidence": 1.0,
        "required_flag": true,
        "esco_uri": null,
        "is_genai_extension": false,
        "source_span": {
          "text": "Infrastructure as Code",
          "field_source": "requirements",
          "start_char": 0,
          "end_char": 22
        },
        "labeler_note": "Domain practice, not a specific tool. Terraform is the tool."
      },
      {
        "label": "CI/CD",
        "type": "Domain",
        "confidence": 1.0,
        "required_flag": true,
        "esco_uri": null,
        "is_genai_extension": false,
        "source_span": {
          "text": "CI/CD",
          "field_source": "requirements",
          "start_char": 0,
          "end_char": 5
        },
        "labeler_note": "Domain practice — Jenkins/GitLab CI are the tools."
      },
      {
        "label": "Incident Response",
        "type": "Domain",
        "confidence": 1.0,
        "required_flag": true,
        "esco_uri": null,
        "is_genai_extension": false,
        "source_span": {
          "text": "Incident Response",
          "field_source": "requirements",
          "start_char": 0,
          "end_char": 17
        },
        "labeler_note": "From 'Respond to production incidents and conduct post-mortems'."
      },
      {
        "label": "Mentoring",
        "type": "Soft",
        "confidence": 1.0,
        "required_flag": false,
        "esco_uri": null,
        "is_genai_extension": false,
        "source_span": {
          "text": "Mentoring",
          "field_source": "requirements",
          "start_char": 0,
          "end_char": 9
        },
        "labeler_note": "From 'Mentor team members'. Soft skill, not explicit requirement."
      },
      {
        "label": "Leadership",
        "type": "Soft",
        "confidence": 1.0,
        "required_flag": false,
        "esco_uri": null,
        "is_genai_extension": false,
        "source_span": {
          "text": "Leadership",
          "field_source": "requirements",
          "start_char": 0,
          "end_char": 10
        },
        "labeler_note": "Ambiguous — inferred from mentoring responsibility. Debatable whether this counts separately from Mentoring."
      }
    ],
    "tools": [
      {
        "tool_name": "Jenkins",
        "category": "devops",
        "confidence": 1.0,
        "source_span": {
          "text": "Jenkins",
          "field_source": "requirements",
          "start_char": 0,
          "end_char": 7
        },
        "is_genai_tool": false
      },
      {
        "tool_name": "GitLab CI",
        "category": "devops",
        "confidence": 1.0,
        "source_span": {
          "text": "GitLab CI",
          "field_source": "requirements",
          "start_char": 0,
          "end_char": 9
        },
        "is_genai_tool": false
      },
      {
        "tool_name": "Terraform",
        "category": "devops",
        "confidence": 1.0,
        "source_span": {
          "text": "Terraform",
          "field_source": "requirements",
          "start_char": 0,
          "end_char": 9
        },
        "is_genai_tool": false
      },
      {
        "tool_name": "CloudFormation",
        "category": "devops",
        "confidence": 1.0,
        "source_span": {
          "text": "CloudFormation",
          "field_source": "requirements",
          "start_char": 0,
          "end_char": 14
        },
        "is_genai_tool": false
      },
      {
        "tool_name": "Kubernetes",
        "category": "devops",
        "confidence": 1.0,
        "source_span": {
          "text": "Kubernetes",
          "field_source": "requirements",
          "start_char": 0,
          "end_char": 10
        },
        "is_genai_tool": false
      },
      {
        "tool_name": "Docker",
        "category": "devops",
        "confidence": 1.0,
        "source_span": {
          "text": "Docker",
          "field_source": "requirements",
          "start_char": 0,
          "end_char": 6
        },
        "is_genai_tool": false
      },
      {
        "tool_name": "Prometheus",
        "category": "devops",
        "confidence": 1.0,
        "source_span": {
          "text": "Prometheus",
          "field_source": "requirements",
          "start_char": 0,
          "end_char": 10
        },
        "is_genai_tool": false
      },
      {
        "tool_name": "Grafana",
        "category": "devops",
        "confidence": 1.0,
        "source_span": {
          "text": "Grafana",
          "field_source": "requirements",
          "start_char": 0,
          "end_char": 7
        },
        "is_genai_tool": false
      }
    ]
  },
  {
    "ground_truth_id": "gt-005",
    "title": "AI Solutions Architect",
    "company": "Accenture Federal Services",
    "city": "El Paso",
    "state": "Texas",
    "description": "We are looking for an AI Solutions Architect to lead the design of intelligent automation solutions for federal agencies. You will evaluate foundation models, design agentic systems that orchestrate multiple AI capabilities, and ensure AI governance standards are met. This role requires both deep technical expertise and the ability to communicate complex AI concepts to senior government stakeholders.",
    "requirements": "7+ years in software architecture, with 2+ years focused on AI/ML systems. Experience designing agentic AI systems or multi-agent orchestration pipelines. Hands-on experience with LLM APIs and embedding models. Understanding of AI governance frameworks and responsible AI principles. Proficiency in Python. Experience with Azure AI services. Strong presentation and leadership skills. TOGAF or AWS Solutions Architect certification preferred.",
    "responsibilities": "Lead architecture design sessions for AI-powered solutions. Evaluate and select foundation models based on cost, quality, and latency trade-offs. Design multi-agent orchestration patterns for complex workflows. Establish AI governance guardrails and validation frameworks. Present technical solutions to C-suite and senior government officials. Mentor engineering teams on AI integration best practices.",
    "skills": [
      {
        "label": "Agentic Systems Design",
        "type": "Technical",
        "confidence": 1.0,
        "required_flag": true,
        "esco_uri": "http://data.europa.eu/esco/skill/55555555-software-architecture",
        "is_genai_extension": true,
        "source_span": {
          "text": "Agentic Systems Design",
          "field_source": "requirements",
          "start_char": 0,
          "end_char": 22
        },
        "labeler_note": "GenAI Extension Layer skill #5 → maps to ESCO 'Software architecture'. From 'agentic AI systems or multi-agent orchestration'."
      },
      {
        "label": "Foundation Model Selection",
        "type": "Technical",
        "confidence": 1.0,
        "required_flag": true,
        "esco_uri": "http://data.europa.eu/esco/skill/88888888-technology-evaluation",
        "is_genai_extension": true,
        "source_span": {
          "text": "Foundation Model Selection",
          "field_source": "requirements",
          "start_char": 0,
          "end_char": 26
        },
        "labeler_note": "GenAI Extension Layer skill #8 → maps to ESCO 'Technology evaluation'."
      },
      {
        "label": "AI Governance",
        "type": "Domain",
        "confidence": 1.0,
        "required_flag": true,
        "esco_uri": "http://data.europa.eu/esco/skill/44444444-digital-ethics",
        "is_genai_extension": true,
        "source_span": {
          "text": "AI Governance",
          "field_source": "requirements",
          "start_char": 0,
          "end_char": 13
        },
        "labeler_note": "GenAI Extension Layer skill #4 → maps to ESCO 'Digital ethics'."
      },
      {
        "label": "AI Output Validation",
        "type": "Technical",
        "confidence": 1.0,
        "required_flag": false,
        "esco_uri": "http://data.europa.eu/esco/skill/66666666-quality-assurance",
        "is_genai_extension": true,
        "source_span": {
          "text": "AI Output Validation",
          "field_source": "requirements",
          "start_char": 0,
          "end_char": 20
        },
        "labeler_note": "GenAI Extension Layer skill #6. Inferred from 'validation frameworks' in responsibilities."
      },
      {
        "label": "Software Architecture",
        "type": "Domain",
        "confidence": 1.0,
        "required_flag": true,
        "esco_uri": null,
        "is_genai_extension": false,
        "source_span": {
          "text": "Software Architecture",
          "field_source": "requirements",
          "start_char": 0,
          "end_char": 21
        },
        "labeler_note": "Broader than agentic systems — 7+ years of general architecture experience required."
      },
      {
        "label": "Python",
        "type": "Technical",
        "confidence": 1.0,
        "required_flag": true,
        "esco_uri": "http://data.europa.eu/esco/skill/bab65147-22f1-4493-86e3-4e8e8464e954",
        "is_genai_extension": false,
        "source_span": {
          "text": "Python",
          "field_source": "requirements",
          "start_char": 0,
          "end_char": 6
        },
        "labeler_note": "Ambiguous — classified Technical."
      },
      {
        "label": "Communication",
        "type": "Soft",
        "confidence": 1.0,
        "required_flag": true,
        "esco_uri": null,
        "is_genai_extension": false,
        "source_span": {
          "text": "Communication",
          "field_source": "requirements",
          "start_char": 0,
          "end_char": 13
        },
        "labeler_note": "From 'communicate complex AI concepts to senior government stakeholders' and 'presentation skills'."
      },
      {
        "label": "Leadership",
        "type": "Soft",
        "confidence": 1.0,
        "required_flag": true,
        "esco_uri": null,
        "is_genai_extension": false,
        "source_span": {
          "text": "Leadership",
          "field_source": "requirements",
          "start_char": 0,
          "end_char": 10
        },
        "labeler_note": "Ambiguous — explicitly listed as requirement AND inferred from 'Lead architecture design sessions', 'Mentor engineering teams'."
      }
    ],
    "tools": [
      {
        "tool_name": "Azure AI Services",
        "category": "platform",
        "confidence": 1.0,
        "source_span": {
          "text": "Azure AI Services",
          "field_source": "requirements",
          "start_char": 0,
          "end_char": 17
        },
        "is_genai_tool": true
      }
    ],
    "certifications": [
      {
        "label": "TOGAF",
        "required_flag": false
      },
      {
        "label": "AWS Solutions Architect",
        "required_flag": false
      }
    ]
  }
]
```

---

## Labeling Decisions Log

These decisions should be consistent across all 20–30 records. All pairs should follow these when labeling their assigned postings.

| Item | Decision | Rationale |
|------|----------|-----------|
| **Python** | SkillRecord `type: "Technical"` when listed as a competency; ToolRecord `tool_name: "Python"`, `category: "language"` | It's both. Skill = competency. Tool = the runtime. |
| **Excel** | SkillRecord `type: "Tool"`; ToolRecord `tool_name: "Excel"`, `category: "other"` | It's a specific product, not a technical practice. |
| **Leadership** | `type: "Soft"`, `required_flag` depends on explicit mention | Only `true` if the listing explicitly says "leadership skills required". Otherwise `false` (inferred). |
| **Communication** | `type: "Soft"` | Always Soft. Check if explicitly required or inferred from context. |
| **GenAI Extension skills** | Use exact labels from the 10-skill list | Must match exactly: "Prompt Engineering" not "prompt design". |
| **esco_uri for GenAI** | Use placeholder URIs until ESCO store is populated | Replace with real URIs from `esco_digital_skills.json` once available. |
| **source_span** | Required on every record. For hand-labeled ground truth, set `start_char: 0` and `end_char: len(text)` with `text` set to the skill/tool label. `field_source` indicates which section the skill appears in. | SpanRecord validates `end_char - start_char == len(text)` and `start_char >= 0`, so sentinel values like `-1` will fail Pydantic validation. Use `text: "Python", start_char: 0, end_char: 6` pattern for ground truth. |
| **is_genai_tool** | `true` on ToolRecord for AI/GenAI-specific tools (Pinecone, LangChain, OpenAI API, etc.) | Matches the ToolRecord schema from PR #62. |
| **Certifications** | Separate `certifications` array | Not in the SkillRecord schema as a type — track separately for eval. |

---

## Sourcing Real Postings via JSearch

These 5 examples use synthetic job descriptions. For the remaining 15–25 records, each pair should pull **real postings** using the ground truth labeling tool (JSearch integration) to ensure the ground truth reflects actual employer language, not what we think a listing looks like.

**Recommended queries** (El Paso / Borderplex region):

| Query | Why |
|-------|-----|
| `data engineer in el paso tx` | Traditional role, likely has Python/SQL/Excel ambiguity |
| `AI engineer in el paso tx` | GenAI skills, tests Extension Layer detection |
| `business analyst in el paso tx` | Traditional, Excel-heavy, soft skills |
| `devops engineer in el paso tx` | Traditional infra role, no AI/ML |
| `machine learning engineer in el paso tx` | GenAI-adjacent, tests boundary between ML and GenAI |
| `software developer in el paso tx` | General role, tests breadth of extraction |
| `cybersecurity analyst in el paso tx` | Traditional, domain-heavy, tests cert extraction |

**Workflow:**
1. Query JSearch → get raw posting JSON
2. Copy `title`, `company`, `description` fields from the API response
3. Split description into `requirements` / `responsibilities` manually (JSearch returns a single description blob)
4. Hand-label `skills`, `tools`, and `certifications`
5. Add `labeler_note` on every ambiguous call

This produces ground truth that the eval harness can compare against the agent's extraction of the **same real postings** already in the ingestion pipeline.

---

## Next Steps for All Pairs

Each pair should label 2–3 postings to collectively reach the 20–30 record target.

1. **Use these 5 records as your template** — match this exact JSON structure.
2. **Use the ground truth labeling tool** (`tools/ground-truth-labeler`) to search JSearch and label postings.
3. **Label 2–3 postings per pair** to reach the 20–30 target collectively.
4. **Maintain the ratios:** ~30–40% GenAI roles, at least 5–8 traditional, ambiguous items throughout.
5. **Save to:** `agents/eval/extraction_ground_truth.json`
6. **Replace placeholder ESCO URIs** once `esco_digital_skills.json` is populated and the taxonomy store is loaded.
7. **Add `labeler_note`** on every ambiguous call — the eval harness ignores this field but reviewers need it.
