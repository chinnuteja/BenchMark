"""Run one provider/model across all three prompt templates (the eval matrix)."""

from __future__ import annotations

import re
from pathlib import Path

import typer
from rich.console import Console

from tender_timeline.run_model import run_items

app = typer.Typer(add_completion=False)
console = Console()

PROMPTS = ["naive", "clause_first", "event_graph_first"]


def model_slug(model: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", model.lower()) or "model"


@app.command()
def main(
    provider: str = typer.Option(..., "--provider"),
    model: str = typer.Option(..., "--model"),
    items: Path = typer.Option(..., "--items"),
    prompts_dir: Path = typer.Option(Path("baselines/prompts"), "--prompts-dir"),
    out_dir: Path = typer.Option(Path("baselines/outputs"), "--out-dir"),
) -> None:
    """Run one provider/model across all three prompt templates."""
    slug = model_slug(model)
    for prompt in PROMPTS:
        prompt_path = prompts_dir / f"{prompt}.md"
        out_path = out_dir / f"{provider}_{slug}_{prompt}_outputs.jsonl"
        console.print(f"[cyan]Running {provider}/{model} x {prompt}[/cyan]")
        run_items(
            provider=provider,
            model=model,
            prompt_path=prompt_path,
            items_dir=items,
            output_path=out_path,
        )
    console.print(
        f"[green]Matrix complete: {len(PROMPTS)} prompt runs for {provider}/{slug}[/green]"
    )


if __name__ == "__main__":
    app()
