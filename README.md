# TENDER-TIMELINE

A public-dev MVP for a frontier-LLM benchmark on procedural compliance in international government procurement.

## One-sentence summary

TENDER-TIMELINE tests whether models can construct and verify legally operative event graphs under addenda, deadlines, calendars, and preconditions.

## Real-model results summary (two deployments)

Two real OpenAI-family models, three prompts each (18 + 18 live records, zero parse errors).

**Azure `gpt-5.4-nano`** (weaker / contrast model):

| Prompt | Strict | Verdict | Failure Code | Clause | Paired Consist. | Right-Reason |
|--------|-------:|--------:|-------------:|-------:|----------------:|-------------:|
| naive | 0.67 | 1.00 | 0.67 | 0.83 | 1.00 | 0.50 |
| clause_first | 0.67 | 1.00 | 0.67 | 1.00 | 1.00 | 0.50 |
| event_graph_first | 0.67 | 0.83 | 0.67 | 1.00 | **0.50** | 0.50 |

**OpenAI `gpt-5.5`** (frontier model):

| Prompt | Strict | Verdict | Failure Code | Clause | Paired Consist. | Right-Reason |
|--------|-------:|--------:|-------------:|-------:|----------------:|-------------:|
| naive | 0.83 | 1.00 | 0.83 | 0.83 | 1.00 | 0.83 |
| clause_first | **1.00** | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 |
| event_graph_first | 0.83 | 1.00 | 1.00 | 1.00 | 1.00 | 0.83 |

**The benchmark discriminates.** `gpt-5.4-nano` falls into the Kenya bid-security cascade trap — on
`event_graph_first` it grounds all three clauses and uses the Addendum 2 deadline but miscalculates the
cascade (`Nov 6` vs `Nov 9`), returns **VALID**, and `paired_consistency` drops to **0.50**
(auto-tagged `CASCADE_ARITHMETIC_ERROR`). `gpt-5.5` **solves that trap** on every prompt — verdict 1.00,
paired consistency 1.00 throughout — and reaches a clean **1.00 strict on `clause_first`**.

**What gpt-5.5 still trips on (honest residuals, all on Item 002):**
- **Failure-code taxonomy** — it understands the defect but labels it `BID_SECURITY_VALIDITY_TOO_SHORT`
  instead of the canonical `INSUFFICIENT_BID_SECURITY_VALIDITY` (taxonomy, not reasoning).
- **A missed clause keyword** on `naive` (omits "Addendum 2" from its grounding).

> Note: running `gpt-5.5` surfaced — and we then fixed — an end-of-day grading artifact on Item 005
> (`23:59:59` vs gold `23:59:00`). The grader now treats end-of-day `23:59:00`–`23:59:59` as equivalent;
> see Limitations. The tables above reflect the corrected grader.

Full report: `reports/real_model_eval_report.md`; cross-model table: `reports/leaderboard.md`.

## Core failure case (Item 002)

Base Tender Data Sheet deadline: **10 June 2026**. Addendum 2 extends submission to **14 June 2026**. Bid validity runs 120 calendar days from the controlling deadline; bid security must remain valid 28 days beyond that (ITB 18.1 + ITB 19.3).

Bidder submits on 14 June with bid security through **6 November 2026**. Required through date under Addendum 2: **9 November 2026** → **INVALID** (`INSUFFICIENT_BID_SECURITY_VALIDITY`).

If a model uses the base June 10 deadline, required through becomes 5 November and 6 November looks sufficient → false **VALID**. The benchmark catches this with strict grading and clause grounding.

## Why this exists

Frontier models can sound legally fluent while using the wrong controlling clause or outdated deadline. Procurement compliance often turns on exact procedural validity, not broad summarization.

## What the MVP contains

