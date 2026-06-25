#!/usr/bin/env python3
"""
Vision timing probe — measure the photo→product round-trip per brain.

This is the "how long does it take to create a new product" KPI tool. Point it at
one or more sample product photos, pick the brains, and it fires each photo at each
provider N times and reports latency (p50/p95) + the draft fields it got back.

Needs the relevant key(s) in the environment (it calls the real model):
    BH_GOOGLE_API_KEY      for gemini   (the free-with-a-Google-account path)
    ANTHROPIC_API_KEY      for claude
    OLLAMA_URL + a pulled vision model for ollama

Examples:
    python scripts/vision_timing_probe.py photo1.jpg photo2.jpg
    python scripts/vision_timing_probe.py shot.jpg --provider gemini --provider claude -n 5

Rule #11: Python + Typer + asyncio.
"""
from __future__ import annotations

import asyncio
import statistics
import sys
from pathlib import Path

import typer

# Make `src...` importable when run from the repo root.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

app = typer.Typer(add_completion=False, help=__doc__)


def _pct(values: list[float], p: float) -> float:
    if not values:
        return 0.0
    s = sorted(values)
    k = max(0, min(len(s) - 1, round((p / 100) * (len(s) - 1))))
    return s[k]


async def _run(photos: list[Path], providers: list[str], n: int) -> None:
    from src.services.vision_product_analyzer import suggest_product_from_image

    for provider in providers:
        typer.secho(f"\n=== {provider} ===", fg=typer.colors.CYAN, bold=True)
        lat: list[float] = []
        for photo in photos:
            raw = photo.read_bytes()
            for i in range(n):
                res = await suggest_product_from_image(raw, "image/jpeg", provider=provider)
                ms = res["elapsed_ms"]
                lat.append(ms)
                s = res["suggestion"]
                note = f"  ⚠ {res['note']}" if res.get("note") else ""
                typer.echo(
                    f"  {photo.name} #{i+1}: {ms:>5}ms  conf={s['confidence']:.2f}  "
                    f"name={s['name']!r} cat={s['category']!r} price≈{s['price_estimate']}{note}"
                )
        if lat:
            typer.secho(
                f"  → n={len(lat)}  p50={_pct(lat,50):.0f}ms  p95={_pct(lat,95):.0f}ms  "
                f"min={min(lat):.0f}  max={max(lat):.0f}  mean={statistics.mean(lat):.0f}",
                fg=typer.colors.GREEN, bold=True,
            )


@app.command()
def main(
    photos: list[Path] = typer.Argument(..., help="Sample product photo(s)"),
    provider: list[str] = typer.Option(
        None, "--provider", "-p",
        help="Brain(s) to test: gemini|claude|ollama (default: gemini)",
    ),
    n: int = typer.Option(3, "--runs", "-n", help="Runs per photo per provider"),
) -> None:
    providers = provider or ["gemini"]
    missing = [p for p in photos if not p.exists()]
    if missing:
        typer.secho(f"Not found: {', '.join(map(str, missing))}", fg=typer.colors.RED)
        raise typer.Exit(1)
    asyncio.run(_run(photos, providers, n))


if __name__ == "__main__":
    app()
