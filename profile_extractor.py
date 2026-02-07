"""
Profile Extractor — uses OpenAI to pull structured fields from raw
Google search result snippets.
"""

import json
from openai import OpenAI
from dataclasses import dataclass, asdict

import config
from google_scraper import SearchResult

SYSTEM_PROMPT = """You are a data-extraction assistant.

I will give you a Google search result (title + snippet) from a LinkedIn profile page.
Extract the following fields as JSON. If a field is not available, use null.

{
  "person_name":      "Full name of the person",
  "first_name":       "First name only",
  "last_name":        "Last name only",
  "job_title":        "Current or most-recent job title",
  "company_name":     "Current or most-recent company name",
  "location":         "City / region if mentioned",
  "context_snippet":  "One sentence explaining why this person matched the search"
}

Rules:
- Return ONLY valid JSON. No markdown fences, no extra text.
- person_name comes from the LinkedIn title (usually "FirstName LastName – Title").
- If the title has "| LinkedIn" or "- LinkedIn", strip that suffix.
- Derive first_name and last_name from person_name.
- company_name is critical — extract it even if approximate.
"""


@dataclass
class ProfileData:
    person_name: str | None
    first_name: str | None
    last_name: str | None
    job_title: str | None
    company_name: str | None
    location: str | None
    context_snippet: str | None
    linkedin_url: str | None

    def to_dict(self) -> dict:
        return asdict(self)


def extract_profiles(results: list[SearchResult]) -> list[ProfileData]:
    """
    Given a list of Google search results, use OpenAI to extract structured
    profile information from each one.
    """
    if not results:
        return []

    client = OpenAI(api_key=config.OPENAI_API_KEY)
    profiles: list[ProfileData] = []

    for r in results:
        user_content = f"Title: {r.title}\nSnippet: {r.snippet}\nURL: {r.url}"

        try:
            resp = client.chat.completions.create(
                model=config.OPENAI_MODEL,
                temperature=0.0,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": user_content},
                ],
            )
            raw = resp.choices[0].message.content.strip()

            # Strip markdown fences if present
            if raw.startswith("```"):
                raw = raw.split("\n", 1)[-1]
            if raw.endswith("```"):
                raw = raw.rsplit("```", 1)[0]
            raw = raw.strip()

            data = json.loads(raw)
            profiles.append(
                ProfileData(
                    person_name=data.get("person_name"),
                    first_name=data.get("first_name"),
                    last_name=data.get("last_name"),
                    job_title=data.get("job_title"),
                    company_name=data.get("company_name"),
                    location=data.get("location"),
                    context_snippet=data.get("context_snippet"),
                    linkedin_url=r.url,
                )
            )
        except (json.JSONDecodeError, Exception) as exc:
            # If one result fails, skip it but keep going
            profiles.append(
                ProfileData(
                    person_name=r.title.replace(" | LinkedIn", "").replace(" - LinkedIn", ""),
                    first_name=None,
                    last_name=None,
                    job_title=None,
                    company_name=None,
                    location=None,
                    context_snippet=r.snippet[:200] if r.snippet else None,
                    linkedin_url=r.url,
                )
            )

    return profiles
