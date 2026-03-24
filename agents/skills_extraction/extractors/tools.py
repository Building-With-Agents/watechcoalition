"""Tools extraction — Pass 1 (pattern matching) + optional LLM verification.

Extracts programming languages, frameworks, platforms, databases, and DevOps
tools from job posting text using regex/dictionary lookup. High-confidence
pattern matches incur zero LLM cost. Ambiguous matches are verified with a
Haiku-class LLM.

Week 4 implementation (Bryan + Emilio):
- Pattern matching (Pass 1) — regex/dictionary lookup against known tool lists
- Produce ToolRecord per tool with tool_name, category, confidence, source_span
- Verify with LLM (Haiku-class) only for ambiguous matches
- Zero LLM cost for high-confidence pattern matches

Reference: ARCHITECTURE_DEEP.md § Work Intelligence Agent — Hybrid Extraction.
"""

from __future__ import annotations

import re
from collections.abc import Iterable
from dataclasses import dataclass

from agents.common.types import JobRecord, SpanRecord, ToolRecord

FIELD_PRIORITY = {
    "title": 0,
    "requirements": 1,
    "responsibilities": 2,
    "description": 3,
}

BOUNDARY_CHARS = "A-Za-z0-9"
AMBIGUOUS_CONFIDENCE = 0.82
EXACT_CONFIDENCE = 0.97
EXPLICIT_ALIAS_CONFIDENCE = 0.98
CONTEXT_WINDOW = 48


@dataclass(frozen=True)
class ToolAlias:
    """One literal alias for a canonical tool."""

    text: str
    confidence: float = EXACT_CONFIDENCE
    requires_context: bool = False


@dataclass(frozen=True)
class ToolDefinition:
    """Canonical metadata for one tool in the Pass 1 catalog."""

    tool_name: str
    category: str
    aliases: tuple[ToolAlias, ...]
    context_keywords: tuple[str, ...] = ()
    context_patterns: tuple[str, ...] = ()
    is_genai_tool: bool = False


@dataclass(frozen=True)
class CompiledAlias:
    """Compiled regex plus canonical metadata for one alias."""

    definition: ToolDefinition
    alias: ToolAlias
    pattern: re.Pattern[str]


@dataclass(frozen=True)
class ToolCandidate:
    """Intermediate deterministic match before ToolRecord materialization."""

    tool_id: str
    tool_name: str
    category: str
    confidence: float
    source_span: SpanRecord
    is_genai_tool: bool

    @property
    def field_priority(self) -> int:
        """Sort helper for preferring earlier, higher-signal fields."""
        return FIELD_PRIORITY[self.source_span.field_source]

    @property
    def match_length(self) -> int:
        """Sort helper for preferring the more explicit alias when confidence ties."""
        return len(self.source_span.text)


