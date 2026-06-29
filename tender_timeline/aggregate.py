"""Aggregate many grade-result files into a model x prompt leaderboard."""

from __future__ import annotations

import json
from pathlib import Path

import typer
from rich.console import Console

from tender_timeline.report import _baseline_label
from tender_timeline.utils import repo_root

app = typer.Typer(add_completion=False)
console = Console()

# Longest-match-first so "event_graph_first" wins over "event_graph".
PROMPT_SUFFIXES = ["event_graph_first", "event_graph", "clause_first", "naive"]


def parse_label(label: str) -> tuple[str, str]:
    """Split '{provider}_{model}_{prompt}' into (model_label, prompt)."""
    for suffix in PROMPT_SUFFIXES:
        if label == suffix:
            return "unknown", suffix
        if label.endswith("_" + suffix):
            return label[: -(len(suffix) + 1)], suffix
    return label, "unknown"


def build_leaderboard(results_dir: Path) -> dict:
    rows = []
    for path in sorted(results_dir.glob("*_grade_results.json")):
        payload = json.loads(path.read_text(encoding="utf-8"))
        summary = payload.get("summary", {})
        model, prompt = parse_label(_baseline_label(path))
        rows.append(
            {
                "file": path.name,
                "model": model,
                "prompt": prompt,
                "strict_accuracy": summary.get("strict_accuracy"),
                "verdict_accuracy": summary.get("verdict_accuracy"),
                "clause_grounding_accuracy": summary.get("clause_grounding_accuracy"),
                "paired_consistency": summary.get("paired_consistency"),
                "right_reason_accuracy": summary.get("right_reason_accuracy"),
                "parse_error_rate": summary.get("parse_error_rate"),
            }
        )
    rows.sort(key=lambda r: (r["model"], r["prompt"]))
    return {"rows": rows}


def render_markdown(leaderboard: dict) -> str:
    lines = [
        "# TENDER-TIMELINE Leaderboard",
        "",
        "| Model | Prompt | Strict | Verdict | Clause | Paired Consist. | Right-Reason | Parse Err |",
        "|---|---|---:|---:|---:|---:|---:|---:|",
    ]
    for r in leaderboard["rows"]:

        def fmt(v: object) -> str:
            return "n/a" if v is None else (f"{v:.4f}" if isinstance(v, float) else str(v))

        lines.append(
            f"| {r['model']} | {r['prompt']} | {fmt(r['strict_accuracy'])} | "
            f"{fmt(r['verdict_accuracy'])} | {fmt(r['clause_grounding_accuracy'])} | "
            f"{fmt(r['paired_consistency'])} | {fmt(r['right_reason_accuracy'])} | "
            f"{fmt(r['parse_error_rate'])} |"
        )
    lines.append("")
    return "\n".join(lines)


@app.command()
def main(
    results_dir: Path = typer.Option(
        ..., "--results-dir", help="Directory of *_grade_results.json files"
    ),
    out: Path = typer.Option(
        Path("reports/leaderboard.md"), "--out", help="Markdown leaderboard output"
    ),
    json_out: Path = typer.Option(
        Path("reports/leaderboard.json"), "--json-out", help="JSON leaderboard output"
    ),
) -> None:
    """Aggregate grade-result files into a model x prompt leaderboard."""
    root = repo_root()
    resolved_dir = results_dir if results_dir.is_absolute() else root / results_dir
    leaderboard = build_leaderboard(resolved_dir)

    md_path = out if out.is_absolute() else root / out
    json_path = json_out if json_out.is_absolute() else root / json_out
    md_path.parent.mkdir(parents=True, exist_ok=True)
    json_path.parent.mkdir(parents=True, exist_ok=True)
    md_path.write_text(render_markdown(leaderboard), encoding="utf-8")
    json_path.write_text(json.dumps(leaderboard, indent=2), encoding="utf-8")

    console.print(
        f"[green]Wrote {len(leaderboard['rows'])} rows to {md_path} and {json_path}[/green]"
    )


if __name__ == "__main__":
    app()
