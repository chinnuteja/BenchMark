# Contributing to TENDER-TIMELINE

Thank you for helping improve this evaluation benchmark.

## Install

```bash
pip install -e ".[dev]"
```

Optional provider SDKs for real model runs:

```bash
pip install -e ".[providers]"
```

Copy `.env.example` to `.env` and add API keys locally. **Never commit `.env`.**

## Add a new benchmark item

1. Add or update document family markdown under `data/public_dev/documents/`.
2. Create a JSON file in `data/public_dev/items/` following the `TenderTimelineItem` schema.
3. Include `grading.required_clause_keywords` and `data_version: public_dev_v0.1`.
4. Validate:

```bash
python -m tender_timeline.validate_items --items data/public_dev/items
```

5. Add or update tests if the item introduces new grading behavior.

## Run tests

```bash
pytest
```

Or:

```bash
make test
```

## Run the full local demo (fake/sample pipeline)

```bash
make demo
```

This validates items, runs tests, grades sample predictions, and writes `reports/mini_eval_report.md`.

## Data and legal disclaimer

Public-dev items are simplified and perturbed for AI evaluation research. They are **not legal advice** and must not be used for real procurement decisions.

Fake/sample outputs (`provider=fake`) are for pipeline validation only and must not be presented as real frontier model results.