- 6 public-dev benchmark items across 3 document families
- Pydantic schemas and item validation CLI
- **Procedural oracle** (`calculator.py`) that *computes* gold answers from rule parameters + demo calendars, plus a **`--verify-gold` CI gate** that proves authored gold matches the oracle
- Deterministic grader with clause-grounding gate **and oracle-driven failure attribution** (e.g. `CASCADE_ARITHMETIC_ERROR`, `WRONG_CONTROLLING_DEADLINE`, `WRONG_RULE_SELECTION`)
- **Shortcut/consistency metrics**: paired-item consistency (matched INVALID/VALID controls) and "right-reason" accuracy
- Three prompt templates: `naive`, `clause_first`, `event_graph_first`
- **Aggregate leaderboard CLI** and a one-command **model × prompt matrix runner**
- Fake/sample pipeline outputs and real Azure OpenAI evaluation artifacts
- Mini evaluation reports (with attribution + paired consistency) and failure-case documentation
- 117 automated tests and GitHub Actions CI (lint → validate → verify-gold → test → grade → leaderboard)

## Quickstart

```bash
pip install -e ".[dev]"
make demo
```

Or step by step:

```bash
pip install -e ".[dev]"
pytest
python -m tender_timeline.validate_items --items data/public_dev/items --verify-gold
python -m tender_timeline.grade \
  --items data/public_dev/items \
  --predictions baselines/outputs/sample_model_outputs.jsonl \
  --out reports/sample_grade_results.json
python -m tender_timeline.report \
  --grade-results reports/sample_grade_results.json \
  --out reports/mini_eval_report.md
python -m tender_timeline.aggregate \
  --results-dir baselines/outputs \
  --out reports/leaderboard.md
```

### Demo output (actual)

```text
Loaded 6 items
All items valid
All gold answers verified
============================= 117 passed in ~7s =============================
Wrote grade results to .../reports/sample_grade_results.json
Wrote evaluation report
Wrote leaderboard
Demo complete. See reports/mini_eval_report.md and reports/leaderboard.md
```

## Procedural oracle and gold verification

Gold answers are not hand-trusted constants. `tender_timeline/calculator.py` computes the operative
deadline, bid-security validity cascade, protest window, and verdict directly from each item's
`compute_spec` (rule parameters) + demo calendar. The `--verify-gold` gate recomputes every item and
asserts the authored `expected_answer` matches the oracle (operative deadline, required bid-security
date, verdict, failure code) — and runs in CI:

```bash
python -m tender_timeline.validate_items --items data/public_dev/items --verify-gold
# → All gold answers verified
```

## Grading

```bash
python -m tender_timeline.grade \
  --items data/public_dev/items \
  --predictions <outputs.jsonl> \
  --out <grade_results.json>
```

Metrics:

| Metric | Meaning |
|--------|---------|
| **Strict accuracy** | All strict fields + clause grounding pass |
| **Verdict accuracy** | VALID/INVALID match |
| **Failure-code accuracy** | `failure_reason_code` match |
| **Clause-grounding accuracy** | Required clause keywords present |
| **Paired consistency** | Fraction of matched INVALID/VALID control pairs the model gets right on *both* members (exposes always-INVALID pattern-matching that verdict accuracy hides) |
| **Right-reason accuracy** | Strict pass *and* no construct-relevant attribution (cascade error, wrong rule, wrong controlling deadline, clause-grounding failure) |
| **Parse-error rate** | Fraction of unparseable outputs |

**Clause-grounding gate:** a model that returns the correct verdict from the wrong controlling clause can still fail strict grading.

Each graded item also carries a `failure_attribution` list (oracle-driven diagnosis of *which* reasoning step broke) and `attribution_detail` with evidence (predicted vs computed).

See `EVAL_CARD.md`.

## Leaderboard and matrix runner

Aggregate any directory of `*_grade_results.json` into a model × prompt leaderboard:

```bash
python -m tender_timeline.aggregate --results-dir baselines/outputs --out reports/leaderboard.md
```

Run all three prompts for one provider/model in a single command:

```bash
python -m tender_timeline.run_matrix \
  --provider anthropic --model claude-sonnet-4-6 \
  --items data/public_dev/items
```

## Run baselines

### Fake/sample pipeline (no API keys)

Clearly labeled `provider=fake` — **not real model results**:

