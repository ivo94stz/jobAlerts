import logging

from database import is_seen, mark_seen
from filters import is_relevant
from notifier import send_email, send_no_jobs_email
from scrapers import jobagent, jobscout24, linkedin

log = logging.getLogger(__name__)

SCRAPERS = [linkedin, jobscout24, jobagent]


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

    log.info(f"Check done. {len(new_jobs)} new relevant job(s).")

    if new_jobs:
        send_email(new_jobs)
    elif manual:
        log.info("Manual run — sending 'no new jobs' notification.")
        send_no_jobs_email()
