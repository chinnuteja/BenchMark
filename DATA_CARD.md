# DATA CARD — TENDER-TIMELINE public_dev_v0.1

## Dataset purpose

This public-dev set demonstrates the mechanics of a benchmark for procedural compliance in procurement documents.

## Dataset size

6 items, 3 document families.

## Data type

Simplified and perturbed procedural procurement demo items.

## Source inspiration

Kenya-style procurement review patterns, GAO-style bid protest timeliness, and Uganda-style administrative review deadlines.

## Public-dev vs future private test

The public-dev set is for calibration and repo demonstration. The fellowship-scale benchmark would use expert-reviewed seed rulings and private held-out item families.

## Label schema

Each item has a verdict, failure reason code, controlling clause, operative deadline, and citation fields.

## Oracle-derived gold and contrast pairs

Each item carries a `compute_spec` (rule parameters: base/addendum deadlines, validity and
bid-security day counts, protest subtype, window length, calendar id). The procedural oracle
(`tender_timeline/calculator.py`) recomputes the gold operative deadline, bid-security cascade,
verdict, and failure code from this spec; `--verify-gold` asserts the authored answers match
(verified in CI for all 6 items). Matched items are tagged with a `contrast_group`
(`kenya_bid_security_pair`: 002 INVALID ↔ 003 VALID; `gao_timeliness_pair`: 004 INVALID ↔ 005 VALID)
so the grader can measure paired consistency and detect verdict pattern-matching.

## Known limitations

Small, demo-only, not statistically powered, not legal advice. Oracle verification currently covers
operative deadline, required bid-security date, verdict, and failure code (not full free-text citation
derivation). `review_status` is `demo_self_reviewed`, not expert-QA'd.

## Ethical/legal note

Do not use for real procurement decisions.
