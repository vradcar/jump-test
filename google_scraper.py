"""
Google Scraper — executes a Boolean search string on Google using
cookie-based authentication to bypass bot detection, then parses
the organic results.
"""

import time
import requests
from bs4 import BeautifulSoup
from dataclasses import dataclass
from rich.console import Console

import config

console = Console()


@dataclass
class SearchResult:
    """One organic Google result."""
    title: str
    url: str
    snippet: str


def search(boolean_string: str, num_results: int | None = None) -> list[SearchResult]:
    """
    Runs the boolean string as a Google query and returns parsed results.

    Uses cookie + user-agent headers to appear as a real browser session.
    """
    num = num_results or config.GOOGLE_NUM_RESULTS

    headers = {
        "User-Agent": config.GOOGLE_USER_AGENT,
        "Cookie": config.GOOGLE_COOKIE,
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
        "Accept-Encoding": "gzip, deflate, br",
        "Referer": "https://www.google.com/",
        "DNT": "1",
    }

    params = {
        "q": boolean_string,
        "num": num,
        "hl": "en",
    }

    console.print(f"  [dim]Querying Google with {len(boolean_string)} char Boolean string …[/dim]")

    try:
        resp = requests.get(
            "https://www.google.com/search",
            headers=headers,
            params=params,
            timeout=15,
        )
        resp.raise_for_status()
    except requests.RequestException as exc:
        console.print(f"  [red]Google request failed:[/red] {exc}")
        return []

    # Check for CAPTCHA / block page
    if "sorry" in resp.url.lower() or resp.status_code == 429:
        console.print("  [red]Google returned a CAPTCHA or rate-limit page.[/red]")
        console.print("  [yellow]→ Refresh your GOOGLE_COOKIE in .env and try again.[/yellow]")
        return []

    soup = BeautifulSoup(resp.text, "html.parser")
    results: list[SearchResult] = []

    # Google wraps each organic result in a <div class="g"> (or data-sokoban)
    for g_div in soup.select("div.g"):
        # Title + URL live in the first <a> with an <h3>
        anchor = g_div.select_one("a[href]")
        h3 = g_div.select_one("h3")
        if not anchor or not h3:
            continue

        url = anchor.get("href", "")
        title = h3.get_text(strip=True)

        # Snippet — usually in a <div> with class containing "VwiC3b" or a <span>
        snippet_el = (
            g_div.select_one("[data-sncf]")
            or g_div.select_one(".VwiC3b")
            or g_div.select_one("div.IsZvec")
        )
        snippet = snippet_el.get_text(" ", strip=True) if snippet_el else ""

        # Only keep LinkedIn profile URLs
        if "linkedin.com/in/" in url:
            results.append(SearchResult(title=title, url=url, snippet=snippet))

    # Respect rate limits
    time.sleep(config.GOOGLE_DELAY_SECONDS)

    console.print(f"  [green]Found {len(results)} LinkedIn profile results.[/green]")
    return results
