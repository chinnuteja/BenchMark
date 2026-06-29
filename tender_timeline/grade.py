"""CLI for grading model predictions against benchmark items."""

from __future__ import annotations

import json
from pathlib import Path

import typer
from rich.console import Console
from rich.table import Table

from tender_timeline.consistency import paired_consistency, right_reason_rate
from tender_timeline.grader import grade_prediction
from tender_timeline.schema import TenderTimelineItem
from tender_timeline.utils import repo_root

app = typer.Typer(add_completion=False)
console = Console()


def load_items(items_dir: Path) -> dict[str, TenderTimelineItem]:
    items: dict[str, TenderTimelineItem] = {}
    for path in sorted(items_dir.glob("*.json")):
        raw = json.loads(path.read_text(encoding="utf-8"))
        item = TenderTimelineItem.model_validate(raw)
        items[item.item_id] = item
    return items


def load_predictions(predictions_path: Path) -> dict[str, dict]:
    predictions: dict[str, dict] = {}
    for line_no, line in enumerate(
        predictions_path.read_text(encoding="utf-8").splitlines(),
        start=1,
    ):
        stripped = line.strip()
        if not stripped:
            continue
        record = json.loads(stripped)
        item_id = record.get("item_id")
        if not item_id:
            raise ValueError(f"Missing item_id in predictions file line {line_no}")
        predictions[item_id] = record
    return predictions


def build_summary(item_results: list[dict]) -> dict[str, float | int | None]:
    num_items = len(item_results)
    if num_items == 0:
        return {
            "num_items": 0,
            "strict_accuracy": 0.0,
            "verdict_accuracy": 0.0,
            "failure_code_accuracy": 0.0,
            "clause_grounding_accuracy": 0.0,
            "parse_error_rate": 0.0,
            "paired_consistency": None,
            "right_reason_accuracy": 0.0,
        }

    parse_errors = sum(1 for result in item_results if "parse_error" in result.get("errors", []))

    return {
        "num_items": num_items,
        "strict_accuracy": round(
            sum(result["strict_score"] for result in item_results) / num_items,
            4,
        ),
        "verdict_accuracy": round(
            sum(result["verdict_score"] for result in item_results) / num_items,
            4,
        ),
        "failure_code_accuracy": round(
            sum(result["failure_code_score"] for result in item_results) / num_items,
            4,
        ),
        "clause_grounding_accuracy": round(
            sum(result["clause_grounding_score"] for result in item_results) / num_items,
            4,
        ),
        "parse_error_rate": round(parse_errors / num_items, 4),
        "paired_consistency": paired_consistency(item_results),
        "right_reason_accuracy": right_reason_rate(item_results),
    }


@app.command()
def main(
    items: Path = typer.Option(..., "--items", help="Directory containing item JSON files"),
    predictions: Path = typer.Option(..., "--predictions", help="Predictions JSONL file"),
    out: Path = typer.Option(..., "--out", help="Output JSON grade-results file"),
) -> None:
    """Grade model predictions and write JSON results."""
    root = repo_root()
    items_dir = items if items.is_absolute() else root / items
    predictions_path = predictions if predictions.is_absolute() else root / predictions
    output_path = out if out.is_absolute() else root / out

    item_map = load_items(items_dir)
    prediction_map = load_predictions(predictions_path)

    item_results: list[dict] = []
    for item_id, item in sorted(item_map.items()):
        record = prediction_map.get(item_id)
        if record is None:
            result = grade_prediction(item, prediction=None, raw_output=None)
            result["errors"].append("missing_prediction")
            result["diagnosis"].append("No prediction provided for this item.")
            result["contrast_group"] = item.contrast_group
            item_results.append(result)
            continue

        parsed_prediction = record.get("parsed_prediction")
        raw_output = record.get("raw_output")
        if parsed_prediction is not None and not isinstance(parsed_prediction, dict):
            parsed_prediction = None

        result = grade_prediction(
            item,
            prediction=parsed_prediction,
            raw_output=raw_output if parsed_prediction is None else None,
        )
        result["contrast_group"] = item.contrast_group
        item_results.append(result)

    payload = {
        "summary": build_summary(item_results),
        "items": item_results,
    }

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    summary = payload["summary"]
    table = Table(title="TENDER-TIMELINE Grade Summary")
    table.add_column("Metric")
    table.add_column("Value")
    table.add_row("Items", str(summary["num_items"]))
    table.add_row("Strict accuracy", str(summary["strict_accuracy"]))
    table.add_row("Verdict accuracy", str(summary["verdict_accuracy"]))
    table.add_row("Failure-code accuracy", str(summary["failure_code_accuracy"]))
    table.add_row("Clause-grounding accuracy", str(summary["clause_grounding_accuracy"]))
    table.add_row("Parse error rate", str(summary["parse_error_rate"]))
    table.add_row("Paired consistency", str(summary["paired_consistency"]))
    table.add_row("Right-reason accuracy", str(summary["right_reason_accuracy"]))
    console.print(table)

    item_table = Table(title="Per-Item Results")
    item_table.add_column("Item ID")
    item_table.add_column("Passed")
    item_table.add_column("Strict")
    item_table.add_column("Verdict")
    item_table.add_column("Clause")
    for result in item_results:
        item_table.add_row(
            result["item_id"],
            "yes" if result["passed"] else "no",
            str(result["strict_score"]),
            str(result["verdict_score"]),
            str(result["clause_grounding_score"]),
        )
    console.print(item_table)
    console.print(f"[green]Wrote grade results to {output_path}[/green]")


if __name__ == "__main__":
    app()
