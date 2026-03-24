# Prompt iteration log — Skills extraction (Exercise 4.5)

Document prompt changes and before/after metrics when iterating on the skills extraction prompt.

## Version history

| Version | Date | Change | Before metrics | After metrics |
|---------|------|--------|----------------|----------------|
| v1 | (initial) | Initial prompt in `agents/skills_extraction/prompts/skills_extraction_v1.py` | — | — |
| v0-baseline | 2026-03-18 | Placeholder ground truth (8 records, title-only, keyword stub extractor) | — | Skills P=1.00 R=0.12; Tools P=0.00 R=0.00 |
| v1-pipeline-30 | 2026-03-23 | **Baseline (no prompt change):** `run_extraction_eval --mode pipeline`, `extraction_ground_truth.json` (30 jobs), prompt `skills_extraction_v1`, git `b7ea71da` | — | **Skills** P=0.17 R=0.41 (91/221 matched); **Tools** P=0.54 R=0.25 (32/127 matched); ~78.6k tokens, ~\$0.62 est., 0 LLM failures |
| **pass1-catalog-v2** | 2026-03-24 | **Pass 1 only:** expand `TOOL_CATALOG` in `agents/skills_extraction/extractors/tools.py` (BI stacks, Atlassian, data platforms, security tools, Microsoft Office naming, split `React.js` vs `React`, Azure `Microsoft Windows Azure`, Splunk ES variants, MITRE ATT&CK); **eval:** `normalize_tool_label_for_eval()` in `extraction_eval_core.py` so `Microsoft Excel`/`excel`/`Microsoft PowerPoint`/`powerpoint`/`Microsoft Outlook`/`outlook` align for micro P/R | **Tools (v1-pipeline-30, 30 jobs):** P=0.54 R=0.25 (32/127 matched) | **Pass-1 micro on 30 jobs (same GT, `extract_tools` + eval label equivalence):** **Tools P=0.75 R=0.69** (87/127 matched, 116 pred); *not* full pipeline re-run — see § Exercise 4.5 Pass-1 audit below |
| **pass1-catalog-v3** | 2026-03-23 | **Pass 1 correctness pass + full rerun:** fix `tool_id` collision so `C++` and `C#` no longer collapse, add contextual `R`, add Office-list `Projects` → `Microsoft Projects`, keep eval tool-label equivalence for Office and extend to `Splunk (ES)` / `Fortinet Firewalls`, then re-run full pipeline on all 30 jobs | **v1-pipeline-30:** Skills P=0.17 R=0.41 (91/221 matched); Tools P=0.54 R=0.25 (32/127 matched) | **Full pipeline (30 jobs):** **Skills P=0.16 R=0.38** (84/221 matched); **Tools P=0.76 R=0.72** (92/127 matched, 121 pred); ~68.6k tokens, ~\$0.48 est., 0 LLM failures |
| **v2-softskill-filter** | 2026-03-23 | **Initial v2 prompt:** add generic soft-skill suppression guidance, negative examples, and contextual replacements in `agents/skills_extraction/prompts/skills_extraction_v2.py`; this first pass proved too strict and encouraged empty outputs / over-specific relabeling | **pass1-catalog-v3:** Skills P=0.16 R=0.38 (84/221 matched, 516 pred); Tools P=0.76 R=0.72 (92/127 matched) | **Full pipeline (30 jobs):** **Skills P=0.13 R=0.19** (41/221 matched, 309 pred); **Tools P=0.76 R=0.72** (92/127 matched, 121 pred); ~49.4k tokens, ~\$0.26 est., 0 LLM failures |
| **v2-softskill-filter-r2** | 2026-03-23 | **Refined v2 prompt:** preserve hard-skill extraction, prefer conventional labels, avoid role-title restatements, reduce near-duplicate paraphrases, and require a hard-skill double-check before returning empty skills | **v2-softskill-filter:** Skills P=0.13 R=0.19 (41/221 matched, 309 pred); Tools P=0.76 R=0.72 (92/127 matched) | **Full pipeline (30 jobs):** **Skills P=0.20 R=0.33** (72/221 matched, 365 pred); **Tools P=0.76 R=0.72** (92/127 matched, 121 pred); ~66.3k tokens, ~\$0.34 est., 0 LLM failures |

