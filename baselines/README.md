# Baselines

This directory contains prompt templates and saved model outputs for TENDER-TIMELINE.

## Prompt styles

Three distinct prompt templates are used — do not collapse them into a generic "structured" prompt:

| Prompt | File | Intent |
|--------|------|--------|
| `naive` | `prompts/naive.md` | Minimal instruction; JSON only |
| `clause_first` | `prompts/clause_first.md` | Identify controlling clause/addendum before deciding validity |
| `event_graph_first` | `prompts/event_graph_first.md` | Build an internal event graph (base rule → amendment → deadline → action → verdict); JSON only |

## Output format

Each run writes JSONL records with:

- `item_id`, `provider`, `model`, `prompt_name`, `prompt_path`
- `raw_output`, `parsed_prediction`, `parse_error`
- `latency_ms`, `usage`, `data_version`

Fake runs also include `is_fake_sample_output: true`.

## Fake vs real outputs

**Fake outputs** (`provider=fake`, `model=fake-v1`) are deterministic sample predictions for pipeline validation. They are labeled fake/sample and must never be presented as real frontier model results.

**Real outputs** require API keys and optional provider packages:

```bash
pip install -e ".[providers]"
```

Supported real providers: `azure` (Azure OpenAI), `openai`, `anthropic`, `google`.

Example:

```bash
python -m tender_timeline.run_model \
  --provider openai \
  --model gpt-4.1 \
  --prompt baselines/prompts/naive.md \
  --items data/public_dev/items \
  --out baselines/outputs/openai_gpt41_naive_outputs.jsonl
```

## Fake baseline files

- `outputs/fake_naive_outputs.jsonl`
- `outputs/fake_clause_first_outputs.jsonl`
- `outputs/fake_event_graph_outputs.jsonl`

Corresponding grade results:

- `outputs/fake_naive_grade_results.json`
- `outputs/fake_clause_first_grade_results.json`
- `outputs/fake_event_graph_grade_results.json`
