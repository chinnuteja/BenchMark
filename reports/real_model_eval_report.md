# TENDER-TIMELINE Real Model Evaluation Report

## What TENDER-TIMELINE Tests

TENDER-TIMELINE evaluates whether models can verify procedural compliance in procurement documents: controlling clauses, amended deadlines, validity periods, protest windows, and structured JSON answers.

## Dataset Summary

- Public-dev items: 6
- Document families: 3
- Data version: public_dev_v0.1

## Baselines Run

- `azure_gpt54nano_naive` (baselines\outputs\azure_gpt54nano_naive_grade_results.json)
- `azure_gpt54nano_clause_first` (baselines\outputs\azure_gpt54nano_clause_first_grade_results.json)
- `azure_gpt54nano_event_graph` (baselines\outputs\azure_gpt54nano_event_graph_grade_results.json)
- `openai_gpt55_naive` (baselines\outputs\openai_gpt55_naive_grade_results.json)
- `openai_gpt55_clause_first` (baselines\outputs\openai_gpt55_clause_first_grade_results.json)
- `openai_gpt55_event_graph_first` (baselines\outputs\openai_gpt55_event_graph_first_grade_results.json)

> These are real model outputs from live API calls. Provider and model are recorded in each JSONL record.

## Metrics

| Baseline | Strict Accuracy | Verdict Accuracy | Failure Code Accuracy | Clause Grounding | Paired Consistency | Right-Reason | Parse Error Rate |
|---|---:|---:|---:|---:|---:|---:|---:|
| azure_gpt54nano_naive | 0.6667 | 1.0000 | 0.6667 | 0.8333 | 1.0000 | 0.5000 | 0.0000 |
| azure_gpt54nano_clause_first | 0.6667 | 1.0000 | 0.6667 | 1.0000 | 1.0000 | 0.5000 | 0.0000 |
| azure_gpt54nano_event_graph | 0.6667 | 0.8333 | 0.6667 | 1.0000 | 0.5000 | 0.5000 | 0.0000 |
| openai_gpt55_naive | 0.8333 | 1.0000 | 0.8333 | 0.8333 | 1.0000 | 0.8333 | 0.0000 |
| openai_gpt55_clause_first | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 0.0000 |
| openai_gpt55_event_graph_first | 0.8333 | 1.0000 | 0.8333 | 1.0000 | 1.0000 | 0.8333 | 0.0000 |

## Failure-Mode Breakdown

### azure_gpt54nano_naive
- `missing_required_clause`: 2
- `wrong_failure_reason_code`: 2
- `wrong_clause_grounding`: 1
- `wrong_governing_clause_id`: 1

### azure_gpt54nano_clause_first
- `wrong_failure_reason_code`: 2

### azure_gpt54nano_event_graph
- `wrong_failure_reason_code`: 2
- `wrong_verdict`: 1

### openai_gpt55_naive
- `missing_required_clause`: 1
- `wrong_clause_grounding`: 1
- `wrong_failure_reason_code`: 1
- `wrong_governing_clause_id`: 1

### openai_gpt55_clause_first
- No recorded errors.

### openai_gpt55_event_graph_first
- `wrong_failure_reason_code`: 1

## Failure-Attribution Breakdown

Oracle-driven diagnosis: which procedural reasoning step each prediction got wrong.

### azure_gpt54nano_naive
- `CASCADE_ARITHMETIC_ERROR`: 2
- `WRONG_FAILURE_CODE`: 2
- `CLAUSE_GROUNDING_FAILURE`: 1

### azure_gpt54nano_clause_first
- `CASCADE_ARITHMETIC_ERROR`: 2
- `WRONG_FAILURE_CODE`: 2

### azure_gpt54nano_event_graph
- `CASCADE_ARITHMETIC_ERROR`: 2
- `WRONG_FAILURE_CODE`: 2
- `WRONG_VERDICT`: 1

### openai_gpt55_naive
- `CLAUSE_GROUNDING_FAILURE`: 1
- `WRONG_FAILURE_CODE`: 1

### openai_gpt55_clause_first
- No recorded attributions.

### openai_gpt55_event_graph_first
- `WRONG_FAILURE_CODE`: 1

## Strongest Substantive Failure

**azure_gpt54nano_event_graph / tt_item_002_bid_security_short** — Correct controlling deadline but miscalculated the bid-security cascade. [`CASCADE_ARITHMETIC_ERROR`] (evidence: predicted_required=2026-11-06, computed_required=2026-11-09) This is a competent-looking procedural failure, mechanically diagnosed by the oracle rather than hand-written.

## Failure Classification

### Substantive procedural failures

- **azure_gpt54nano_naive / tt_item_002_bid_security_short** (substantive): Prediction did not ground answer in required controlling clause keywords.; Failure reason code does not match expected classification.
- **azure_gpt54nano_event_graph / tt_item_002_bid_security_short** (substantive): Verdict does not match expected procedural outcome.; Failure reason code does not match expected classification.
- **openai_gpt55_naive / tt_item_002_bid_security_short** (substantive): Prediction did not ground answer in required controlling clause keywords.; Failure reason code does not match expected classification.

### Formatting / taxonomy / schema failures

- **azure_gpt54nano_naive / tt_item_002_bid_security_short** (also formatting/taxonomy): Prediction did not ground answer in required controlling clause keywords.; Failure reason code does not match expected classification.
- **azure_gpt54nano_naive / tt_item_006_uganda_admin_review_late** (formatting/taxonomy): Failure reason code does not match expected classification.
- **azure_gpt54nano_clause_first / tt_item_002_bid_security_short** (formatting/taxonomy): Failure reason code does not match expected classification.
- **azure_gpt54nano_clause_first / tt_item_006_uganda_admin_review_late** (formatting/taxonomy): Failure reason code does not match expected classification.
- **azure_gpt54nano_event_graph / tt_item_002_bid_security_short** (also formatting/taxonomy): Verdict does not match expected procedural outcome.; Failure reason code does not match expected classification.
- **azure_gpt54nano_event_graph / tt_item_006_uganda_admin_review_late** (formatting/taxonomy): Failure reason code does not match expected classification.
- **openai_gpt55_naive / tt_item_002_bid_security_short** (also formatting/taxonomy): Prediction did not ground answer in required controlling clause keywords.; Failure reason code does not match expected classification.
- **openai_gpt55_event_graph_first / tt_item_002_bid_security_short** (formatting/taxonomy): Failure reason code does not match expected classification.

## What This Shows

The benchmark exposes failures where models appear competent but ground answers in the wrong clause, miss addendum-controlled deadlines, or apply the wrong procedural rule.

## Limitations

- Public-dev demo items only; not legal advice.
- Results reflect real model deployments on the public-dev MVP slice.
- Six items is an MVP slice, not a production benchmark size.

## Fellowship-Scale Next Steps

- Expand item families with perturbation certificates and expert QA.
- Run a real model × prompt matrix (OpenAI, Anthropic, Google).
- Add held-out private evaluation and richer failure taxonomy.
