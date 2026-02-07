"""
Configuration loader — reads .env and exposes settings with validation.
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Load .env from project root
_env_path = Path(__file__).resolve().parent / ".env"
load_dotenv(_env_path)


def _require(key: str) -> str:
    val = os.getenv(key, "").strip()
    if not val or val.startswith("your-") or val.startswith("sk-your"):
        return ""
    return val


# ── OpenAI ───────────────────────────────────────────────────────────────────
OPENAI_API_KEY: str = _require("OPENAI_API_KEY")
OPENAI_MODEL: str = os.getenv("OPENAI_MODEL", "gpt-4o-mini").strip()

# ── Hunter.io ────────────────────────────────────────────────────────────────
HUNTER_API_KEY: str = _require("HUNTER_API_KEY")

# ── Google Scraping ──────────────────────────────────────────────────────────
GOOGLE_COOKIE: str = _require("GOOGLE_COOKIE")
GOOGLE_USER_AGENT: str = os.getenv(
    "GOOGLE_USER_AGENT",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
).strip()
GOOGLE_NUM_RESULTS: int = int(os.getenv("GOOGLE_NUM_RESULTS", "10"))
GOOGLE_DELAY_SECONDS: float = float(os.getenv("GOOGLE_DELAY_SECONDS", "3"))

# ── Output ───────────────────────────────────────────────────────────────────
OUTPUT_FORMAT: str = os.getenv("OUTPUT_FORMAT", "both").strip().lower()
OUTPUT_DIR: str = os.getenv("OUTPUT_DIR", "./output").strip()


def validate(require_hunter: bool = True) -> list[str]:
    """Return a list of missing-config error messages (empty = all good)."""
    errors: list[str] = []
    if not OPENAI_API_KEY:
        errors.append("OPENAI_API_KEY is missing in .env")
    if not GOOGLE_COOKIE:
        errors.append("GOOGLE_COOKIE is missing in .env")
    if require_hunter and not HUNTER_API_KEY:
        errors.append("HUNTER_API_KEY is missing in .env (needed for email lookup)")
    return errors
