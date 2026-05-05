# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this project does

JobAlerts scrapes 6 Swiss job boards every 2 hours (07:00–17:00 CEST) for Talent Acquisition / Recruiter roles in Kanton Zug and Zürich city, and sends HTML email alerts to milahristova98@gmail.com. It runs entirely on GitHub Actions — no server required.

## Running locally

```bash
pip install -r requirements.txt
cp .env.example .env   # fill in Gmail credentials
python run.py           # single scheduled check (no email if nothing new)
python run.py --manual  # single check, always emails (even "no results")
python run.py --weekly  # send weekly digest
python main.py          # infinite loop with built-in scheduler (local only)
```

`.env` requires `EMAIL_ADDRESS`, `EMAIL_PASSWORD` (Gmail App Password), `EMAIL_TO`.

## Architecture

```
run.py          → GitHub Actions entry point (single run)
main.py         → local infinite-loop scheduler
job_checker.py  → orchestrates scrapers → filters → dedup → email
database.py     → SQLite seen_jobs.db + JSON import/export for cloud persistence
filters.py      → relevance checks (title keywords, location, language)
config.py       → all tunable constants (locations, search terms, patterns)
notifier.py     → builds and sends HTML emails via Gmail SMTP SSL
merge_seen.py   → merges local seen_jobs.json with origin before git push
scrapers/
  base.py       → Job dataclass
  linkedin.py, jobscout24.py, jobagent.py, xing.py, adzuna.py, talent.py
```

### Deduplication (two layers)

1. **Per-site:** `is_seen(source, job_id)` — SQLite `UNIQUE(source, job_id)`
2. **Cross-site:** `is_seen_by_content(title, company)` — `content_key` column stores `normalize(title)||normalize(company)`; catches the same job listed on multiple boards across separate runs

`seen_jobs.json` (committed to git) is the persistence bridge between stateless GitHub Actions runs. It stores `{source, job_id, title, company}`. On each run: import JSON → SQLite → scrape → export SQLite → JSON → commit + push.

`merge_seen.py` runs before each commit to union the local JSON with origin's version, preventing data loss from concurrent runs.

### Filtering pipeline (`filters.py → is_relevant`)

A job passes all four gates in order:
1. Title contains a relevant keyword (see `RELEVANT_TITLE_KEYWORDS` in `filters.py`)
2. Location matches Kanton Zug cities or Zürich city (see `config.py`)
3. Posting language is English (keyword heuristic + `langdetect`)
4. German is not listed as mandatory (regex patterns in `config.py`)

## GitHub Actions workflow

`.github/workflows/job_alerts.yml` — key behaviours:
- `concurrency: group: job-alerts` prevents simultaneous runs
- After `python run.py`, calls `merge_seen.py`, commits, then `git pull --rebase -X ours` before push — handles any race conditions without failing
- Sunday 06:00 UTC triggers `--weekly` instead of a normal check
- Secrets needed: `EMAIL_ADDRESS`, `EMAIL_PASSWORD`, `EMAIL_TO`

## Adding a new scraper

1. Create `scrapers/mysitename.py` with a `scrape() -> list[Job]` function
2. Each `Job` must have a stable `job_id` (prefer numeric ID from URL, not slug)
3. Import and add to `SCRAPERS` list in `job_checker.py`
4. Test locally: `python -c "from scrapers import mysitename; print(mysitename.scrape())"`

## Key constraints

- `data/seen_jobs.db` is in `.gitignore` — never committed; rebuilt from `seen_jobs.json` each run
- LinkedIn job IDs: extracted with `r"(\d{7,})$"` on the URL (not the full slug) — do not change this or existing seen entries become invalid
- `_normalize()` in `database.py` is the single source of truth for text normalisation used in both cross-site dedup and `_dedup_cross_site()` in `job_checker.py`
