"""
Output Handler — writes enriched profile data to CSV and/or JSON.
"""

import csv
import json
import os
from datetime import datetime
from pathlib import Path
from rich.console import Console

import config

console = Console()

_FIELDNAMES = [
    "person_name",
    "first_name",
    "last_name",
    "job_title",
    "company_name",
    "company_domain",
    "email",
    "location",
    "linkedin_url",
    "context_snippet",
]


def _ensure_dir() -> Path:
    out = Path(config.OUTPUT_DIR)
    out.mkdir(parents=True, exist_ok=True)
    return out


def _timestamp() -> str:
    return datetime.now().strftime("%Y%m%d_%H%M%S")


def save_csv(rows: list[dict], tag: str = "") -> str:
    out_dir = _ensure_dir()
    filename = f"profiles_{tag}_{_timestamp()}.csv" if tag else f"profiles_{_timestamp()}.csv"
    filepath = out_dir / filename

    with open(filepath, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=_FIELDNAMES, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)

    console.print(f"  [green]CSV saved →[/green] {filepath}")
    return str(filepath)


def save_json(rows: list[dict], tag: str = "") -> str:
    out_dir = _ensure_dir()
    filename = f"profiles_{tag}_{_timestamp()}.json" if tag else f"profiles_{_timestamp()}.json"
    filepath = out_dir / filename

    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(rows, f, indent=2, ensure_ascii=False)

    console.print(f"  [green]JSON saved →[/green] {filepath}")
    return str(filepath)


def save(rows: list[dict], tag: str = "") -> list[str]:
    """Save in the format(s) specified in config. Returns list of file paths."""
    if not rows:
        console.print("  [yellow]No data to save.[/yellow]")
        return []

    paths: list[str] = []
    fmt = config.OUTPUT_FORMAT

    if fmt in ("csv", "both"):
        paths.append(save_csv(rows, tag))
    if fmt in ("json", "both"):
        paths.append(save_json(rows, tag))

    return paths


def print_table(rows: list[dict]) -> None:
    """Pretty-print results to the console using Rich."""
    from rich.table import Table

    if not rows:
        console.print("[yellow]No results to display.[/yellow]")
        return

    table = Table(title="Extracted Profiles", show_lines=True, expand=True)
    table.add_column("Name", style="bold cyan", no_wrap=True)
    table.add_column("Title", style="white")
    table.add_column("Company", style="white")
    table.add_column("Email", style="green")
    table.add_column("Location", style="dim")
    table.add_column("LinkedIn", style="blue", no_wrap=True)

    for r in rows:
        table.add_row(
            r.get("person_name", "—"),
            r.get("job_title", "—"),
            r.get("company_name", "—"),
            r.get("email") or "—",
            r.get("location", "—"),
            r.get("linkedin_url", "—"),
        )

    console.print(table)
