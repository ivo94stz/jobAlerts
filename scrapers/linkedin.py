import re
import time

import requests
from bs4 import BeautifulSoup

from .base import Job

SOURCE = "linkedin.com"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.5",
}

SEARCHES = [
    {"keywords": "talent acquisition", "location": "Zug, Switzerland"},
    {"keywords": "talent acquisition partner", "location": "Zug, Switzerland"},
    {"keywords": "recruiter", "location": "Zug, Switzerland"},
    {"keywords": "talent acquisition", "location": "Zurich, Switzerland"},
    {"keywords": "talent acquisition manager", "location": "Zurich, Switzerland"},
    {"keywords": "recruiter", "location": "Zurich, Switzerland"},
]


def scrape():
    all_jobs = []
    seen_ids: set = set()

    for cfg in SEARCHES:
        try:
            jobs = _fetch(cfg)
            for job in jobs:
                if job.job_id not in seen_ids:
                    seen_ids.add(job.job_id)
                    all_jobs.append(job)
            time.sleep(2)
        except Exception as e:
            print(f"[linkedin] Error ({cfg['keywords']} / {cfg['location']}): {e}")

    return all_jobs


def _fetch(cfg: dict) -> list:
    resp = requests.get(
        "https://www.linkedin.com/jobs-guest/jobs/api/seeMoreJobPostings/search",
        params={"keywords": cfg["keywords"], "location": cfg["location"], "start": 0, "count": 25},
        headers=HEADERS,
        timeout=20,
    )
    resp.raise_for_status()

    soup = BeautifulSoup(resp.text, "lxml")
    jobs = []

    for card in soup.select("li"):
        try:
            title_el = card.select_one(".base-search-card__title, h3.base-search-card__title")
            company_el = card.select_one(".base-search-card__subtitle, h4.base-search-card__subtitle")
            location_el = card.select_one(".job-search-card__location, span.job-search-card__location")
            link_el = card.select_one("a.base-card__full-link, a[href*='/jobs/view/']")

            if not title_el or not link_el:
                continue

            href = link_el.get("href", "").split("?")[0]
            match = re.search(r"/jobs/view/(\d+)", href)
            job_id = match.group(1) if match else href[-20:]

            jobs.append(
                Job(
                    title=title_el.get_text(strip=True),
                    company=company_el.get_text(strip=True) if company_el else "Unknown",
                    location=location_el.get_text(strip=True) if location_el else cfg["location"],
                    url=href,
                    description=card.get_text(separator=" ", strip=True)[:1500],
                    source=SOURCE,
                    job_id=job_id,
                )
            )
        except Exception:
            continue

    return jobs
