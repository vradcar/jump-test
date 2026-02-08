"""
SerpAPI client — uses SerpAPI to search Google for LinkedIn profiles.
"""

import time
from dataclasses import dataclass
from rich.console import Console
from serpapi import GoogleSearch

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
    Performs a Google Custom Search using the official API.
    """
    num = num_results or config.GOOGLE_NUM_RESULTS

    console.print(f"  [dim]Querying SerpAPI with {len(boolean_string)} char Boolean string …[/dim]")

    if not config.SERPAPI_KEY:
        console.print("  [red]Error: SERPAPI_KEY must be set in .env[/red]")
        console.print("  [yellow]Get free key at: https://serpapi.com/users/sign_up[/yellow]")
        return []

    results: list[SearchResult] = []

    try:
        # Query SerpAPI
        search = GoogleSearch({
            "q": boolean_string,
            "num": num,
            "api_key": config.SERPAPI_KEY
        })
        
        response = search.get_dict()
        organic_results = response.get("organic_results", [])
        
        for item in organic_results:
            url = item.get("link", "")
            title = item.get("title", "")
            snippet = item.get("snippet", "")

            # Only keep LinkedIn profile URLs
            if "linkedin.com/in/" in url:
                results.append(SearchResult(title=title, url=url, snippet=snippet))

    except Exception as e:
        console.print(f"  [red]Error querying SerpAPI:[/red] {e}")
        return []

    # Respect rate limits
    time.sleep(config.GOOGLE_DELAY_SECONDS)

    console.print(f"  [green]Found {len(results)} LinkedIn profile results.[/green]")
    return results
