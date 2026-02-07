"""
Email Enricher — resolves company domains and finds email addresses
using Hunter.io (with fallback domain-guessing for when Hunter's
domain-search returns nothing).
"""

import re
import requests
from rich.console import Console

import config
from profile_extractor import ProfileData

console = Console()

# ── Domain resolution helpers ────────────────────────────────────────────────

_DOMAIN_CACHE: dict[str, str | None] = {}


def _guess_domain(company_name: str) -> str | None:
    """
    Best-effort domain guess:  "Acme Corp" → "acmecorp.com"
    """
    if not company_name:
        return None
    slug = re.sub(r"[^a-z0-9]", "", company_name.lower())
    return f"{slug}.com" if slug else None


def _hunter_domain_search(company_name: str) -> str | None:
    """
    Use Hunter.io's Domain Search to resolve a company name → domain.
    """
    if not config.HUNTER_API_KEY or not company_name:
        return None

    try:
        resp = requests.get(
            "https://api.hunter.io/v2/domain-search",
            params={
                "company": company_name,
                "api_key": config.HUNTER_API_KEY,
            },
            timeout=10,
        )
        if resp.status_code == 200:
            data = resp.json().get("data", {})
            domain = data.get("domain")
            if domain:
                return domain
    except requests.RequestException:
        pass

    return None


def resolve_domain(company_name: str) -> str | None:
    """Resolve a company name to a domain, with caching."""
    if not company_name:
        return None

    key = company_name.strip().lower()
    if key in _DOMAIN_CACHE:
        return _DOMAIN_CACHE[key]

    # Try Hunter first, then fall back to a naive guess
    domain = _hunter_domain_search(company_name) or _guess_domain(company_name)
    _DOMAIN_CACHE[key] = domain
    return domain


# ── Email finder ─────────────────────────────────────────────────────────────

def find_email(first_name: str, last_name: str, domain: str) -> str | None:
    """
    Call Hunter.io's email-finder endpoint.
    Returns the best email address or None.
    """
    if not all([first_name, last_name, domain, config.HUNTER_API_KEY]):
        return None

    try:
        resp = requests.get(
            "https://api.hunter.io/v2/email-finder",
            params={
                "domain": domain,
                "first_name": first_name,
                "last_name": last_name,
                "api_key": config.HUNTER_API_KEY,
            },
            timeout=10,
        )
        if resp.status_code == 200:
            data = resp.json().get("data", {})
            return data.get("email")
    except requests.RequestException:
        pass

    return None


# ── Batch enrichment ─────────────────────────────────────────────────────────

def enrich_profiles(profiles: list[ProfileData]) -> list[dict]:
    """
    For each profile, resolve the company domain and look up the email.
    Returns a list of dicts ready for output.
    """
    enriched: list[dict] = []

    for i, p in enumerate(profiles, 1):
        row = p.to_dict()

        domain = resolve_domain(p.company_name)
        row["company_domain"] = domain

        email = None
        if p.first_name and p.last_name and domain:
            console.print(
                f"  [dim]({i}/{len(profiles)}) Looking up email for "
                f"{p.first_name} {p.last_name} @ {domain} …[/dim]"
            )
            email = find_email(p.first_name, p.last_name, domain)

        row["email"] = email
        enriched.append(row)

        if email:
            console.print(f"    [green]✓ {email}[/green]")
        else:
            console.print(f"    [yellow]✗ No email found[/yellow]")

    return enriched
