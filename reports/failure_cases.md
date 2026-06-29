# Failure Cases — TENDER-TIMELINE Public-Dev MVP

These are illustrative benchmark failures exposed by the deterministic grader. They are not real tribunal outcomes.

## Failure Case 1 — Correct arithmetic, wrong clause

**Item:** `tt_item_002_bid_security_short`

**Expected:**

- Addendum 2 controls the submission deadline
- Operative deadline: 14 June 2026, 10:00 EAT
- Required bid security valid through: 9 November 2026
- Submitted bid security valid through: 6 November 2026
- Verdict: INVALID
- Failure code: `INSUFFICIENT_BID_SECURITY_VALIDITY`

**Bad model behavior:**

- Uses base Tender Data Sheet deadline of 10 June 2026
- Computes required security through 5 November 2026
- Treats submitted 6 November 2026 as sufficient
- Returns VALID with citation to the Tender Data Sheet only

**Lesson:**

> Arithmetic is not enough. The model must propagate the amendment through the event graph.

## Failure Case 2 — Wrong procedural rule

**Item:** `tt_item_004_gao_solicitation_impropriety_late`

**Expected:**

- Apparent solicitation impropriety visible before proposal deadline
- Governing rule: `4 CFR §21.2(a)(1)`
- Protest must be filed before the proposal deadline
- Verdict: INVALID

**Bad model behavior:**

- Applies the 10-day known-basis rule (`4 CFR §21.2(a)(2)`) instead
- Computes a later deadline unrelated to the solicitation receipt time
- May still return INVALID, but for the wrong legal/document reason

**Lesson:**

> Procedural compliance requires selecting the correct rule, not just returning a plausible INVALID label.

## Failure Case 3 — Valid control item

**Item:** `tt_item_003_valid_control`

**Expected:**

- Timely submission under Addendum 2 deadline
- Bid security valid through 10 November 2026 (required through 9 November 2026)
- Verdict: VALID
- Failure code: `VALID`

**Why it matters:**

Valid controls prevent models from learning a shortcut of always predicting INVALID. A serious benchmark must include both trap failures and correctly satisfied controls.

**Lesson:**

> Benchmark quality depends on label balance and controls, not only on catching errors.

## Failure Case 4 — Real model: cascade error despite correct addendum (Azure gpt-5.4-nano)

**Item:** `tt_item_002_bid_security_short`  
**Prompt:** `event_graph_first`  
**Source:** Real Azure OpenAI output (`baselines/outputs/azure_gpt54nano_event_graph_outputs.jsonl`)

**Expected:**

- Addendum 2 deadline: 14 June 2026
- Required bid security through: 9 November 2026
- Submitted through: 6 November 2026
- Verdict: **INVALID**

**Observed model behavior:**

- Used operative deadline **14 June 2026** (addendum applied)
- Computed required/submitted through **6 November 2026** for both fields
- Returned **VALID** / `VALID`

**Lesson:**

> Even when a model applies the amendment deadline, it can still fail the dependent validity cascade and return a false VALID. This is the strongest substantive failure in the real Azure evaluation.
