#!/usr/bin/env python3
"""
LinkedIn Profile Finder — CLI entry point.

Usage:
    python main.py "VP of Sales at SaaS companies in Boston"
    python main.py --interactive
    python main.py --skip-email "Python developers in Berlin"
"""

import sys
import click
from rich.console import Console
from rich.panel import Panel
from rich.text import Text

import config
import boolean_generator
import google_scraper
import profile_extractor
import email_enricher
import output_handler

console = Console()


def _banner():
    console.print(
        Panel(
            Text.from_markup(
                "[bold cyan]LinkedIn Profile Finder[/bold cyan]\n"
                "[dim]Search → Extract → Enrich → Export[/dim]"
            ),
            border_style="blue",
        )
    )


def run_pipeline(query: str, skip_email: bool = False, num_results: int | None = None):
    """Full pipeline: Boolean → Google → Extract → Enrich → Save."""

    # ── Step 1: Generate Boolean search string ───────────────────────────
    console.print("\n[bold]Step 1/4 · Generating Boolean search string …[/bold]")
    boolean_string = boolean_generator.generate(query)
    console.print(f"  [cyan]{boolean_string}[/cyan]\n")

    # ── Step 2: Google search ────────────────────────────────────────────
    console.print("[bold]Step 2/4 · Searching Google …[/bold]")
    results = google_scraper.search(boolean_string, num_results=num_results)
    if not results:
        console.print("  [red]No LinkedIn results found. Try a different query.[/red]")
        return

    # ── Step 3: Extract profile data ─────────────────────────────────────
    console.print(f"\n[bold]Step 3/4 · Extracting data from {len(results)} results …[/bold]")
    profiles = profile_extractor.extract_profiles(results)
    console.print(f"  [green]Extracted {len(profiles)} profiles.[/green]\n")

    # ── Step 4: Email enrichment ─────────────────────────────────────────
    if skip_email:
        console.print("[bold]Step 4/4 · Email enrichment skipped (--skip-email).[/bold]\n")
        enriched = [p.to_dict() for p in profiles]
        for row in enriched:
            row["company_domain"] = None
            row["email"] = None
            row["email_source"] = None
    else:
        method = config.EMAIL_METHOD
        console.print(f"[bold]Step 4/4 · Finding emails …[/bold]")
        enriched = email_enricher.enrich_profiles(profiles, method=method)
        console.print()

    # ── Display + Save ───────────────────────────────────────────────────
    output_handler.print_table(enriched)

    # Build a filesystem-friendly tag from the query
    tag = query[:40].strip().replace(" ", "_").replace("/", "-")
    paths = output_handler.save(enriched, tag=tag)

    if paths:
        console.print(f"\n[bold green]Done![/bold green] Files saved to: {', '.join(paths)}")
    else:
        console.print("\n[bold green]Done![/bold green]")


# ── CLI ──────────────────────────────────────────────────────────────────────

@click.command()
@click.argument("query", required=False)
@click.option("--interactive", "-i", is_flag=True, help="Interactive mode — prompt for queries in a loop.")
@click.option("--skip-email", "-s", is_flag=True, help="Skip Hunter.io email enrichment.")
@click.option("--num", "-n", type=int, default=None, help="Number of Google results to fetch.")
def main(query: str | None, interactive: bool, skip_email: bool, num: int | None):
    """
    Find LinkedIn profiles matching ANY criteria.

    Pass a query directly:
        python main.py "Marketing Managers at startups in Austin"

    Or run interactively:
        python main.py --interactive
    """
    _banner()

    # ── Config validation ────────────────────────────────────────────────
    errors = config.validate(skip_email=skip_email)
    if errors:
        for e in errors:
            console.print(f"  [red]✗ {e}[/red]")
        console.print("\n  [yellow]Copy .env.example → .env and add your API keys.[/yellow]")
        sys.exit(1)

    # ── Interactive loop ─────────────────────────────────────────────────
    if interactive:
        console.print("[dim]Type your query, or 'quit' to exit.[/dim]\n")
        while True:
            q = console.input("[bold cyan]Query → [/bold cyan]").strip()
            if q.lower() in ("quit", "exit", "q"):
                break
            if q:
                run_pipeline(q, skip_email=skip_email, num_results=num)
                console.print()
        return

    # ── Single-shot mode ─────────────────────────────────────────────────
    if not query:
        console.print("[red]Provide a query or use --interactive mode.[/red]")
        console.print("[dim]Example: python main.py \"VP of Sales in Boston\"[/dim]")
        sys.exit(1)

    run_pipeline(query, skip_email=skip_email, num_results=num)


if __name__ == "__main__":
    main()