## How to add an entry

1. Update the prompt in `agents/skills_extraction/prompts/skills_extraction_*.py` (or create a new versioned file).
2. Run the eval harness (Pair A) and record precision/recall per skill type.
3. Add a row to the table above with version, date, short description of the change, and before/after metrics.
4. Commit the prompt file and this log together.

---

## Integration verification checklist

- [ ] **llm_audit_log coverage:** Verify `llm_audit_log` contains entries for all LLM calls from all pairs (Bryan/Emilio, Angel/Fabian, Juan/Enrique, etc.).
- [ ] **Cost accuracy:** Verify cost data is accurate after Pair C's prompt iteration changes (compare `cost_usd` and `token_count` before/after).
- [ ] **Cost-per-record impact:** Check whether prompt revisions changed cost per record (more/fewer tokens).
- [ ] **Cost projections:** Update cost projections in `cost_model_week4.md` if per-record cost changed significantly.
- [ ] **End-to-end:** Verify `extracted_intelligence` has correct `extraction_tokens_used`, `extraction_cost_usd`, and `extraction_metadata` populated.

### llm_audit_log coverage

| Agent / pair     | LLM calls go through adapter? | Notes |
|------------------|-------------------------------|--------|
| Skills extraction| Yes (`invoke_skills_llm` → `log_extraction_event`) | Azure deployment from `EXTRACTION_*` / `AZURE_OPENAI_*` |
| _Pair C_         | _Verify_                      | _TBD_  |
| _Other_          | _Verify_                      | _TBD_  |

### Cost before / after prompt iteration

| When   | Avg tokens per record | Avg cost per record | Notes |
|--------|------------------------|---------------------|--------|
| Before | ~2,620 / job (78,603÷30) | ~\$0.0208 / job (\$0.623÷30) | Run `exercise-4-5-baseline` snapshot 2026-03-23 |
| After Pass 1 | ~2,287 / job (68,597÷30) | ~\$0.0160 / job (\$0.47841÷30) | Run `pass1-catalog-v3` snapshot 2026-03-23 |
| After v2 prompt | ~2,209 / job (66,282÷30) | ~\$0.0114 / job (\$0.3414÷30) | Run `v2-softskill-filter-r2` snapshot 2026-03-23 |

### extracted_intelligence columns

| Check                          | Result | Notes |
|--------------------------------|--------|--------|
| `extraction_tokens_used` set   | _TBD_  | _Sample query_ |
| `extraction_cost_usd` set      | _TBD_  | _Sample query_ |
| `extraction_metadata` populated | **Yes (Pass 2)** | `SkillsExtractionAgent` writes `ExtractionMetadata` JSON on LLM path; verify with DB sample |

---

## Changelog