TOOL_CATALOG: tuple[ToolDefinition, ...] = (
    ToolDefinition(
        tool_name="Python",
        category="language",
        aliases=(ToolAlias("Python"),),
    ),
    ToolDefinition(
        tool_name="JavaScript",
        category="language",
        aliases=(ToolAlias("JavaScript"), ToolAlias("Javascript", confidence=0.95)),
    ),
    ToolDefinition(
        tool_name="TypeScript",
        category="language",
        aliases=(ToolAlias("TypeScript"),),
    ),
    ToolDefinition(
        tool_name="Java",
        category="language",
        aliases=(ToolAlias("Java"),),
    ),
    ToolDefinition(
        tool_name="Go",
        category="language",
        aliases=(
            ToolAlias("Golang", confidence=EXPLICIT_ALIAS_CONFIDENCE),
            ToolAlias("Go", confidence=AMBIGUOUS_CONFIDENCE, requires_context=True),
        ),
        context_keywords=(
            "language",
            "programming",
            "developer",
            "engineer",
            "backend",
            "microservice",
            "api",
            "service",
            "code",
        ),
        context_patterns=(
            r"\b(?:using|with|in|build(?:ing)?|develop(?:ing)?|experience(?:\s+with)?|proficient(?:ly)?\s+in)\s+go\b",
            r"\bgo\s+(?:developer|engineer|services?|apis?|microservices?|language|code)\b",
            r"\bgo\b\s*[,/]\s*(?:python|java(?:script)?|typescript|rust|kubernetes|docker|aws|azure|gcp)\b",
            r"\b(?:python|java(?:script)?|typescript|rust|kubernetes|docker|aws|azure|gcp)\b\s*[,/]\s*go\b",
        ),
    ),
    ToolDefinition(
        tool_name="Rust",
        category="language",
        aliases=(ToolAlias("Rust"),),
    ),
    ToolDefinition(
        tool_name="SQL",
        category="language",
        aliases=(ToolAlias("SQL"),),
    ),
    ToolDefinition(
        tool_name="Bash",
        category="language",
        aliases=(ToolAlias("Bash"),),
    ),
    ToolDefinition(
        tool_name="React.js",
        category="framework",
        aliases=(ToolAlias("React.js", confidence=EXPLICIT_ALIAS_CONFIDENCE),),
    ),
    ToolDefinition(
        tool_name="React",
        category="framework",
        aliases=(ToolAlias("React"),),
    ),
    ToolDefinition(
        tool_name="Angular",
        category="framework",
        aliases=(ToolAlias("Angular"),),
    ),
    ToolDefinition(
        tool_name="Vue",
        category="framework",
        aliases=(ToolAlias("Vue"), ToolAlias("Vue.js", confidence=EXPLICIT_ALIAS_CONFIDENCE)),
    ),
    ToolDefinition(
        tool_name="Django",
        category="framework",
        aliases=(ToolAlias("Django"),),
    ),
    ToolDefinition(
        tool_name="FastAPI",
        category="framework",
        aliases=(ToolAlias("FastAPI"),),
    ),
    ToolDefinition(
        tool_name="Flask",
        category="framework",
        aliases=(ToolAlias("Flask"),),
    ),
    ToolDefinition(
        tool_name="Spring Boot",
        category="framework",
        aliases=(ToolAlias("Spring Boot", confidence=EXPLICIT_ALIAS_CONFIDENCE),),
    ),
    ToolDefinition(
        tool_name="Node.js",
        category="framework",
        aliases=(ToolAlias("Node.js", confidence=EXPLICIT_ALIAS_CONFIDENCE), ToolAlias("NodeJS")),
    ),
    ToolDefinition(
        tool_name="AWS",
        category="platform",
        aliases=(
            ToolAlias("Amazon Web Services", confidence=EXPLICIT_ALIAS_CONFIDENCE),
            ToolAlias("AWS"),
        ),
    ),
    ToolDefinition(
        tool_name="Azure",
        category="platform",
        aliases=(
            ToolAlias("Microsoft Azure", confidence=EXPLICIT_ALIAS_CONFIDENCE),
            ToolAlias("Microsoft Windows Azure", confidence=EXPLICIT_ALIAS_CONFIDENCE),
            ToolAlias("Azure"),
        ),
    ),
    ToolDefinition(
        tool_name="GCP",
        category="platform",
        aliases=(
            ToolAlias("Google Cloud Platform", confidence=EXPLICIT_ALIAS_CONFIDENCE),
            ToolAlias("GCP"),
        ),
    ),
    ToolDefinition(
        tool_name="Docker",
        category="platform",
        aliases=(ToolAlias("Docker"),),
    ),
    ToolDefinition(
        tool_name="Kubernetes",
        category="platform",
        aliases=(ToolAlias("Kubernetes"), ToolAlias("K8s", confidence=0.95)),
    ),
    ToolDefinition(
        tool_name="PostgreSQL",
        category="database",
        aliases=(ToolAlias("PostgreSQL"), ToolAlias("Postgres", confidence=0.95)),
    ),
    ToolDefinition(
        tool_name="MySQL",
        category="database",
        aliases=(ToolAlias("MySQL"),),
    ),
    ToolDefinition(
        tool_name="MongoDB",
        category="database",
        aliases=(ToolAlias("MongoDB"),),
    ),
    ToolDefinition(
        tool_name="Redis",
        category="database",
        aliases=(ToolAlias("Redis"),),
    ),
    ToolDefinition(
        tool_name="Elasticsearch",
        category="database",
        aliases=(ToolAlias("Elasticsearch"),),
    ),
    ToolDefinition(
        tool_name="Snowflake",
        category="database",
        aliases=(ToolAlias("Snowflake"),),
    ),
    # BI / analytics platforms (eval GT + common job-posting literals)
    ToolDefinition(
        tool_name="Tableau",
        category="platform",
        aliases=(ToolAlias("Tableau"),),
    ),
    ToolDefinition(
        tool_name="Looker",
        category="platform",
        aliases=(ToolAlias("Looker"),),
    ),
    ToolDefinition(
        tool_name="Power BI",
        category="platform",
        aliases=(ToolAlias("Power BI", confidence=EXPLICIT_ALIAS_CONFIDENCE),),
    ),
    ToolDefinition(
        tool_name="Sigma",
        category="platform",
        aliases=(ToolAlias("Sigma", confidence=AMBIGUOUS_CONFIDENCE, requires_context=True),),
        context_keywords=(
            "bi",
            "analytics",
            "dashboard",
            "data",
            "visualization",
            "warehouse",
            "snowflake",
            "looker",
            "tableau",
        ),
        context_patterns=(
            r"\b(?:sigma|modern)\s+bi\b",
            r"\b(?:tableau|looker|power\s+bi|snowflake|sigma)\b",
        ),
    ),
    ToolDefinition(
        tool_name="Databricks",
        category="platform",
        aliases=(ToolAlias("Databricks"),),
    ),
    ToolDefinition(
        tool_name="dbt",
        category="devops",
        aliases=(ToolAlias("dbt"), ToolAlias("DBT", confidence=EXPLICIT_ALIAS_CONFIDENCE)),
    ),
    ToolDefinition(
        tool_name="Jira",
        category="platform",
        aliases=(ToolAlias("Jira"),),
    ),
    ToolDefinition(
        tool_name="Confluence",
        category="platform",
        aliases=(ToolAlias("Confluence"),),
    ),
    ToolDefinition(
        tool_name="Miro",
        category="platform",
        aliases=(ToolAlias("Miro"),),
    ),
    ToolDefinition(
        tool_name="Git",
        category="devops",
        aliases=(ToolAlias("Git"),),
    ),
    ToolDefinition(
        tool_name="GitLab",
        category="devops",
        aliases=(ToolAlias("GitLab"), ToolAlias("Gitlab", confidence=0.95)),
    ),
    ToolDefinition(
        tool_name="Splunk",
        category="platform",
        aliases=(
            ToolAlias("Splunk"),
            ToolAlias("Splunk (ES)", confidence=EXPLICIT_ALIAS_CONFIDENCE),
            ToolAlias("Splunk ES", confidence=EXPLICIT_ALIAS_CONFIDENCE),
        ),
    ),
    ToolDefinition(
        tool_name="Twilio",
        category="platform",
        aliases=(ToolAlias("Twilio"),),
    ),
    ToolDefinition(
        tool_name="Next.js",
        category="framework",
        aliases=(ToolAlias("Next.js", confidence=EXPLICIT_ALIAS_CONFIDENCE), ToolAlias("NextJS")),
    ),
    ToolDefinition(
        tool_name="Prisma",
        category="framework",
        aliases=(ToolAlias("Prisma", confidence=AMBIGUOUS_CONFIDENCE, requires_context=True),),
        context_keywords=(
            "orm",
            "schema",
            "typescript",
            "javascript",
            "next",
            "node",
            "postgresql",
            "database",
            "migrate",
        ),
        context_patterns=(
            r"\bprisma\s+(?:orm|client|schema|migrate)\b",
            r"\b(?:with|using)\s+prisma\b",
        ),
    ),
    ToolDefinition(
        tool_name="SQL Server",
        category="database",
        aliases=(
            ToolAlias("SQL Server", confidence=EXPLICIT_ALIAS_CONFIDENCE),
            ToolAlias("Microsoft SQL Server", confidence=EXPLICIT_ALIAS_CONFIDENCE),
        ),
    ),
    ToolDefinition(
        tool_name="Visual Studio",
        category="other",
        aliases=(ToolAlias("Visual Studio", confidence=EXPLICIT_ALIAS_CONFIDENCE),),
    ),
    ToolDefinition(
        tool_name=".NET",
        category="framework",
        aliases=(ToolAlias(".NET", confidence=EXPLICIT_ALIAS_CONFIDENCE),),
    ),
    ToolDefinition(
        tool_name="C#",
        category="language",
        aliases=(ToolAlias("C#"),),
    ),
    ToolDefinition(
        tool_name="C++",
        category="language",
        aliases=(ToolAlias("C++"),),
    ),
    ToolDefinition(
        tool_name="Scala",
        category="language",
        aliases=(ToolAlias("Scala"),),
    ),
    ToolDefinition(
        tool_name="Linux",
        category="platform",
        aliases=(ToolAlias("Linux"),),
    ),
    ToolDefinition(
        tool_name="PowerShell",
        category="language",
        aliases=(ToolAlias("PowerShell"),),
    ),
    ToolDefinition(
        tool_name="PyTest",
        category="devops",
        aliases=(ToolAlias("PyTest"), ToolAlias("pytest", confidence=0.95)),
    ),
    ToolDefinition(
        tool_name="PyTorch",
        category="framework",
        aliases=(ToolAlias("PyTorch"),),
    ),
    ToolDefinition(
        tool_name="TensorFlow",
        category="framework",
        aliases=(ToolAlias("TensorFlow"),),
    ),
    ToolDefinition(
        tool_name="Keras",
        category="framework",
        aliases=(ToolAlias("Keras"),),
    ),
    ToolDefinition(
        tool_name="Pandas",
        category="framework",
        aliases=(ToolAlias("Pandas"),),
    ),
    ToolDefinition(
        tool_name="NumPy",
        category="framework",
        aliases=(ToolAlias("NumPy"), ToolAlias("Numpy", confidence=0.95)),
    ),
    ToolDefinition(
        tool_name="matplotlib",
        category="framework",
        aliases=(ToolAlias("matplotlib"),),
    ),
    ToolDefinition(
        tool_name="ggplot2",
        category="framework",
        aliases=(ToolAlias("ggplot2"),),
    ),
    ToolDefinition(
        tool_name="Datawrapper",
        category="platform",
        aliases=(ToolAlias("Datawrapper"),),
    ),
    ToolDefinition(
        tool_name="Burp Suite",
        category="platform",
        aliases=(ToolAlias("Burp Suite", confidence=EXPLICIT_ALIAS_CONFIDENCE),),
    ),
    ToolDefinition(
        tool_name="Wireshark",
        category="platform",
        aliases=(ToolAlias("Wireshark"),),
    ),
    ToolDefinition(
        tool_name="Kali Linux",
        category="platform",
        aliases=(ToolAlias("Kali Linux", confidence=EXPLICIT_ALIAS_CONFIDENCE),),
    ),
    ToolDefinition(
        tool_name="Nessus",
        category="platform",
        aliases=(ToolAlias("Nessus"),),
    ),
    ToolDefinition(
        tool_name="Metasploit",
        category="platform",
        aliases=(ToolAlias("Metasploit"),),
    ),
    ToolDefinition(
        tool_name="CrowdStrike",
        category="platform",
        aliases=(ToolAlias("CrowdStrike"),),
    ),
    ToolDefinition(
        tool_name="Cisco",
        category="platform",
        aliases=(ToolAlias("Cisco"),),
    ),
    ToolDefinition(
        tool_name="Fortinet",
        category="platform",
        aliases=(ToolAlias("Fortinet"),),
    ),
    ToolDefinition(
        tool_name="MITRE ATT&CK",
        category="platform",
        aliases=(ToolAlias("MITRE ATT&CK", confidence=EXPLICIT_ALIAS_CONFIDENCE),),
    ),
    ToolDefinition(
        tool_name="Visio",
        category="other",
        aliases=(ToolAlias("Visio"),),
    ),
    ToolDefinition(
        tool_name="PowerPoint",
        category="other",
        aliases=(
            ToolAlias("PowerPoint", confidence=EXPLICIT_ALIAS_CONFIDENCE),
            ToolAlias("Powerpoint", confidence=0.95),
            ToolAlias("Microsoft PowerPoint", confidence=EXPLICIT_ALIAS_CONFIDENCE),
        ),
    ),
    ToolDefinition(
        tool_name="Outlook",
        category="other",
        aliases=(
            ToolAlias("Microsoft Outlook", confidence=EXPLICIT_ALIAS_CONFIDENCE),
            ToolAlias("Outlook", confidence=AMBIGUOUS_CONFIDENCE, requires_context=True),
        ),
        context_keywords=(
            "microsoft",
            "office",
            "email",
            "calendar",
            "exchange",
            "teams",
        ),
        context_patterns=(
            r"\bmicrosoft\s+outlook\b",
            r"\boutlook\s+(?:calendar|email|mailbox)\b",
        ),
    ),
    ToolDefinition(
        tool_name="Microsoft Projects",
        category="other",
        aliases=(
            ToolAlias("Microsoft Projects", confidence=EXPLICIT_ALIAS_CONFIDENCE),
            ToolAlias("Microsoft Project", confidence=EXPLICIT_ALIAS_CONFIDENCE),
        ),
    ),
    ToolDefinition(
        tool_name="ChatGPT",
        category="ai_tool",
        aliases=(ToolAlias("ChatGPT"),),
        is_genai_tool=True,
    ),
    ToolDefinition(
        tool_name="Claude",
        category="ai_tool",
        aliases=(ToolAlias("Claude", confidence=AMBIGUOUS_CONFIDENCE, requires_context=True),),
        context_keywords=(
            "anthropic",
            "llm",
            "ai",
            "model",
            "prompt",
            "api",
            "assistant",
        ),
        context_patterns=(
            r"\bclaude\s+(?:\d|opus|sonnet|haiku)\b",
            r"\banthropic['’]s\s+claude\b",
        ),
        is_genai_tool=True,
    ),
    ToolDefinition(
        tool_name="Cursor",
        category="ai_tool",
        aliases=(ToolAlias("Cursor", confidence=AMBIGUOUS_CONFIDENCE, requires_context=True),),
        context_keywords=(
            "ide",
            "editor",
            "copilot",
            "ai",
            "coding",
            "developer",
            "vscode",
        ),
        context_patterns=(
            r"\bcursor\s+(?:ide|editor|ai)\b",
            r"\b(?:the\s+)?cursor\s+editor\b",
        ),
        is_genai_tool=True,
    ),
    ToolDefinition(
        tool_name="GitHub Copilot",
        category="ai_tool",
        aliases=(ToolAlias("GitHub Copilot", confidence=EXPLICIT_ALIAS_CONFIDENCE),),
        is_genai_tool=True,
    ),
    ToolDefinition(
        tool_name="Flextrack",
        category="platform",
        aliases=(ToolAlias("Flextrack"),),
    ),
    ToolDefinition(
        tool_name="Terraform",
        category="devops",
        aliases=(ToolAlias("Terraform"),),
    ),
    ToolDefinition(
        tool_name="Ansible",
        category="devops",
        aliases=(ToolAlias("Ansible"),),
    ),
    ToolDefinition(
        tool_name="Jenkins",
        category="devops",
        aliases=(ToolAlias("Jenkins"),),
    ),
    ToolDefinition(
        tool_name="GitHub Actions",
        category="devops",
        aliases=(ToolAlias("GitHub Actions"),),
    ),
    ToolDefinition(
        tool_name="GitLab CI",
        category="devops",
        aliases=(ToolAlias("GitLab CI"),),
    ),
    ToolDefinition(
        tool_name="LangChain",
        category="ai_tool",
        aliases=(ToolAlias("LangChain"),),
        is_genai_tool=True,
    ),
    ToolDefinition(
        tool_name="LlamaIndex",
        category="ai_tool",
        aliases=(ToolAlias("LlamaIndex"),),
        is_genai_tool=True,
    ),
    ToolDefinition(
        tool_name="Hugging Face",
        category="ai_tool",
        aliases=(ToolAlias("Hugging Face"),),
        is_genai_tool=True,
    ),
    ToolDefinition(
        tool_name="OpenAI API",
        category="ai_tool",
        aliases=(ToolAlias("OpenAI API"), ToolAlias("OpenAI APIs", confidence=0.95)),
        is_genai_tool=True,
    ),
    ToolDefinition(
        tool_name="Anthropic API",
        category="ai_tool",
        aliases=(ToolAlias("Anthropic API"), ToolAlias("Anthropic APIs", confidence=0.95)),
        is_genai_tool=True,
    ),
    ToolDefinition(
        tool_name="Pinecone",
        category="ai_tool",
        aliases=(ToolAlias("Pinecone"),),
        is_genai_tool=True,
    ),
    ToolDefinition(
        tool_name="Weaviate",
        category="ai_tool",
        aliases=(ToolAlias("Weaviate"),),
        is_genai_tool=True,
    ),
    ToolDefinition(
        tool_name="Microsoft Excel",
        category="other",
        aliases=(
            ToolAlias("Microsoft Excel", confidence=EXPLICIT_ALIAS_CONFIDENCE),
            ToolAlias("Excel", confidence=AMBIGUOUS_CONFIDENCE, requires_context=True),
        ),
        context_keywords=(
            "microsoft",
            "office",
            "spreadsheet",
            "spreadsheets",
            "workbook",
            "worksheet",
            "pivot",
            "vlookup",
            "formula",
            "formulas",
            "macro",
            "reporting",
            "dashboard",
        ),
        context_patterns=(
            r"\b(?:advanced|expert|expertise|proficient|using)\s+excel\b",
            r"\bexcel\b\s+(?:reporting|dashboard|dashboards|spreadsheet|spreadsheets|workbook|workbooks|worksheet|worksheets|formula|formulas|macro|macros|pivot)\b",
        ),
    ),
)


