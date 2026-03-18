# Ground Truth Labeling Tool

A lightweight Streamlit app for hand-labeling job postings with `SkillRecord` and `ToolRecord` annotations that conform to the `extraction_types.py` Pydantic models.

## Quick Start

```bash
cd tools/ground-truth-labeler
pip install -r requirements.txt
streamlit run app.py
```

## Environment

The JSearch search tab requires a RapidAPI key in your environment:

```
JSEARCH_API_KEY=your_rapidapi_key_here
```

This is the same key used by the ingestion agent. If unset, use the Manual Entry tab instead.

## Workflow

1. **Search & Select** — Search JSearch for real El Paso postings, or paste text manually
2. **Review** — Read the job posting split by section (title, description, requirements, responsibilities)
3. **Label Skills** — Add SkillRecords with type, confidence, field_source, GenAI flag
4. **Label Tools** — Add ToolRecords with category, confidence, GenAI tool flag
5. **Review & Export** — Validate against Pydantic, add to dataset, export JSON

## Output Format

Exported JSON matches the `SkillRecord` and `ToolRecord` shapes from `extraction_types.py` (PR #64 schema). Each record can be loaded directly with Pydantic for validation.

## Target Dataset

20-30 labeled postings covering:
- Traditional roles (no AI/ML) — at least 5-8
- GenAI-focused roles (~30-40% of dataset)
- Ambiguous items (Excel, leadership, Python)
