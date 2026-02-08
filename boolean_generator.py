"""
Boolean Generator — uses AI (Gemini or OpenAI) to convert a free-form
query into a Google Boolean search string targeting LinkedIn profiles.
"""

import ai_client

SYSTEM_PROMPT = """You are an expert researcher and Boolean search specialist.

I will give you a target audience description. Your goal is to write a Google
Boolean search string to find LinkedIn profiles that match this audience.

Rules:
1. ALWAYS start with:  site:linkedin.com/in/
2. Use AND to combine required terms (role, industry, location, skills).
3. Use OR (in parentheses) for synonyms, e.g. (VP OR "Vice President").
4. Use "quotes" for exact multi-word phrases like "machine learning".
5. Use intitle: when you want the term in the page title (LinkedIn headline).
6. For locations, add the city/state/country as an AND term.
7. Keep the string concise — no more than ~200 characters.
8. Return ONLY the boolean string. No explanation, no markdown, no commentary.

Examples:
  Query: "VP of Sales at SaaS companies in Boston"
  Output: site:linkedin.com/in/ AND intitle:(VP OR "Vice President") AND Sales AND SaaS AND Boston

  Query: "Python developers who speak French"
  Output: site:linkedin.com/in/ AND (Python OR "Python developer") AND French

  Query: "Marketing Managers at startups in Austin, Texas"
  Output: site:linkedin.com/in/ AND intitle:"Marketing Manager" AND startup AND Austin AND Texas
"""


def generate(query: str) -> str:
    """
    Takes a free-form audience description and returns a Google Boolean search
    string targeting LinkedIn profiles.
    """
    boolean_string = ai_client.chat(
        system_prompt=SYSTEM_PROMPT,
        user_message=query,
        temperature=0.2,
    )

    # Strip markdown code fences if the model wraps the answer
    for fence in ("```", "`"):
        boolean_string = boolean_string.strip(fence)
    boolean_string = boolean_string.strip()

    return boolean_string
