install:
	pip install -e ".[dev]"

test:
	pytest

lint:
	ruff check tender_timeline tests

validate:
	python -m tender_timeline.validate_items --items data/public_dev/items

verify-gold:
	python -m tender_timeline.validate_items --items data/public_dev/items --verify-gold

grade-sample:
	python -m tender_timeline.grade --items data/public_dev/items --predictions baselines/outputs/sample_model_outputs.jsonl --out reports/sample_grade_results.json

run-fake-naive:
	python -m tender_timeline.run_model --provider fake --model fake-v1 --prompt baselines/prompts/naive.md --items data/public_dev/items --out baselines/outputs/fake_naive_outputs.jsonl

report-sample:
	python -m tender_timeline.report --grade-results reports/sample_grade_results.json --out reports/mini_eval_report.md

aggregate:
	python -m tender_timeline.aggregate --results-dir baselines/outputs --out reports/leaderboard.md

run-matrix-fake:
	python -m tender_timeline.run_matrix --provider fake --model fake-v1 --items data/public_dev/items --out-dir baselines/outputs

demo: validate verify-gold test grade-sample report-sample aggregate
	@echo Demo complete. See reports/mini_eval_report.md and reports/leaderboard.md