| Date       | Who / what |
|------------|------------|
| _Week 4_   | Template created; fill after prompt iteration and integration runs. |
| 2026-03-18 | Recorded v0-baseline: 8 placeholder records (title-only, no `text` field), keyword-matching stub extractor. Skills Precision 1.00, Recall 0.12 (3/24 matched). Tools Precision 0.00, Recall 0.00 (0/12). Ground truth dataset is WIP — expand to 30-50 records with full `text` descriptions and run against real LLM extractor for meaningful baseline. |
| 2026-03-23 | **v1-pipeline-30:** Full pipeline eval on 30 labeled jobs. Artifacts: `agents/eval/runs/20260323T111224-0600_exercise-4-5-baseline.json`, `agents/eval/prompt_backlog/20260323T111224-0600_exercise-4-5-baseline.md`. |
| 2026-03-24 | **Exercise 4.5 — Pass 1 catalog + eval label alignment:** See § below. |
| 2026-03-23 | **pass1-catalog-v3:** Full pipeline rerun after Pass 1 correctness fixes. Artifacts: `agents/eval/runs/20260323T222345-0600_pass1-catalog-v3.json`, `agents/eval/prompt_backlog/20260323T222345-0600_pass1-catalog-v3.md`. |
| 2026-03-23 | **v2-softskill-filter:** Initial v2 prompt rerun after adding generic soft-skill suppression and negative examples. Artifacts: `agents/eval/runs/20260323T231434-0600_v2-softskill-filter.json`, `agents/eval/prompt_backlog/20260323T231434-0600_v2-softskill-filter.md`. |
| 2026-03-23 | **v2-softskill-filter-r2:** Refined v2 prompt rerun after restoring hard-skill coverage and standardizing labels. Artifacts: `agents/eval/runs/20260323T233540-0600_v2-softskill-filter-r2.json`, `agents/eval/prompt_backlog/20260323T233540-0600_v2-softskill-filter-r2.md`. |

---

## Exercise 4.5 — Pass 1 catalog audit (GT tools vs `extract_tools`)

### Root cause

`TOOL_CATALOG` was missing many **literal vendor / BI / collaboration** strings that appear in `extraction_ground_truth.json` (e.g. Tableau, Looker, Power BI, Jira, Confluence, Databricks, dbt). Pass 1 cannot emit a `ToolRecord` for a name that is not in the catalog, so **tools recall stayed low** even when Pass 2 skills precision was high.

**Additional:** `React` and `React.js` shared one `ToolDefinition`, so matches on `React.js` still emitted `tool_name="React"`, which did not match GT `react.js`. **GT vs canonical names** for Office (e.g. `excel` vs `Microsoft Excel`) also inflated missed counts.

### Audit: GT tool labels (30 jobs) with no Pass-1 match *before* catalog expansion

Typical buckets:

- **Missing catalog entries:** BI (Tableau, Looker, Power BI, Sigma), Atlassian (Jira, Confluence), data (Databricks, dbt), collaboration (Miro), security (Splunk, Wireshark, Burp Suite, Kali Linux, Nessus, Metasploit, CrowdStrike, Cisco, Fortinet), dev (Git, GitLab, Next.js, Prisma, SQL Server, Visual Studio, PyTest, .NET, C#, C++, Scala, Linux, PowerShell), ML libs (PyTorch, TensorFlow, Keras, Pandas, NumPy, matplotlib, ggplot2, Datawrapper), GenAI products (ChatGPT, Claude, Cursor, GitHub Copilot), etc.
- **Not literal strings in posting text:** GT lists tools (e.g. Snowflake, dbt) that do not appear in the job text — Pass 1 cannot match.
- **Abstract categories, not products:** e.g. “CI/CD Tools”, “Modern Data Platforms”, “SQL Data Query Tools” — out of scope for dictionary Pass 1.

### After this change

On all 30 `extraction_ground_truth.json` jobs, the current `extract_tools` + `normalize_tool_label_for_eval` yields **92 / 127** GT tool labels matched (micro **P≈0.76, R≈0.72**). A full `run_extraction_eval --mode pipeline` rerun on the same 30 jobs produces the same tools counts (**92 / 127**, **121 predicted**) because tools are still owned by Pass 1.

Remaining misses are now mostly:

- **Not literal strings in posting text:** `Snowflake`, `dbt`, `ChatGPT`, `Claude`, `Cursor`, `Twilio`
- **Abstract categories, not concrete products:** `Large Language Models (LLMs)`, `SQL Data Query Tools`, `Data Visualization Tools`, `Reporting Tools`, `Data Processing Systems`, `Quality Assurance (QA) Tools`
- **Non-tool governance / compliance labels still present in GT tools:** `GDPR`, `Risk Register`, `ISO 2700`
