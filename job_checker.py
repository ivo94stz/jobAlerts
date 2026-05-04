import logging
import re

from database import is_seen, mark_seen
from filters import is_relevant
from notifier import send_email, send_no_jobs_email, send_weekly_digest
from scrapers import adzuna, jobagent, jobscout24, linkedin, talent, xing

log = logging.getLogger(__name__)

SCRAPERS = [linkedin, jobscout24, jobagent, xing, adzuna, talent]


def run_job_check(manual: bool = False):
    new_jobs = []

    for scraper in SCRAPERS:
        name = scraper.__name__.split(".")[-1]
        try:
            log.info(f"Scraping {name}...")
            jobs = scraper.scrape()
            log.info(f"[{name}] fetched {len(jobs)} listing(s)")

            for job in jobs:
                already_seen = is_seen(job.source, job.job_id)
                mark_seen(job.source, job.job_id, job.title, job.company, job.url)

                if already_seen:
                    continue

                if is_relevant(job):
                    log.info(f"[{name}] NEW  : {job.title} @ {job.company} ({job.location})")
                    new_jobs.append(job)
                else:
                    log.debug(f"[{name}] skip : {job.title} @ {job.location} (filtered)")

        except Exception as e:
            log.error(f"[{name}] scraper error: {e}", exc_info=True)

    # Cross-site deduplication: same title + company from multiple sources → keep first
    new_jobs = _dedup_cross_site(new_jobs)

    log.info(f"Check done. {len(new_jobs)} new relevant job(s).")

    if new_jobs:
        send_email(new_jobs)
    elif manual:
        log.info("Manual run — sending 'no new jobs' notification.")
        send_no_jobs_email()


def run_weekly_digest():
    from database import get_jobs_last_7_days
    jobs = get_jobs_last_7_days()
    log.info(f"Weekly digest: {len(jobs)} job(s) found in the last 7 days.")
    send_weekly_digest(jobs)


def _dedup_cross_site(jobs: list) -> list:
    """Remove duplicate jobs that appear on multiple sources (same title + company)."""
    seen_keys: set = set()
    result = []
    for job in jobs:
        key = (_normalize(job.title), _normalize(job.company))
        if key not in seen_keys:
            seen_keys.add(key)
            result.append(job)
        else:
            log.debug(f"Cross-site dup removed: {job.title} @ {job.company} ({job.source})")
    return result


_LEGAL_SUFFIXES = re.compile(
    r"\b(ag|gmbh|ltd|sa|llc|inc|corp|se|nv|bv|plc|srl|oy|ab|as)\b", re.I
)


def _normalize(text: str) -> str:
    text = text.lower().strip()
    text = _LEGAL_SUFFIXES.sub("", text)
    text = re.sub(r"[^\w\s]", "", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text
