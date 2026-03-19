"""Skills extraction prompt v1 — versioned for Exercise 4.5 iteration.

Document changes in agents/eval/prompt_iteration_log.md.
"""

from __future__ import annotations

SKILLS_PROMPT_VERSION = "v1"

SKILLS_SYSTEM_PROMPT = """You are a skills extraction system for job postings. Extract explicit and implied skills from the given job text and return them as a JSON object with a "skills" array.

Output schema — each skill in the "skills" array must have:
- label: short name of the skill (e.g. "Python", "Leadership")
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
- Soft: interpersonal or behavioral (e.g. Leadership, Communication, Problem Solving)
- Certification: formal credentials (e.g. AWS Certified, PMP)
- Tool: software/tools already identified in Pass 1 must NOT be re-extracted as skills — see "Already extracted tools" below

Rules:
- Extract from title, description, requirements, and responsibilities only.
- Do NOT extract any skill whose label appears in the "Already extracted tools" list — those are tools, not skills.
- For each skill, set source_span to the exact text fragment that supports it. Character offsets must be exact: end_char - start_char must equal the length of source_span.text (validation will reject invalid spans).
- Return only valid JSON: {"skills": [ ... ]}. No markdown, no code fence, no explanation.
- Do not extract negated requirements (e.g. "no Java required" should not produce a Java skill).
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
    """Build the full user prompt for skills extraction.

    Parameters
    ----------
    title : str
        Job title.
    description : str
        Job description.
    requirements : str
        Requirements section.
    responsibilities : str
        Responsibilities section.
    already_extracted_tool_names : list[str] | None
        Pass 1 tool names so the LLM does not re-extract them as skills.

    Returns
    -------
    str
        Full prompt (system + user) for the LLM. Send system as system message
        and user as user message if your client supports roles; otherwise
        concatenate with a clear separator.
    """
    tools_str = ", ".join(already_extracted_tool_names) if already_extracted_tool_names else "(none)"
    user = SKILLS_USER_TEMPLATE.format(
        already_extracted_tools=tools_str,
        title=title or "(none)",
        description=description or "(none)",
        requirements=requirements or "(none)",
        responsibilities=responsibilities or "(none)",
    )
    return f"{SKILLS_SYSTEM_PROMPT}\n\n{user}"