def _compile_aliases() -> tuple[CompiledAlias, ...]:
    """Compile all catalog aliases once at import time for fast matching."""
    compiled: list[CompiledAlias] = []
    for definition in TOOL_CATALOG:
        for alias in definition.aliases:
            pattern = re.compile(
                rf"(?<![{BOUNDARY_CHARS}]){re.escape(alias.text)}(?![{BOUNDARY_CHARS}])",
                re.IGNORECASE,
            )
            compiled.append(CompiledAlias(definition=definition, alias=alias, pattern=pattern))
    return tuple(compiled)


COMPILED_ALIASES = _compile_aliases()


def extract_tools(job_record: JobRecord) -> list[ToolRecord]:
    """Extract tools from a normalized job record using pattern matching.

    Parameters
    ----------
    job_record : JobRecord
        A normalized job posting from the normalization pipeline.

    Returns
    -------
    list[ToolRecord]
        Extracted tools with categories and source spans.
    """
    best_by_tool: dict[str, ToolCandidate] = {}

    for field_source, text in _iter_job_fields(job_record):
        for candidate in _find_candidates(text=text, field_source=field_source):
            current = best_by_tool.get(candidate.tool_id)
            if current is None or _is_better_candidate(candidate, current):
                best_by_tool[candidate.tool_id] = candidate

    ordered_candidates = sorted(
        best_by_tool.values(),
        key=lambda candidate: (
            candidate.field_priority,
            candidate.source_span.start_char,
            candidate.tool_name.casefold(),
        ),
    )
    return [
        ToolRecord(
            tool_id=candidate.tool_id,
            tool_name=candidate.tool_name,
            category=candidate.category,
            confidence=candidate.confidence,
            source_span=candidate.source_span,
            is_genai_tool=candidate.is_genai_tool,
        )
        for candidate in ordered_candidates
    ]


