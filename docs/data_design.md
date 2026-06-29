# Data Design — TENDER-TIMELINE

## Item families

Three public-dev families:

| Family | File | Focus |
|--------|------|-------|
| Kenya-style bid security | `family_kenya_bid_security.md` | Addenda, submission deadlines, bid-security validity cascade |
| GAO-style protest timeliness | `family_gao_timeliness.md` | Apparent impropriety vs 10-day known-basis rules |
| Uganda-style admin review | `family_uganda_admin_review.md` | Calendar-day filing windows |

Six items span these families, including valid controls (`tt_item_003`, `tt_item_005`).

## Public-dev vs private held-out split

**Public-dev (`public_dev_v0.1`)** — small, perturbed, repo-visible set for calibration, grader development, and demonstration.

**Future private split** — expert-QA'd items derived from seed rulings, held out from training and public repos to reduce contamination.

## Seed-family splitting

Fellowship-scale design groups items by procedural pattern (seed family), then perturbs dates, party labels, and action logs while preserving invariant legal mechanics. Perturbation certificates document allowed vs prohibited variable changes per item.

## Perturbation concept

Each item includes a `perturbation_certificate` listing:

- allowed variables (e.g., submission timestamp)
- prohibited variables (e.g., changing bid validity rule)
- invariant assumptions (e.g., Addendum 2 controls deadline)

## Clause grounding

Items declare `grading.required_clause_keywords`. The grader checks substring presence in `governing_clause_id` and `citation` (with harmless spacing normalization). This catches “right answer, wrong clause” failures.

## Valid controls

Items like `tt_item_003_valid_control` ensure models cannot succeed by always predicting INVALID. Controls are essential for label balance.

## Why the MVP is small

Six items prove representability, grading, baselines, and failure analysis — not statistical power. The fellowship version targets 150–300 expert-QA'd items across 40–60 seed patterns.
