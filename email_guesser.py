"""
Email Guesser — generates common email patterns from a person's name
and company domain, then verifies them via SMTP (free, unlimited).
"""

import re
import smtplib
import dns.resolver
from rich.console import Console

console = Console()

# ── MX lookup cache ──────────────────────────────────────────────────────────
_MX_CACHE: dict[str, str | None] = {}


def _get_mx_host(domain: str) -> str | None:
    """Look up the mail-exchange server for a domain."""
    if domain in _MX_CACHE:
        return _MX_CACHE[domain]

    try:
        records = dns.resolver.resolve(domain, "MX")
        # Pick the highest-priority (lowest preference number) MX record
        mx = sorted(records, key=lambda r: r.preference)[0]
        host = str(mx.exchange).rstrip(".")
        _MX_CACHE[domain] = host
        return host
    except Exception:
        _MX_CACHE[domain] = None
        return None


def generate_patterns(first: str, last: str, domain: str) -> list[str]:
    """
    Generate the most common corporate email patterns.
    Returns a list of candidate email addresses.
    """
    f = first.lower().strip()
    l = last.lower().strip()

    if not f or not l or not domain:
        return []

    fi = f[0]  # first initial
    li = l[0]  # last initial

    return [
        f"{f}.{l}@{domain}",          # john.smith@company.com  (~60%)
        f"{f}{l}@{domain}",           # johnsmith@company.com
        f"{f}@{domain}",              # john@company.com
        f"{fi}{l}@{domain}",          # jsmith@company.com
        f"{f}{li}@{domain}",          # johns@company.com
        f"{f}_{l}@{domain}",          # john_smith@company.com
        f"{l}.{f}@{domain}",          # smith.john@company.com
        f"{l}{f}@{domain}",           # smithjohn@company.com
        f"{fi}.{l}@{domain}",         # j.smith@company.com
        f"{l}@{domain}",              # smith@company.com
    ]


def verify_email_smtp(email: str, mx_host: str, timeout: int = 10) -> bool:
    """
    Verify if an email address exists by talking to the SMTP server.
    Returns True if the server accepts the address, False otherwise.

    NOTE: This does NOT send any email — it just asks the server
    "would you accept mail for this address?" and reads the response code.
    """
    try:
        smtp = smtplib.SMTP(timeout=timeout)
        smtp.connect(mx_host, 25)
        smtp.helo("verify.local")
        smtp.mail("verify@verify.local")
        code, _ = smtp.rcpt(email)
        smtp.quit()
        # 250 = accepted, 251 = forwarded — both mean the address is valid
        return code in (250, 251)
    except Exception:
        return False


def find_email(first_name: str, last_name: str, domain: str) -> str | None:
    """
    Generate email pattern candidates and verify each one via SMTP.
    Returns the first verified email, or the best guess if SMTP is blocked.
    """
    if not all([first_name, last_name, domain]):
        return None

    candidates = generate_patterns(first_name, last_name, domain)
    if not candidates:
        return None

    mx_host = _get_mx_host(domain)

    if not mx_host:
        # No MX record — domain probably doesn't have email.
        # Return best-guess (first.last) but mark it unverified.
        console.print(f"    [dim]No MX record for {domain} — returning best guess[/dim]")
        return candidates[0]  # first.last@domain

    # Try each pattern against the SMTP server
    for email in candidates:
        if verify_email_smtp(email, mx_host):
            return email

    # If SMTP verification didn't confirm any (some servers reject all RCPT
    # checks as an anti-spam measure), return the most-common pattern
    console.print(f"    [dim]SMTP catch-all or blocked — returning best guess[/dim]")
    return candidates[0]
