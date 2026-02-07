# LinkedIn Profile Finder

> **Search → Extract → Enrich → Export** — Find anyone on LinkedIn from a single text query.

Give it a plain-English description like *"VP of Sales at SaaS companies in Boston"* and it will:

1. **Generate** a Google Boolean search string using OpenAI
2. **Scrape** Google for LinkedIn profile results (cookie-auth to bypass bot detection)
3. **Extract** structured data (name, title, company, location) via OpenAI
4. **Enrich** with email addresses via Hunter.io
5. **Export** results to CSV + JSON

---

## Quick Start

### 1. Install dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure API keys

```bash
copy .env.example .env        # Windows
# cp .env.example .env        # Mac/Linux
```

Open `.env` and fill in:

| Key | Where to get it |
|---|---|
| `OPENAI_API_KEY` | [platform.openai.com/api-keys](https://platform.openai.com/api-keys) |
| `HUNTER_API_KEY` | [hunter.io/api-keys](https://hunter.io/api-keys) |
| `GOOGLE_COOKIE` | See instructions below |

### 3. Get your Google Cookie

1. Open **Google.com** in Chrome (logged in to your Google account)
2. Open DevTools → **Network** tab
3. Search for anything
4. Click the first `www.google.com` request
5. In **Request Headers**, copy the entire `Cookie:` value
6. Paste it into `GOOGLE_COOKIE` in your `.env` file

> ⚠️ The cookie expires periodically — refresh it if you start getting CAPTCHA errors.

### 4. Run it

```bash
# Single query
python main.py "Marketing Managers at startups in Austin, Texas"

# Interactive mode (loop of queries)
python main.py --interactive

# Skip email enrichment (no Hunter.io needed)
python main.py --skip-email "Python developers in Berlin"

# Fetch more results
python main.py -n 20 "Freelance UX designers in New York"
```

---

## Project Structure

```
├── main.py                 # CLI entry point (run this)
├── config.py               # Loads .env, validates settings
├── boolean_generator.py    # OpenAI → Google Boolean string
├── google_scraper.py       # Scrapes Google with cookie auth
├── profile_extractor.py    # OpenAI → structured profile data
├── email_enricher.py       # Hunter.io domain + email lookup
├── output_handler.py       # CSV / JSON export + Rich table
├── requirements.txt        # Python dependencies
├── .env.example            # Template for API keys
└── output/                 # Generated results land here
```

## Pipeline Flow

```
┌─────────────┐    ┌──────────────────┐    ┌───────────────┐
│  Your Query  │───▶│  OpenAI Boolean   │───▶│ Google Search  │
│  (any text)  │    │  Generator        │    │ (cookie auth)  │
└─────────────┘    └──────────────────┘    └───────┬───────┘
                                                    │
                   ┌──────────────────┐    ┌───────▼───────┐
                   │   Hunter.io      │◀───│ OpenAI Profile │
                   │   Email Finder   │    │ Extractor      │
                   └────────┬─────────┘    └───────────────┘
                            │
                   ┌────────▼─────────┐
                   │  CSV + JSON      │
                   │  Output          │
                   └──────────────────┘
```

## CLI Options

| Flag | Description |
|---|---|
| `--interactive` / `-i` | Loop mode — keep entering queries |
| `--skip-email` / `-s` | Skip Hunter.io lookup (useful if you only need names) |
| `--num N` / `-n N` | Number of Google results to fetch (default: 10) |

## Example Queries

```
"VP of Sales at SaaS companies in Boston"
"Python developers who speak French"
"Marketing Managers at startups in Austin, Texas"
"Freelance graphic designers in London"
"CTO OR Chief Technology Officer at fintech companies"
"Data Scientists with PhD in San Francisco"
"Product Managers at Series A startups in NYC"
```

## Troubleshooting

| Problem | Fix |
|---|---|
| Google returns CAPTCHA | Refresh `GOOGLE_COOKIE` in `.env` |
| 0 results found | Try a simpler/broader query |
| Hunter.io returns no email | The company domain may be wrong — check the CSV |
| OpenAI rate limit | Wait a minute, or switch to a different model in `.env` |

## License

MIT — use at your own risk. Respect LinkedIn's ToS and rate limits.
