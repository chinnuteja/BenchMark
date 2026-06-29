"""Generate evaluation reports from grade-result JSON files."""

from __future__ import annotations

import json
from pathlib import Path

import typer
from rich.console import Console

from tender_timeline.utils import repo_root

app = typer.Typer(add_completion=False)
console = Console()


def _baseline_label(path: Path) -> str:
    stem = path.stem
    if stem.endswith("_grade_results"):
        return stem[: -len("_grade_results")]
    return stem


def _load_grade_results(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _format_metric(value: float | int) -> str:
    if isinstance(value, float):
        return f"{value:.4f}"
    return str(value)


def _format_metric_opt(value: float | int | None) -> str:
    """Format a metric that may be absent (e.g. paired_consistency with no pairs)."""
    if value is None:
        return "n/a"
    return _format_metric(value)


def _failure_mode_breakdown(items: list[dict]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for item in items:
        for error in item.get("errors", []):
            key = error.split(":", 1)[0]
            counts[key] = counts.get(key, 0) + 1
    return dict(sorted(counts.items(), key=lambda pair: (-pair[1], pair[0])))


def _attribution_breakdown(items: list[dict]) -> dict[str, int]:
    """Count failure-attribution categories across items (oracle-driven diagnosis)."""
    counts: dict[str, int] = {}
    for item in items:
        for category in item.get("failure_attribution", []):
            counts[category] = counts.get(category, 0) + 1
    return dict(sorted(counts.items(), key=lambda pair: (-pair[1], pair[0])))


# Substantive procedural failures, in descending order of how telling they are.
_SUBSTANTIVE_PRIORITY = [
    "CASCADE_ARITHMETIC_ERROR",
    "WRONG_RULE_SELECTION",
    "WRONG_CONTROLLING_DEADLINE",
]


def _format_substantive_failure(baseline: dict, item: dict, entry: dict) -> str:
    category = entry.get("category", "")
    evidence = entry.get("evidence", {})
    ev_str = ", ".join(f"{k}={v}" for k, v in evidence.items())
    suffix = f" (evidence: {ev_str})" if ev_str else ""
    return (
        f"**{baseline['label']} / {item['item_id']}** — "
        f"{entry.get('message', category)} [`{category}`]{suffix} "
        "This is a competent-looking procedural failure, mechanically "
        "diagnosed by the oracle rather than hand-written."
    )


def _strongest_substantive_failure(baselines: list[dict]) -> str | None:
    """Find the most telling oracle-diagnosed failure across baselines, with evidence.

    Within each category we prefer cases where the same item also has a WRONG_VERDICT
    attribution, i.e. the reasoning slip actually flipped the procedural outcome — the
    most damning "looks competent but is wrong" failure.
    """
    for category in _SUBSTANTIVE_PRIORITY:
        for require_flipped_verdict in (True, False):
            for baseline in baselines:
                for item in baseline["payload"]["items"]:
                    item_categories = item.get("failure_attribution", [])
                    if require_flipped_verdict and "WRONG_VERDICT" not in item_categories:
                        continue
                    for entry in item.get("attribution_detail", []):
                        if entry.get("category") == category:
                            return _format_substantive_failure(baseline, item, entry)
    return None


def _classify_item_errors(item: dict) -> tuple[list[str], list[str]]:
    """Split item errors into substantive procedural vs formatting/taxonomy failures."""
    substantive: list[str] = []
    formatting: list[str] = []

    field_results = item.get("field_results", {})
    verdict_wrong = not field_results.get("verdict", {}).get("passed", True)

    for error in item.get("errors", []):
        key = error.split(":", 1)[0]
        if key == "parse_error":
            substantive.append(error)
        elif key == "wrong_verdict":
            substantive.append(error)
        elif key in {"wrong_clause_grounding", "wrong_governing_clause_id"} or key == "missing_required_clause":
            substantive.append(error)
        elif key == "wrong_operative_deadline":
            if verdict_wrong:
                substantive.append(error)
            else:
                formatting.append(error)
        elif key == "wrong_failure_reason_code":
            formatting.append(error)
        else:
            formatting.append(error)

    return substantive, formatting


def _format_failed_item_line(baseline_label: str, item: dict, category: str) -> str:
    diagnosis = "; ".join(item.get("diagnosis", [])[:3]) or "No diagnosis recorded."
    return f"- **{baseline_label} / {item['item_id']}** ({category}): {diagnosis}"


def _failure_sections_for_baseline(baseline: dict) -> tuple[list[str], list[str]]:
    substantive_lines: list[str] = []
    formatting_lines: list[str] = []

    for item in baseline["payload"]["items"]:
        if item.get("passed"):
            continue
        substantive_errors, formatting_errors = _classify_item_errors(item)
        label = baseline["label"]
        if substantive_errors:
            substantive_lines.append(
                _format_failed_item_line(label, item, "substantive")
            )
        if formatting_errors and not substantive_errors:
            formatting_lines.append(
                _format_failed_item_line(label, item, "formatting/taxonomy")
            )
        elif formatting_errors and substantive_errors:
            formatting_lines.append(
                _format_failed_item_line(label, item, "also formatting/taxonomy")
            )

    return substantive_lines, formatting_lines


def generate_report(
    grade_result_paths: list[Path],
    output_path: Path,
    items_dir: Path | None = None,
    *,
    real_model: bool = False,
) -> str:
    """Build a Markdown evaluation report."""
    root = repo_root()
    resolved_output = output_path if output_path.is_absolute() else root / output_path

    baselines: list[dict] = []
    for path in grade_result_paths:
        resolved = path if path.is_absolute() else root / path
        baselines.append(
            {
                "label": _baseline_label(resolved),
                "path": str(resolved.relative_to(root) if resolved.is_relative_to(root) else resolved),
                "payload": _load_grade_results(resolved),
            }
        )

    item_count = baselines[0]["payload"]["summary"]["num_items"] if baselines else 0
    family_count = 3
    if items_dir is not None:
        resolved_items = items_dir if items_dir.is_absolute() else root / items_dir
        item_count = len(list(resolved_items.glob("*.json")))

    title = (
        "# TENDER-TIMELINE Real Model Evaluation Report"
        if real_model
        else "# TENDER-TIMELINE Mini Evaluation Report"
    )
    lines = [
        title,
        "",
        "## What TENDER-TIMELINE Tests",
        "",
        "TENDER-TIMELINE evaluates whether models can verify procedural compliance in procurement documents: controlling clauses, amended deadlines, validity periods, protest windows, and structured JSON answers.",
        "",
        "## Dataset Summary",
        "",
        f"- Public-dev items: {item_count}",
        f"- Document families: {family_count}",
        "- Data version: public_dev_v0.1",
        "",
        "## Baselines Run",
        "",
    ]

    for baseline in baselines:
        lines.append(f"- `{baseline['label']}` ({baseline['path']})")

    if real_model:
        disclaimer = (
            "> These are real model outputs from live API calls. "
            "Provider and model are recorded in each JSONL record."
        )
        limitations_extra = "- Results reflect real model deployments on the public-dev MVP slice."
    else:
        disclaimer = (
            "> These are fake/sample outputs used to demonstrate the evaluation pipeline. "
            "Real model outputs can be generated by providing provider API keys."
        )
        limitations_extra = "- Fake baselines are deterministic samples for pipeline validation."

    lines.extend(
        [
            "",
            disclaimer,
            "",
            "## Metrics",
            "",
            "| Baseline | Strict Accuracy | Verdict Accuracy | Failure Code Accuracy | "
            "Clause Grounding | Paired Consistency | Right-Reason | Parse Error Rate |",
            "|---|---:|---:|---:|---:|---:|---:|---:|",
        ]
    )

    for baseline in baselines:
        summary = baseline["payload"]["summary"]
        lines.append(
            "| {label} | {strict} | {verdict} | {failure} | {clause} | "
            "{paired} | {right} | {parse} |".format(
                label=baseline["label"],
                strict=_format_metric(summary["strict_accuracy"]),
                verdict=_format_metric(summary["verdict_accuracy"]),
                failure=_format_metric(summary["failure_code_accuracy"]),
                clause=_format_metric(summary["clause_grounding_accuracy"]),
                paired=_format_metric_opt(summary.get("paired_consistency")),
                right=_format_metric_opt(summary.get("right_reason_accuracy")),
                parse=_format_metric(summary["parse_error_rate"]),
            )
        )

    lines.extend(["", "## Failure-Mode Breakdown", ""])
    for baseline in baselines:
        breakdown = _failure_mode_breakdown(baseline["payload"]["items"])
        lines.append(f"### {baseline['label']}")
        if breakdown:
            for error, count in breakdown.items():
                lines.append(f"- `{error}`: {count}")
        else:
            lines.append("- No recorded errors.")
        lines.append("")

    lines.extend(
        [
            "## Failure-Attribution Breakdown",
            "",
            "Oracle-driven diagnosis: which procedural reasoning step each prediction got wrong.",
            "",
        ]
    )
    for baseline in baselines:
        attribution = _attribution_breakdown(baseline["payload"]["items"])
        lines.append(f"### {baseline['label']}")
        if attribution:
            for category, count in attribution.items():
                lines.append(f"- `{category}`: {count}")
        else:
            lines.append("- No recorded attributions.")
        lines.append("")

    if real_model:
        strongest = _strongest_substantive_failure(baselines)
        lines.extend(
            [
                "## Strongest Substantive Failure",
                "",
                strongest or "- No oracle-diagnosed substantive failure in supplied grade results.",
                "",
                "## Failure Classification",
                "",
                "### Substantive procedural failures",
                "",
            ]
        )
        substantive_all: list[str] = []
        formatting_all: list[str] = []
        for baseline in baselines:
            substantive, formatting = _failure_sections_for_baseline(baseline)
            substantive_all.extend(substantive)
            formatting_all.extend(formatting)
        if substantive_all:
            lines.extend(substantive_all)
        else:
            lines.append("- None recorded.")
        lines.extend(["", "### Formatting / taxonomy / schema failures", ""])
        if formatting_all:
            lines.extend(formatting_all)
        else:
            lines.append("- None recorded.")
    else:
        lines.extend(["## Concrete Failure Cases", ""])
        cases: list[str] = []
        for baseline in baselines:
            substantive, formatting = _failure_sections_for_baseline(baseline)
            cases.extend(substantive[:3])
            cases.extend(formatting[:2])
            if len(cases) >= 5:
                break
        if cases:
            lines.extend(cases[:5])
        else:
            lines.append("- No failing items in supplied grade results.")

    lines.extend(
        [
            "",
            "## What This Shows",
            "",
            "The benchmark exposes failures where models appear competent but ground answers in the wrong clause, miss addendum-controlled deadlines, or apply the wrong procedural rule.",
            "",
            "## Limitations",
            "",
            "- Public-dev demo items only; not legal advice.",
            limitations_extra,
            "- Six items is an MVP slice, not a production benchmark size.",
            "",
            "## Fellowship-Scale Next Steps",
            "",
            "- Expand item families with perturbation certificates and expert QA.",
            "- Run a real model × prompt matrix (OpenAI, Anthropic, Google).",
            "- Add held-out private evaluation and richer failure taxonomy.",
            "",
        ]
    )

    report_text = "\n".join(lines)
    resolved_output.parent.mkdir(parents=True, exist_ok=True)
    resolved_output.write_text(report_text, encoding="utf-8")
    return report_text


@app.command()
def main(
    grade_results: list[Path] = typer.Option(
        ...,
        "--grade-results",
        help="Grade-results JSON file; pass multiple times",
    ),
    out: Path = typer.Option(..., "--out", help="Output Markdown report path"),
    items: Path | None = typer.Option(None, "--items", help="Optional items directory"),
    real_model: bool = typer.Option(False, "--real-model", help="Label report as real model outputs"),
) -> None:
    """Generate a Markdown evaluation report from grade-result files."""
    report_text = generate_report(
        grade_result_paths=grade_results,
        output_path=out,
        items_dir=items,
        real_model=real_model,
    )
    console.print("[green]Wrote evaluation report[/green]")
    console.print(report_text[:800] + ("..." if len(report_text) > 800 else ""))


if __name__ == "__main__":
    app()
