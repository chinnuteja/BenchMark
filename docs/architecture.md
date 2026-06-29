# Architecture — TENDER-TIMELINE MVP

## Pipeline flow

```text
Item JSON + documents
       ↓
Prompt builder (prompts.py)
       ↓
Model / fake provider (providers.py)
       ↓
Raw output (JSONL record)
       ↓
JSON parser (utils.extract_json_from_text)
       ↓
Schema normalization (schema.py, normalize.py)
       ↓
Deterministic grader (grader.py)
       ↓
Metrics + report (grade.py, report.py)
```

## Layer responsibilities

### Item JSON + documents

Machine-readable benchmark items (`data/public_dev/items/`) reference markdown document families. Each item stores the task, expected answer, grading spec, trap description, and perturbation certificate.

### Prompt builder

`build_prompt()` loads the prompt template (`naive`, `clause_first`, or `event_graph_first`), injects item metadata, task JSON, and full document text. This keeps evaluation reproducible and separates data from prompt wording.

### Model / fake provider

`call_model()` abstracts Azure OpenAI, OpenAI, Anthropic, Google, and a deterministic **fake** provider. Fake outputs are labeled `is_fake_sample_output` and are for pipeline validation only.

### Raw output

Every run saves `raw_output`, `parsed_prediction`, `parse_error`, latency, and provider metadata to JSONL. Raw outputs are never discarded.

### JSON parser

Models may wrap JSON in prose or fenced blocks. `extract_json_from_text()` tries full parse, fenced `json` blocks, then first `{`…`}` span.

### Schema normalization

Pydantic validates answers; `normalize.py` handles enum casing, ISO datetimes, and clause text normalization for robust matching.

### Procedural oracle

`calculator.py` computes the operative deadline, bid-security validity cascade, protest window, and
verdict from each item's `compute_spec` + demo calendar. It backs the `--verify-gold` gate (authored gold
must equal oracle output) and feeds failure attribution. Gold is derived, not hand-trusted.

### Deterministic grader + attribution

`grade_prediction()` scores verdict, failure code, deadlines, clause grounding, and strict pass/fail.
**Clause grounding gates strict credit** — correct verdict from wrong clause still fails strict scoring.
`attribution.py` then localizes *which* reasoning step broke (`CASCADE_ARITHMETIC_ERROR`,
`WRONG_CONTROLLING_DEADLINE`, `WRONG_RULE_SELECTION`, …) with predicted-vs-computed evidence, attached to
each result as `failure_attribution` / `attribution_detail`.

### Metrics + report

`grade.py` aggregates per-item scores into summary metrics, including **paired consistency** (matched
INVALID/VALID control pairs) and **right-reason accuracy** (`consistency.py`). `report.py` writes Markdown
reports with a failure-attribution breakdown and a data-driven strongest-failure section; `aggregate.py`
builds a model × prompt leaderboard across all graded baselines.
