"""Pure classification tests — no database."""

from __future__ import annotations

from agents.enrichment.classification import (
    build_job_corpus,
    classify_job,
    classify_role,
    classify_seniority,
    flatten_extraction_json,
    tokenize,
)


def test_tokenize_basic() -> None:
    assert tokenize("Senior Data Engineer") == {"senior", "data", "engineer"}
    assert tokenize("") == set()
    assert "a" not in tokenize("a b cd")  # min len 2


def test_classify_role_hint_data_engineer() -> None:
    role = classify_role(
        "Senior Data Engineer",
        "senior data engineer",
        [("1", "Irrelevant Title")],
        [],
    )
    assert role == "Data Engineering"


def test_classify_role_tech_overlap() -> None:
    refs = [("t1", "Cloud Infrastructure"), ("t2", "Other")]
    corpus = "we need cloud and infrastructure experience"
    role = classify_role("Platform SRE", corpus, refs, [])
    assert role == "Cloud Infrastructure"


def test_classify_role_sector_fallback() -> None:
    role = classify_role(
        "Hospital IT Lead",
        "hospital healthcare technology patient systems",
        [],
        [("s1", "Healthcare Technology")],
    )
    assert role == "Healthcare Technology"


def test_classify_role_unclassified() -> None:
    role = classify_role(
        "Obscure Title XYZ",
        "obscure title xyz",
        [("t1", "Quantum Cryptography")],
        [("s1", "Aerospace Defense")],
    )
    assert role == "unclassified"


def test_classify_role_tie_breaker_lexicographic_id() -> None:
    """Equal overlap and title length → larger ref id wins."""
    role = classify_role(
        "Job",
        "beta fish",
        [("t1", "Alpha Beta"), ("t2", "Gamma Beta")],
        [],
    )
    assert role == "Gamma Beta"


def test_classify_seniority_executive_over_senior() -> None:
    assert classify_seniority("Senior VP of Engineering", None, None) == "executive"


def test_classify_seniority_lead_backend() -> None:
    assert classify_seniority("Lead Backend Engineer", None, None) == "lead"


def test_classify_seniority_junior() -> None:
    assert classify_seniority("Junior Software Engineer", None, None) == "junior"


def test_classify_seniority_intern_flag() -> None:
    assert classify_seniority("Software Engineer", None, None, is_internship=True) == "intern"


def test_classify_seniority_mid_ic_fallback() -> None:
    assert classify_seniority("Machine Learning Engineer", None, None) == "mid"


def test_classify_seniority_unknown() -> None:
    assert classify_seniority("Specialist", None, None) == "unknown"


def test_classify_seniority_description_fallback() -> None:
    assert classify_seniority("Specialist", "This is a senior level role.", None) == "senior"


def test_flatten_extraction_json_nested() -> None:
    skills = [{"skill_name": "Python", "source_span": {"text": "Python 3"}}]
    tasks = [{"task_description": "Build APIs"}]
    out = flatten_extraction_json(skills, None, tasks, None, None)
    assert "python" in out.lower()
    assert "apis" in out.lower()


def test_build_job_corpus_with_extraction() -> None:
    ext = {
        "skills": [{"label": "Go"}],
        "tools": [],
        "tasks": [],
        "responsibilities": [],
        "context": [],
    }
    c = build_job_corpus("Engineer", "Use tools", ext)
    assert "go" in c.lower()


def test_classify_job_integration() -> None:
    tech = [("1", "Software Engineering")]
    role, sen = classify_job(
        "Junior Software Engineer",
        None,
        None,
        tech,
        [],
    )
    assert role == "Software Engineering"
    assert sen == "junior"