```bash
python -m tender_timeline.run_model \
  --provider fake --model fake-v1 \
  --prompt baselines/prompts/naive.md \
  --items data/public_dev/items \
  --out baselines/outputs/fake_naive_outputs.jsonl

python -m tender_timeline.grade \
  --items data/public_dev/items \
  --predictions baselines/outputs/fake_naive_outputs.jsonl \
  --out baselines/outputs/fake_naive_grade_results.json
```

See `baselines/README.md` for all three prompt styles.

### Real model evaluation (Azure OpenAI)

This repo includes **real** outputs from Azure OpenAI deployment `gpt-5.4-nano` across all three prompts (18 JSONL records, zero parse errors). See `reports/real_model_eval_report.md`.

```bash
# Requires .env with AZURE_OPENAI_* variables (never commit .env)
python -m tender_timeline.run_model \
  --provider azure --model gpt-5.4-nano \
  --prompt baselines/prompts/naive.md \
  --items data/public_dev/items \
  --out baselines/outputs/azure_gpt54nano_naive_outputs.jsonl
```

## Data

Public-dev data (`data/public_dev/`) is simplified and perturbed for evaluation research. See `DATA_CARD.md` and `docs/data_design.md`.

- `data/public_dev/items/` — 6 benchmark JSON items
- `data/public_dev/documents/` — 3 document families
- `data/public_dev/calendars/` — demo calendars (not official legal calendars)

## Reports

| Report | Contents |
|--------|----------|
| `reports/mini_eval_report.md` | Fake/sample pipeline demo metrics + attribution |
| `reports/real_model_eval_report.md` | Real Azure evaluation, attribution breakdown, oracle-diagnosed strongest failure |
| `reports/leaderboard.md` | Model × prompt leaderboard across all graded baselines |
| `reports/failure_cases.md` | Annotated failure patterns |

## Limitations

This MVP is **not statistically powered**; it is a proof-of-mechanics showing the benchmark can be represented, run, graded, and analyzed.

- 6 public-dev items only
- Demo/perturbed facts, not expert-QA'd seed rulings
- Two real model deployments documented so far (`azure/gpt-5.4-nano`, `openai/gpt-5.5`)
- Some failures are formatting/taxonomy (non-canonical failure codes, sub-minute deadline precision)

### Benchmark artifact found and fixed (surfaced by `gpt-5.5`)

Running `gpt-5.5` exposed a grading artifact: Item 005's gold operative deadline is `…T23:59:00`, but
the model answered `…T23:59:59`. The rule text only says "expires at 23:59", so both are defensible
end-of-day readings — yet the original strict grader marked it failed (for *both* models, which gave the
same `23:59:59`). This was a **label/convention artifact, not a reasoning error**. We fixed it:
`normalize.date_or_datetime_equal` now treats end-of-day times `23:59:00`–`23:59:59` on the same date and
offset as equivalent, and the attribution layer distinguishes a genuine wrong deadline
(`WRONG_OPERATIVE_DEADLINE`) from a sub-day precision slip (`DEADLINE_PRECISION_MISMATCH`). `verify-gold`
still passes and all metrics above reflect the corrected grader. This audit-and-fix loop is the
science-of-evals workflow the benchmark is built to support.

> The key exposed failure is not arithmetic failure alone, but arithmetic performed from a displaced or incomplete controlling clause.

## Fellowship-scale plan

- 40–60 procedural seed rulings
- 150–300 expert-QA'd items
- Private held-out split
- Perturbation validity certificates
- Multi-provider frontier evaluation

See `docs/application_summary.md`.

## Documentation

- `docs/architecture.md` — pipeline design
- `docs/data_design.md` — families, perturbation, controls
- `CONTRIBUTING.md` — how to contribute
- `RELEASE_CHECKLIST.md` — release verification

## Disclaimer

> This repository contains public-dev benchmark examples for AI evaluation research. The examples are simplified and/or perturbed and are **not legal advice**. They should not be used to decide real procurement disputes.

## License

See repository license file when published.
