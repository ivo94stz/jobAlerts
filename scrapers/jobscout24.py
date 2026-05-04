import hashlib
import re
import time

import requests
from bs4 import BeautifulSoup

from .base import Job

SOURCE = "jobscout24.ch"
BASE_URL = "https://www.jobscout24.ch"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Accept-Language": "en-US,en;q=0.9",
}

SEARCHES = [
    {"q": "talent acquisition", "location": "Zug"},
    {"q": "talent partner", "location": "Zug"},
    {"q": "recruiter", "location": "Zug"},
    {"q": "talent acquisition", "location": "Zurich"},
    {"q": "talent partner", "location": "Zurich"},
    {"q": "recruiter", "location": "Zurich"},
]


def scrape():
    all_jobs = []
    seen_ids: set = set()

    for cfg in SEARCHES:
        try:
            jobs = _search(cfg)
            for job in jobs:
                if job.job_id not in seen_ids:
                    seen_ids.add(job.job_id)
                    all_jobs.append(job)
            time.sleep(1.5)
        except Exception as e:
            print(f"[jobscout24] Error ({cfg['q']} / {cfg['location']}): {e}")

    return all_jobs


def _search(cfg: dict) -> list:
    resp = requests.get(
        f"{BASE_URL}/en/jobs/",
        params={"q": cfg["q"], "location": cfg["location"]},
        headers=HEADERS,
        timeout=15,
    )
    resp.raise_for_status()

    soup = BeautifulSoup(resp.text, "lxml")
    jobs = []

    for card in soup.select("li.job-list-item"):
        try:
            title_el = card.select_one("a.job-title, a.job-link-detail")
            attrs = card.select("p.job-attributes span")
            company = attrs[0].get_text(strip=True) if len(attrs) > 0 else "Unknown"
            location = attrs[1].get_text(strip=True) if len(attrs) > 1 else cfg["location"]

            if not title_el:
                continue

            href = title_el.get("href", "")
            if not href.startswith("http"):
                href = BASE_URL + href

            job_id = _extract_id(href)

            jobs.append(
                Job(
                    title=title_el.get_text(strip=True),
                    company=company,
                    location=location,
                    url=href,
                    description=card.get_text(separator=" ", strip=True)[:1500],
                    source=SOURCE,
                    job_id=job_id,
                )
            )
        except Exception:
            continue

    return jobs


def _extract_id(url: str) -> str:
    match = re.search(r"/(\d{5,})(?:/|$|\?)", url)
    if match:
        return match.group(1)
    return hashlib.md5(url.encode()).hexdigest()[:16]
