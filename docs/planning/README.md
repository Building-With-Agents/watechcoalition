# Planning Documentation

This folder holds planning and requirements documents for major features and initiatives in the watechcoalition (Tech Talent Showcase) project.

## Contents

| Document | Description |
|----------|-------------|
| [JOB_INGESTION_AGENT_BRD.md](JOB_INGESTION_AGENT_BRD.md) | Business Requirements Document for the Job Ingestion & Intelligence Agent (LLM + ML hybrid). |
| [JOB_INGESTION_AGENT_TRD.md](JOB_INGESTION_AGENT_TRD.md) | Technical Requirements Document for the same agent; depends on BRD design decisions. |
| [JOB_INGESTION_AGENT_INTRO.md](JOB_INGESTION_AGENT_INTRO.md) | Introduction, stack guidance, and tradeoffs for the ingestion engine. |
| [JOB_INGESTION_AGENT_CURRICULUM_TOC.md](JOB_INGESTION_AGENT_CURRICULUM_TOC.md) | Curriculum table of contents with learning outcomes placeholders. |

## Usage

- **BRD** defines scope, success criteria, risks, and design decisions to resolve; it is the business basis for the TRD.
- **TRD** defines architecture, integration with the app/DB, components, and NFRs; implementation should follow approved BRD and TRD.
- **Intro** provides an environment-specific overview and stack recommendations before build-out.
- **Curriculum TOC** is a scaffold for creating learning outcomes and course materials.

New planning docs (e.g. PRD, Evaluation Plan, sprint plans) can be added here and linked from the root [README](../../README.md) or [ONBOARDING.md](../../ONBOARDING.md) as needed.
