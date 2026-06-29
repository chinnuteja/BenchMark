"""CLI for running models over benchmark items."""

from __future__ import annotations

import json
from pathlib import Path

import typer
from rich.console import Console

from tender_timeline.prompts import build_prompt
from tender_timeline.providers import ProviderError, call_model
from tender_timeline.schema import TenderTimelineItem
from tender_timeline.utils import extract_json_from_text, repo_root

app = typer.Typer(add_completion=False)
console = Console()


def load_items(items_dir: Path) -> list[TenderTimelineItem]:
    items: list[TenderTimelineItem] = []
    for path in sorted(items_dir.glob("*.json")):
        raw = json.loads(path.read_text(encoding="utf-8"))
        items.append(TenderTimelineItem.model_validate(raw))
    return items


def prompt_name_from_path(prompt_path: Path) -> str:
    return prompt_path.stem


def run_items(
    provider: str,
    model: str,
    prompt_path: Path,
    items_dir: Path,
    output_path: Path,
    limit: int | None = None,
    item_id: str | None = None,
) -> None:
    """Run the model over items and write JSONL output records."""
    root = repo_root()
    resolved_items_dir = items_dir if items_dir.is_absolute() else root / items_dir
    resolved_prompt_path = prompt_path if prompt_path.is_absolute() else root / prompt_path
    resolved_output_path = output_path if output_path.is_absolute() else root / output_path

    template = resolved_prompt_path.read_text(encoding="utf-8")
    prompt_name = prompt_name_from_path(resolved_prompt_path)
    items = load_items(resolved_items_dir)

    if item_id:
        items = [item for item in items if item.item_id == item_id]
    if limit is not None:
        items = items[:limit]

    if not items:
        raise ValueError("No items selected to run")

    resolved_output_path.parent.mkdir(parents=True, exist_ok=True)
    records: list[dict] = []

    for item in items:
        prompt = build_prompt(item, template)
        try:
            response = call_model(
                provider=provider,
                model=model,
                prompt=prompt,
                item_id=item.item_id,
                prompt_name=prompt_name,
            )
        except ProviderError as exc:
            console.print(f"[red]Provider error for {item.item_id}: {exc}[/red]")
            raise typer.Exit(code=1) from exc

        raw_output = response.get("raw_output", "")
        parsed_prediction, parse_error = extract_json_from_text(raw_output)

        record = {
            "item_id": item.item_id,
            "provider": provider,
            "model": model,
            "prompt_name": prompt_name,
            "prompt_path": str(
                resolved_prompt_path.relative_to(root)
                if resolved_prompt_path.is_relative_to(root)
                else resolved_prompt_path
            ),
            "raw_output": raw_output,
            "parsed_prediction": parsed_prediction,
            "parse_error": parse_error,
            "latency_ms": response.get("latency_ms", 0),
            "usage": response.get("usage", {}),
            "data_version": item.data_version,
        }
        if provider == "fake":
            record["is_fake_sample_output"] = True
        records.append(record)

    with resolved_output_path.open("w", encoding="utf-8") as handle:
        for record in records:
            handle.write(json.dumps(record, ensure_ascii=False) + "\n")

    console.print(
        f"[green]Wrote {len(records)} records to {resolved_output_path}[/green]"
    )


@app.command()
def main(
    provider: str = typer.Option(..., "--provider"),
    model: str = typer.Option(..., "--model"),
    prompt: Path = typer.Option(..., "--prompt"),
    items: Path = typer.Option(..., "--items"),
    out: Path = typer.Option(..., "--out"),
    limit: int | None = typer.Option(None, "--limit"),
    item_id: str | None = typer.Option(None, "--item-id"),
) -> None:
    """Run a provider over benchmark items and save JSONL outputs."""
    run_items(
        provider=provider,
        model=model,
        prompt_path=prompt,
        items_dir=items,
        output_path=out,
        limit=limit,
        item_id=item_id,
    )


if __name__ == "__main__":
    app()