def _iter_job_fields(job_record: JobRecord) -> Iterable[tuple[str, str]]:
    """Yield only non-empty extractable job fields in priority order."""
    for field_source in ("title", "requirements", "responsibilities", "description"):
        value = getattr(job_record, field_source, None)
        if isinstance(value, str) and value.strip():
            yield field_source, value


def _find_candidates(*, text: str, field_source: str) -> list[ToolCandidate]:
    """Find non-overlapping tool candidates inside one text field."""
    raw_candidates: list[ToolCandidate] = []
    for compiled_alias in COMPILED_ALIASES:
        for match in compiled_alias.pattern.finditer(text):
            if compiled_alias.alias.requires_context and not _has_context(
                text=text,
                match=match,
                definition=compiled_alias.definition,
            ):
                continue
            raw_candidates.append(
                _build_candidate(
                    definition=compiled_alias.definition,
                    match=match,
                    field_source=field_source,
                    confidence=compiled_alias.alias.confidence,
                )
            )

    return _suppress_overlaps(raw_candidates)


def _build_candidate(
    *,
    definition: ToolDefinition,
    match: re.Match[str],
    field_source: str,
    confidence: float,
) -> ToolCandidate:
    """Convert one regex match into a deterministic candidate record."""
    matched_text = match.group(0)
    source_span = SpanRecord(
        text=matched_text,
        field_source=field_source,
        start_char=match.start(),
        end_char=match.end(),
    )
    return ToolCandidate(
        tool_id=_build_tool_id(definition.tool_name),
        tool_name=definition.tool_name,
        category=definition.category,
        confidence=confidence,
        source_span=source_span,
        is_genai_tool=definition.is_genai_tool,
    )


