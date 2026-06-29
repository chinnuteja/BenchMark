"""CLI to validate benchmark item JSON files."""

from __future__ import annotations

import json
from pathlib import Path

import typer
from rich.console import Console

from tender_timeline.calculator import CalculatorError, compute_expected
from tender_timeline.normalize import date_or_datetime_equal, normalize_enum
from tender_timeline.schema import TenderTimelineItem
from tender_timeline.utils import repo_root

app = typer.Typer(add_completion=False)
console = Console()


def validate_item_file(path: Path, root: Path) -> tuple[str, bool, str]:
    """Validate a single item file. Returns (item_id, ok, message)."""
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
        item = TenderTimelineItem.model_validate(raw)
    except Exception as exc:  # noqa: BLE001 - surface validation errors to CLI
        item_id = path.stem
        try:
            item_id = json.loads(path.read_text(encoding="utf-8")).get("item_id", item_id)
        except Exception:
            pass
        return item_id, False, str(exc)

    missing_docs: list[str] = []
    for doc in item.documents:
        doc_path = root / doc.path
        if not doc_path.is_file():
            missing_docs.append(doc.path)

    if missing_docs:
        return item.item_id, False, f"missing documents: {', '.join(missing_docs)}"

    return item.item_id, True, "ok"


def verify_gold(item: TenderTimelineItem) -> tuple[bool, list[str]]:
    """Recompute gold via the oracle and compare to the authored expected_answer."""
    if item.compute_spec is None:
        return True, ["no compute_spec (skipped)"]
    try:
        computed = compute_expected(item)
    except CalculatorError as exc:
        return False, [f"calculator error: {exc}"]
    exp = item.expected_answer
    checks = [
        (
            "operative_deadline",
            date_or_datetime_equal(exp.operative_deadline, computed.operative_deadline),
        ),
        (
            "required_bid_security_validity_through",
            date_or_datetime_equal(
                exp.required_bid_security_validity_through,
                computed.required_bid_security_validity_through,
            ),
        ),
        (
            "verdict",
            normalize_enum(exp.verdict) == normalize_enum(computed.verdict),
        ),
        (
            "failure_reason_code",
            normalize_enum(exp.failure_reason_code) == normalize_enum(computed.failure_reason_code),
        ),
    ]
    mismatches = [
        f"{name}: authored={getattr(exp, name)!r} computed={getattr(computed, name)!r}"
        for name, ok in checks
        if not ok
    ]
    return len(mismatches) == 0, mismatches


@app.command()
def main(
    items: Path = typer.Option(
        ...,
        "--items",
        help="Directory containing benchmark item JSON files",
    ),
    verify_gold_flag: bool = typer.Option(
        False,
        "--verify-gold",
        help="Also verify that authored gold answers match the oracle-computed answers",
    ),
) -> None:
    """Load and validate all benchmark item JSON files."""
    root = repo_root()
    items_dir = items if items.is_absolute() else root / items

    if not items_dir.is_dir():
        console.print(f"[red]Items directory not found: {items_dir}[/red]")
        raise typer.Exit(code=1)

    json_files = sorted(items_dir.glob("*.json"))
    if not json_files:
        console.print(f"[red]No JSON files found in {items_dir}[/red]")
        raise typer.Exit(code=1)

    console.print(f"Loaded {len(json_files)} items")

    any_failed = False
    loaded_items: list[TenderTimelineItem] = []
    for path in json_files:
        item_id, ok, message = validate_item_file(path, root)
        status = "valid" if ok else "INVALID"
        console.print(f"  {item_id}: {status}")
        if not ok:
            any_failed = True
            console.print(f"    [red]{message}[/red]")
        elif verify_gold_flag:
            raw = json.loads(path.read_text(encoding="utf-8"))
            loaded_items.append(TenderTimelineItem.model_validate(raw))

    if any_failed:
        console.print("[red]Some items failed validation[/red]")
        raise typer.Exit(code=1)

    console.print("[green]All items valid[/green]")

    if verify_gold_flag:
        console.print("\nVerifying gold answers against oracle...")
        for item in loaded_items:
            ok, messages = verify_gold(item)
            if ok:
                console.print(f"  {item.item_id}: gold OK")
            else:
                any_failed = True
                console.print(f"  [red]{item.item_id}: gold MISMATCH[/red]")
                for msg in messages:
                    console.print(f"    [red]{msg}[/red]")
        if any_failed:
            console.print("[red]Gold verification failed[/red]")
            raise typer.Exit(code=1)
        console.print("[green]All gold answers verified[/green]")


if __name__ == "__main__":
    app()
