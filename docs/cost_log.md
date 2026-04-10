# Cost Log — Week 7 Pair D Analytics LLM Summaries

## Model

- **Call path:** `agents.analytics.insights.llm_summary.generate_summary()` → `agents.common.llm_adapter.complete()`.
- **Provider (default):** **Anthropic** — `complete()` uses `anthropic.Anthropic().messages.create()` when `LLM_PROVIDER` is not `mock` (see `agents/common/llm_adapter.py`, default `LLM_PROVIDER=anthropic`).
- **Model name:** Resolved as `os.getenv("EXTRACTION_MODEL_SKILLS", "claude-sonnet-4-5")` — same default as `complete()` when `model=` is passed from `llm_summary` (`agents/analytics/insights/llm_summary.py` lines 18, 100–105).
- **Mock / no API:** When `LLM_PROVIDER=mock`, `complete()` delegates to `mock_complete` and logs model `mock-sonnet-v1` (no paid tokens to the live Anthropic API).

## Token Usage per Summary (estimated)

`_build_prompt()` (`agents/analytics/insights/llm_summary.py`) builds the **user** message only. The **system** instruction is sent separately by `complete()` (`kwargs["system"]`).

Representative sample: label `Python`, trajectory `rising` / delta `+12` / confidence `0.91`, three `PostingFreshnessResult` rows (one per bucket):

| Component | Chars (approx.) | ÷4 ≈ tokens |
|-----------|-----------------|------------|
| User prompt (`_build_prompt` output) | 445 | **~111** |
| System string (fixed in `generate_summary`) | 147 | **~37** |
| **Input total (user + system)** | 592 | **~148** |

- **Prompt tokens (input):** **~150** (rounded; longer `label` / `sector:…` keys increase this slightly).
- **Completion tokens:** **~500** assumed (3–5 paragraphs; `max_tokens=1200` caps the response).
- **Total per summary (input + output):** **~650** tokens (150 + 500).

## Cost Estimate

Pricing aligned with **Sonnet tier** defaults in `llm_adapter.PRICING` (input **$0.003** / 1K tokens, output **$0.015** / 1K tokens — same as `3e-6` and `15e-6` USD per token for `claude-sonnet-4-5`):

| Line item | Calculation | USD |
|-----------|-------------|-----|
| Cost per 1K **input** tokens | (fixed) | **$0.003** |
| Cost per 1K **output** tokens | (fixed) | **$0.015** |
| **Cost per summary** | (150/1000)×0.003 + (500/1000)×0.015 | **~$0.0079** |
| **Cost per 10-summary batch** | 10 × ~$0.0079 | **~$0.079** |
| **Cost per 100-summary batch** | 100 × ~$0.0079 | **~$0.79** |

## Fallback

- **`FALLBACK_TEMPLATE`** (`agents/analytics/insights/llm_summary.py`) fills a single sentence with real **label**, **trend**, **delta**, **freshness_count**, and **confidence** — no LLM call.
- When the LLM path is skipped (failure, empty content, or exception), **`is_llm_generated=False`**, **`model_used=None`**, **`generated_at`** still set — **cost = $0.00** for that summary.

## Testing Notes

- Set **`STALENESS_THRESHOLD_MINUTES=0`** to force aggregate staleness and **`AnalyticsStaleAlert`**-shaped control-plane payloads (see `agents/analytics/insights/guardrails.py` / agent step 10).
- Set **`LLM_PROVIDER=mock`** to exercise `complete()` without real Anthropic API calls locally (`agents/common/llm_adapter.py`).