def _suppress_overlaps(candidates: list[ToolCandidate]) -> list[ToolCandidate]:
    """Keep the strongest non-overlapping candidates within one field."""
    accepted: list[ToolCandidate] = []

    for candidate in sorted(
        candidates,
        key=lambda item: (
            item.source_span.start_char,
            -item.match_length,
            -item.confidence,
            item.tool_name.casefold(),
        ),
    ):
        if any(_spans_overlap(candidate.source_span, existing.source_span) for existing in accepted):
            continue
        accepted.append(candidate)

    return accepted


def _spans_overlap(left: SpanRecord, right: SpanRecord) -> bool:
    """Return True when two source spans overlap in the same field."""
    if left.field_source != right.field_source:
        return False
    return left.start_char < right.end_char and right.start_char < left.end_char


def _has_context(
    *,
    text: str,
    match: re.Match[str],
    definition: ToolDefinition,
) -> bool:
    """Resolve ambiguous aliases only when nearby technical context is present."""
    window_start = max(0, match.start() - CONTEXT_WINDOW)
    window_end = min(len(text), match.end() + CONTEXT_WINDOW)
    context_window = text[window_start:window_end]

    if any(
        re.search(pattern, context_window, flags=re.IGNORECASE)
        for pattern in definition.context_patterns
    ):
        return True

    return any(keyword in context_window.casefold() for keyword in definition.context_keywords)


def _build_tool_id(tool_name: str) -> str:
    """Generate a stable slug-like identifier for a canonical tool name."""
    slug = re.sub(r"[^a-z0-9]+", "-", tool_name.casefold()).strip("-")
    return f"tool-{slug}"


def _is_better_candidate(candidate: ToolCandidate, current: ToolCandidate) -> bool:
    """Prefer higher-confidence, more explicit, earlier-field matches."""
    candidate_rank = (
        candidate.confidence,
        -candidate.field_priority,
        candidate.match_length,
        -candidate.source_span.start_char,
    )
    current_rank = (
        current.confidence,
        -current.field_priority,
        current.match_length,
        -current.source_span.start_char,
    )
    return candidate_rank > current_rank
