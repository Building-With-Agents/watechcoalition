# Prompt iteration log — Skills extraction (Exercise 4.5)

Document prompt changes and before/after metrics when iterating on the skills extraction prompt.

## Version history

| Version | Date | Change | Before metrics | After metrics |
|---------|------|--------|----------------|----------------|
| v1 | (initial) | Initial prompt in `agents/skills_extraction/prompts/skills_extraction_v1.py` | — | — |

## How to add an entry

1. Update the prompt in `agents/skills_extraction/prompts/skills_extraction_*.py` (or create a new versioned file).
2. Run the eval harness (Pair A) and record precision/recall per skill type.
3. Add a row to the table above with version, date, short description of the change, and before/after metrics.
4. Commit the prompt file and this log together.
