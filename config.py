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


# ── AI Provider ──────────────────────────────────────────────────────────────
# "groq" (free, recommended) | "gemini" (free) | "openai" (paid)
AI_PROVIDER: str = os.getenv("AI_PROVIDER", "groq").strip().lower()

# ── Groq (free — only needed if AI_PROVIDER=groq) ───────────────────────────
GROQ_API_KEY: str = _require("GROQ_API_KEY")
GROQ_MODEL: str = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile").strip()

# ── OpenAI (only needed if AI_PROVIDER=openai) ──────────────────────────────
OPENAI_API_KEY: str = _require("OPENAI_API_KEY")
OPENAI_MODEL: str = os.getenv("OPENAI_MODEL", "gpt-4o-mini").strip()

# ── Google Gemini (only needed if AI_PROVIDER=gemini) ────────────────────────
GEMINI_API_KEY: str = _require("GEMINI_API_KEY")
GEMINI_MODEL: str = os.getenv("GEMINI_MODEL", "gemini-2.0-flash").strip()

# ── Hunter.io (optional — only needed if EMAIL_METHOD=hunter) ────────────────
HUNTER_API_KEY: str = _require("HUNTER_API_KEY")

# ── Email method ─────────────────────────────────────────────────────────────
# "auto"   = free pattern guess + SMTP first, Hunter.io fallback (default)
# "guess"  = free pattern guess + SMTP only (no API key needed)
# "hunter" = Hunter.io only
EMAIL_METHOD: str = os.getenv("EMAIL_METHOD", "auto").strip().lower()

# ── SerpAPI (100 free searches/month) ────────────────────────────────────────
SERPAPI_KEY: str = _require("SERPAPI_KEY")
GOOGLE_NUM_RESULTS: int = int(os.getenv("GOOGLE_NUM_RESULTS", "10"))
GOOGLE_DELAY_SECONDS: float = float(os.getenv("GOOGLE_DELAY_SECONDS", "2"))

# ── Output ───────────────────────────────────────────────────────────────────
OUTPUT_FORMAT: str = os.getenv("OUTPUT_FORMAT", "both").strip().lower()
OUTPUT_DIR: str = os.getenv("OUTPUT_DIR", "./output").strip()


def validate(skip_email: bool = False) -> list[str]:
    """Return a list of missing-config error messages (empty = all good)."""
    errors: list[str] = []
    if AI_PROVIDER == "groq" and not GROQ_API_KEY:
        errors.append("GROQ_API_KEY is missing in .env (required when AI_PROVIDER=groq)")
    if AI_PROVIDER == "openai" and not OPENAI_API_KEY:
        errors.append("OPENAI_API_KEY is missing in .env (required when AI_PROVIDER=openai)")
    if AI_PROVIDER == "gemini" and not GEMINI_API_KEY:
        errors.append("GEMINI_API_KEY is missing in .env (required when AI_PROVIDER=gemini)")
    if not SERPAPI_KEY:
        errors.append("SERPAPI_KEY is missing in .env")
    if not skip_email and EMAIL_METHOD == "hunter" and not HUNTER_API_KEY:
        errors.append("HUNTER_API_KEY is missing in .env (required when EMAIL_METHOD=hunter)")
    return errors
