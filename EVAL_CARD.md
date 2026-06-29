# EVAL CARD — TENDER-TIMELINE MVP

## Evaluated capability

Procedural compliance verification under amendments, deadlines, calendars, and preconditions.

## Non-goals

Not legal advice. Not broad legal QA. Not model training.

## Metrics

- strict accuracy
- verdict accuracy
- failure-code accuracy
- clause-grounding accuracy
- paired consistency (matched INVALID/VALID control pairs both correct)
- right-reason accuracy (strict pass with no construct-relevant attribution)
- parse-error rate

## Grading rule

Clause grounding gates strict credit. A model can fail strict scoring even if the final verdict is correct but the controlling clause is wrong.

## Gold derivation (construct validity)

Gold answers are computed from rule parameters by a deterministic procedural oracle
(`tender_timeline/calculator.py`), not hand-trusted. A `--verify-gold` CI gate asserts the authored
`expected_answer` matches the oracle for operative deadline, required bid-security date, verdict, and
failure code on all items.

## Failure attribution

Every graded item carries a `failure_attribution` list with oracle-driven categories that localize the
broken reasoning step, each with evidence (predicted vs computed):

- `WRONG_CONTROLLING_DEADLINE` — used the displaced base deadline instead of the addendum-controlled one
- `CASCADE_ARITHMETIC_ERROR` — correct controlling deadline but wrong dependent validity cascade
- `WRONG_RULE_SELECTION` — applied the wrong protest-timeliness subsection
- `WRONG_OPERATIVE_DEADLINE` — operative deadline on the wrong day (not a controlling-clause error)
- `DEADLINE_PRECISION_MISMATCH` — right date, off on time-of-day precision
- `CLAUSE_GROUNDING_FAILURE`, `WRONG_VERDICT`, `WRONG_FAILURE_CODE`, `PARSE_ERROR`

## Baselines

- naive
- clause_first
- event_graph_first

## Reward-hacking / shortcut detection

Paired consistency uses matched contrast groups (an INVALID item and its VALID control differing only in
the decisive fact). A model that pattern-matches a family to one verdict scores well on verdict accuracy
but poorly on paired consistency. Example: Azure gpt-5.4-nano `event_graph_first` holds verdict accuracy
0.83 but paired consistency drops to 0.50 on the Kenya pair.

## Failure analysis

The benchmark highlights failures such as using a displaced base deadline instead of an
addendum-controlled deadline, and — more subtly — correct clause + correct deadline but a miscalculated
dependent validity cascade that flips the verdict (the Item 002 `CASCADE_ARITHMETIC_ERROR` hero case).

## Validity threats

Small public-dev dataset (6 items), demo facts, `demo_self_reviewed` (no expert QA yet), and two real
deployments so far (`azure/gpt-5.4-nano`, `openai/gpt-5.5`). Oracle verification covers structured
fields, not free-text citation derivation. Running `gpt-5.5` surfaced — and we then fixed — an end-of-day
grading artifact (Item 005: `23:59:59` vs gold `23:59:00`); the grader now treats end-of-day
`23:59:00`–`23:59:59` as equivalent. See README.

## Fellowship-scale improvements

Expert QA, perturbation certificates, private held-out split, more jurisdictions, frontier-model evaluation.
