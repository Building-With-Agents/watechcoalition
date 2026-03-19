# Ground Truth Labeling Tool

A lightweight Streamlit app for hand-labeling job postings with `SkillRecord` and `ToolRecord` annotations that conform to the `extraction_types.py` Pydantic models.

## Setup

```bash
cd tools/ground-truth-labeler
python -m venv venv
venv\Scripts\activate      # Windows
# source venv/bin/activate # macOS/Linux
pip install -r requirements.txt
# If pip is not recognized, use:
# python -m pip install -r requirements.txt
cp .env.example .env       # add your JSEARCH_API_KEY
```

## Run

```bash
python -m streamlit run app.py
```

## Environment

The JSearch search tab requires a RapidAPI key in your `.env` file:

```
JSEARCH_API_KEY=your_rapidapi_key_here
```

This is the same key used by the ingestion agent. If unset, use the Manual Entry tab instead.

## Workflow

1. **Search & Select** — Search JSearch for real El Paso postings, or paste text manually
2. **Review** — Read the job posting split by section (title, description, requirements, responsibilities)
3. **Label Skills** — Highlight text to capture `source_span`, then fill in skill label, type, confidence, GenAI flag
4. **Label Tools** — Same drag-to-select flow for tools with category and GenAI tool flag
5. **Review & Save** — Validate against Pydantic, preview JSON, append to dataset

## Features

- **Drag-to-select source_span** — highlight text to auto-capture `field_source`, `start_char`, `end_char`, and evidence text
- **Split-pane layout** — form on left, independently scrollable job text on right
- **JSearch caching** — results cached locally, survives refresh
- **Dark mode** support
- **UTF-8 mojibake fix** for JSearch API responses

## Design Decisions

- `SpanRecord.text` captures the evidence phrase; skill/tool label is user-typed (supports inferred skills from surrounding context)
- `SpanRecord` offsets validated by Pydantic (`end_char - start_char == len(text)`, `start_char >= 0`)

## Labeling Examples

See [ground-truth-examples.md](ground-truth-examples.md) for 5 hand-labeled examples showing the expected format, schema conventions, and labeler notes. Use these as a reference when labeling new records.

## Target Dataset

20–30 labeled postings covering:
- Traditional roles (no AI/ML) — at least 5–8
- GenAI-focused roles (~30–40% of dataset)
- Ambiguous items (Excel, leadership, Python)
