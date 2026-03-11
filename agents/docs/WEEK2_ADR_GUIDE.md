# Week 2 ADR Task — What You Need to Do

The TODO item **"Week 2 ADRs (if team chooses different tech)"** is a **documentation/decision** task, not a code task. Here’s what it means and how to complete it.

---

## What the task is asking

1. **CLAUDE:** “If your team’s Week 2 ADRs select different technologies, adapt the implementation.”  
   → So the codebase is allowed to follow a **different** tech choice than the reference, as long as it’s decided and documented.

2. **ARCHITECTURAL_DECISIONS:** “SA decisions must **converge** before the agent that depends on them.”  
   → **Converge** = the team has a clear, documented decision (and if you pick the reference, the ADR still explains *why*).

3. **Your job for Week 2:** **Document or confirm** any Week 2–relevant SA decisions so that:
   - Future you (or the team) knows what was decided.
   - If someone later chooses different tech, they know what to change.

---

## Which decisions are “Week 2–relevant”?

Week 2 **implementation** touches these SA decisions:

| Decision | What Week 2 uses | Deadline in tracker | Week 2 relevance |
|----------|------------------|----------------------|------------------|
| **#11 — LLM provider** | `llm_adapter.py` (provider-agnostic, Azure default) | Before Week 8 | **Yes** — adapter is implemented in Week 2. |
| **#13 — Multi-agent framework** | No framework yet; plain Python loop in runner | Before Week 1 | **Partial** — no LangGraph in Week 2; matters more in Week 6. |
| **#14 — Message bus** | In-process only (no Kafka, etc.); events passed in memory | Before Week 3 | **Yes** — you’re using “in-process Python events.” |

So the ones that are clearly Week 2–relevant are **#11** and **#14**. **#13** you can mention briefly (e.g. “deferred to Week 6 when we add orchestration”).

---

## Two ways to complete the task

### Option A — Confirm reference implementation (minimal)

**Use when:** You (or the team) are sticking with the reference implementation and don’t plan to evaluate alternatives now.

**What to do:**

1. Add a short **confirmation note** (e.g. in this repo or in `docs/planning/`) that states:
   - For **Week 2**, we are using the **reference implementation** for:
     - **#11 LLM provider:** Provider-agnostic adapter, Azure OpenAI default, `LLM_PROVIDER` env var.
     - **#14 Message bus:** In-process Python events (no external bus in Phase 1).
   - We will adapt the implementation if the team later chooses different options and documents them in ADRs.

2. Optionally, in `ARCHITECTURAL_DECISIONS.md`, set **Status** for #11 and #14 to something like “✅ Confirmed for Week 2 (reference)” and add a line: “Week 2 implementation uses reference; full ADR deferred.”

3. Mark the TODO item done: “Week 2 ADRs — confirmed reference for #11, #14; no alternative chosen.”

**You do *not* need to write full ADR documents if you’re not evaluating alternatives.**

---

### Option B — Write ADRs (full)

**Use when:** The team is supposed to evaluate alternatives and record a formal decision (with rationale).

**What to do:**

1. **Create** `docs/adr/` (if it doesn’t exist).

2. **For each Week 2–relevant SA decision** (#11, and #14; optionally #13):
   - Create the file listed in ARCHITECTURAL_DECISIONS (e.g. `docs/adr/ADR-011-llm-provider-strategy.md`, `docs/adr/ADR-014-message-bus.md`).
   - In each ADR include:
     - **Context** — why we need this decision.
     - **Options** — from the tracker (e.g. provider-agnostic vs fixed provider for #11).
     - **Evaluation** — use the “Evaluation Criteria” from ARCHITECTURAL_DECISIONS.
     - **Decision** — what you chose (e.g. “Provider-agnostic adapter, Azure default”).
     - **Consequences** — what this means for env vars, testing, future providers.
   - Even if you choose the **reference** implementation, the ADR must explain *why* (e.g. vendor flexibility, testing without live keys). “The spec said so” is not enough.

3. **Update** `ARCHITECTURAL_DECISIONS.md`: set **Status** to “✅ Resolved” and fill **Decision Made** for those decisions.

4. Mark the TODO item done: “Week 2 ADRs — ADR-011 and ADR-014 written; decisions recorded.”

---

## Recommendation

- **Solo or “just get Week 2 done”:** Use **Option A**. Add a short “Week 2 technology choices” note that confirms reference for #11 and #14, and tick the TODO.
- **Team / curriculum requires ADRs:** Use **Option B**. Create `docs/adr/`, write ADR-011 and ADR-014 (and optionally ADR-013), then update the tracker and the TODO.

---

## Where to put the “confirmation” (Option A)

You can add a small file, e.g.:

- **`agents/docs/WEEK2_TECH_CHOICES.md`** — “Week 2 uses reference implementation for #11 (LLM adapter), #14 (in-process events). No ADR written; will adapt if team selects different tech and documents in docs/adr/.”

Or add a **subsection** under “Documentation & decisions” in `TODO_WEEK2_DELIVERABLES.md`:

- “Week 2 ADRs: Confirmed reference for #11, #14. Full ADRs in docs/adr/ when team evaluates alternatives.”

---

## Summary

| Question | Answer |
|----------|--------|
| Do I have to write code? | No. This is docs/decisions only. |
| Do I have to write full ADR files? | Only if the team/curriculum requires it (Option B). Otherwise, a short confirmation is enough (Option A). |
| Which decisions? | #11 (LLM provider) and #14 (message bus) are clearly Week 2–relevant; #13 can be noted as “deferred to Week 6.” |
| What does “converge” mean? | The team has a clear, documented choice so implementation and future work align. |
| Where do ADRs go? | `docs/adr/`, with filenames like `ADR-011-llm-provider-strategy.md` (see ARCHITECTURAL_DECISIONS). |

Once you’ve either (A) added the confirmation or (B) written the ADRs and updated the tracker, you can mark the TODO item **Week 2 ADRs** as done.
