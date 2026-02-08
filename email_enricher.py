"""
Email Enricher — resolves company domains and finds email addresses.

Default method: free pattern-guessing + SMTP verification (unlimited).
Optional fallback: Hunter.io API (limited free tier).
"""

import re
import requests
from rich.console import Console

import config
import email_guesser
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
    # Strip common suffixes like Inc, LLC, Corp, Ltd, etc.
    cleaned = re.sub(
        r"\b(inc\.?|llc\.?|corp\.?|ltd\.?|co\.?|group|holdings?)\b",
        "",
        company_name,
        flags=re.IGNORECASE,
    )
    slug = re.sub(r"[^a-z0-9]", "", cleaned.lower())
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

    # If Hunter.io is configured, try it first for better accuracy
    domain = None
    if config.HUNTER_API_KEY:
        domain = _hunter_domain_search(company_name)

    # Fall back to pattern guess
    if not domain:
        domain = _guess_domain(company_name)

    _DOMAIN_CACHE[key] = domain
    return domain


# ── Hunter.io email finder ───────────────────────────────────────────────────

def _hunter_find_email(first_name: str, last_name: str, domain: str) -> str | None:
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


# ── Unified email lookup ─────────────────────────────────────────────────────

def find_email(first_name: str, last_name: str, domain: str, method: str = "auto") -> tuple[str | None, str]:
    """
    Find an email using the configured method.

    Methods:
        "auto"    → try guesser first, fall back to Hunter if configured
        "guess"   → pattern guess + SMTP only (free, unlimited)
        "hunter"  → Hunter.io API only

    Returns (email, source) where source is "smtp", "hunter", "guess", or "none".
    """
    if not all([first_name, last_name, domain]):
        return None, "none"

    if method == "hunter":
        email = _hunter_find_email(first_name, last_name, domain)
        return (email, "hunter") if email else (None, "none")

    if method == "guess":
        email = email_guesser.find_email(first_name, last_name, domain)
        return (email, "smtp" if email else "guess"), "guess" if not email else "smtp"

    # Auto mode: guesser first (free), then Hunter as fallback
    email = email_guesser.find_email(first_name, last_name, domain)
    if email:
        return email, "smtp"

    if config.HUNTER_API_KEY:
        email = _hunter_find_email(first_name, last_name, domain)
        if email:
            return email, "hunter"

    return None, "none"


# ── Batch enrichment ─────────────────────────────────────────────────────────

def enrich_profiles(profiles: list[ProfileData], method: str = "auto") -> list[dict]:
    """
    For each profile, resolve the company domain and look up the email.
    Returns a list of dicts ready for output.
    """
    method_label = {
        "auto": "Pattern Guess + SMTP (free) → Hunter.io fallback",
        "guess": "Pattern Guess + SMTP (free, unlimited)",
        "hunter": "Hunter.io API",
    }.get(method, method)
    console.print(f"  [dim]Method: {method_label}[/dim]")

    enriched: list[dict] = []

    for i, p in enumerate(profiles, 1):
        row = p.to_dict()

        domain = resolve_domain(p.company_name)
        row["company_domain"] = domain

        email = None
        source = "none"
        if p.first_name and p.last_name and domain:
            console.print(
                f"  [dim]({i}/{len(profiles)}) Looking up email for "
                f"{p.first_name} {p.last_name} @ {domain} …[/dim]"
            )
            email, source = find_email(p.first_name, p.last_name, domain, method)

        row["email"] = email
        row["email_source"] = source
        enriched.append(row)

        if email:
            console.print(f"    [green]✓ {email}[/green]  [dim]({source})[/dim]")
        else:
            console.print(f"    [yellow]✗ No email found[/yellow]")

    return enriched
