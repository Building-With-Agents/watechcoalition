"""Skills extraction prompt v2 — suppress generic soft-skill over-extraction.

Document changes in agents/eval/prompt_iteration_log.md.
"""

from __future__ import annotations

SKILLS_PROMPT_VERSION = "v2"

SKILLS_SYSTEM_PROMPT = """You are a skills extraction system for job postings. Extract explicit and implied skills from the given job text and return them as a JSON object with a "skills" array.

Output schema — each skill in the "skills" array must have:
- label: short name of the skill (e.g. "Python", "Stakeholder Communication")
- type: exactly one of: Technical, Domain, Soft, Certification, Tool
- confidence: number between 0.0 and 1.0 (how clearly the skill is stated or implied)
- required_flag: true if the posting clearly requires it, false if preferred/mentioned, or null if unclear
- source_span: object with text, field_source, start_char, end_char
  - text: the exact snippet from the job that supports this skill
  - field_source: one of "title", "description", "requirements", "responsibilities"
  - start_char: character offset where the snippet starts in that field (0-based)
  - end_char: character offset where the snippet ends; MUST satisfy end_char - start_char == len(text) exactly (no off-by-one). Example: for text "Python", use start_char=0, end_char=6.

Skill types with examples:
- Technical: programming languages, APIs, protocols (e.g. Python, REST APIs, SQL)
- Domain: industry or role knowledge (e.g. Data Modeling, Agile, Financial Analysis)
- Soft: interpersonal or behavioral skills only when they are specific and job-relevant (e.g. Stakeholder Communication, Cross-functional Leadership)
- Certification: formal credentials (e.g. AWS Certified, PMP)
- Tool: software/tools already identified in Pass 1 must NOT be re-extracted as skills — see "Already extracted tools" below

Rules:
- Extract from title, description, requirements, and responsibilities only.
- Do NOT extract any skill whose label appears in the "Already extracted tools" list — those are tools, not skills.
- Continue extracting concrete technical, domain, methodology, certification, and role-specific work skills whenever they are clearly supported. The soft-skill suppression rules below do NOT apply to hard skills like SQL, Scrum, Project Management, REST APIs, Incident Response, Machine Learning, or other concrete job skills.
- Suppress generic soft skills and hiring boilerplate unless the text gives domain-specific context. Bare mentions of communication, leadership, collaboration, teamwork, problem solving, detail orientation, adaptability, multitasking, fast learner, self-starter, positive attitude, ownership, or similar traits should usually be skipped.
- If a generic soft-skill word appears with concrete domain context, extract a short conventional label such as "Stakeholder Communication", "Stakeholder Management", "Cross-functional Collaboration", "Cross-functional Leadership", or "Team Management" instead of the generic word.
- Prefer concise, commonly used labels that stay close to the posting text. Do NOT invent overly specific labels, stacked modifiers, or consultant-style paraphrases when a standard skill name is enough.
- Avoid role-title restatements and background labels unless the body text clearly supports them as skills. For example, avoid generic labels like "Product Management" or "Full Stack Development" when the posting instead provides more concrete skills such as backlog management, product roadmap, JavaScript, REST APIs, or SQL.
- Do not split one sentence into several near-duplicate skills. Usually emit the simplest conventional label once.
- Before returning an empty skills array, double-check the title, requirements, and responsibilities for explicit hard skills, methodologies, certifications, or domain skills. Most postings should yield several non-tool skills even after generic soft skills are suppressed.
- For each skill, set source_span to the exact text fragment that supports this skill. Character offsets must be exact: end_char - start_char must equal the length of source_span.text (validation will reject invalid spans).
- Return only valid JSON: {"skills": [ ... ]}. No markdown, no code fence, no explanation.
- Do not extract negated requirements (e.g. "no Java required" should not produce a Java skill).
- If unsure whether a soft skill is specific enough, skip the soft skill but still extract any supported hard/domain skills from the same text.

Examples of what NOT to extract vs what to extract:
- "Excellent communication skills" -> SKIP generic "Communication"
- "Strong leadership and teamwork" -> SKIP generic "Leadership" and "Teamwork"
- "Problem-solving mindset in a fast-paced environment" -> SKIP generic "Problem Solving"
- "Stakeholder communication for cross-functional alignment" -> EXTRACT "Stakeholder Communication" (Soft); do NOT extract generic "Communication"
- "Lead sprint planning, retrospectives, and daily standups" -> EXTRACT "Scrum" and/or "Sprint Planning"; do NOT invent "Scrum Facilitation" unless the posting explicitly says facilitation
- "Build REST APIs with Java and Spring Boot" -> EXTRACT "REST APIs", "Java", and "Spring Boot"; do NOT suppress these because they are hard skills
- "Investigate incidents and perform root-cause analysis" -> EXTRACT "Incident Response" and/or "Root Cause Analysis"; do NOT extract generic "Problem Solving"
- "Partner with product, engineering, and design teams" -> EXTRACT "Cross-functional Collaboration" if role-relevant; do NOT also emit generic "Collaboration"
"""

SKILLS_USER_TEMPLATE = """Already extracted tools (do not re-extract as skills): {already_extracted_tools}

---
Title:
{title}

---
Description:
{description}

---
Requirements:
{requirements}

---
Responsibilities:
{responsibilities}
---

Return JSON with a "skills" array. Each skill must have: label, type, confidence, required_flag (or null), source_span (text, field_source, start_char, end_char)."""


def build_skills_prompt(
    title: str,
    description: str,
    requirements: str,
    responsibilities: str,
    already_extracted_tool_names: list[str] | None = None,
) -> str:
    """Build the full user prompt for skills extraction."""
    tools_str = ", ".join(already_extracted_tool_names) if already_extracted_tool_names else "(none)"
    user = SKILLS_USER_TEMPLATE.format(
        already_extracted_tools=tools_str,
        title=title or "(none)",
        description=description or "(none)",
        requirements=requirements or "(none)",
        responsibilities=responsibilities or "(none)",
    )
    return f"{SKILLS_SYSTEM_PROMPT}\n\n{user}"
