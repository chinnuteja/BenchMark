# Application Summary

TENDER-TIMELINE is a benchmark for testing whether frontier models can verify procedural compliance in international government procurement.

## What the public MVP demonstrates

- JSON benchmark items with expected structured answers
- Deterministic grading with multiple metrics
- Clause-grounding gate (strict credit requires correct controlling clause)
- Three prompt baselines: `naive`, `clause_first`, `event_graph_first`
- Fake/sample pipeline outputs for reproducible demo runs
- Real Azure OpenAI (`gpt-5.4-nano`) evaluation across all three prompts (18 records, zero parse errors)
- Failure analysis separating substantive procedural errors from formatting/taxonomy issues

## Strongest real-model failure observed

On `tt_item_002_bid_security_short` with the `event_graph_first` prompt, Azure `gpt-5.4-nano` used the **Addendum 2-controlled June 14 deadline** but miscalculated the bid-security validity cascade and returned **VALID** instead of **INVALID**. This is arithmetic from an partially correct event graph — a substantive compliance failure, not a JSON formatting issue.

## Fellowship-scale plan

- 40–60 real procedural seed rulings
- 150–300 expert-QA'd items
- Private held-out evaluation split
- Perturbation validity certificates with expert review
- Frontier-model evaluation across providers and prompt styles

## Key design insight

> Models can compute internally consistent arithmetic from a displaced or incomplete controlling clause. TENDER-TIMELINE grades the full procedural chain: clause → deadline → dependent validity → verdict.

## Disclaimer

Evaluation research only. Not legal advice. Public-dev data is simplified and perturbed.
