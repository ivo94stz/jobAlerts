import hashlib
import re
import time

import requests
from bs4 import BeautifulSoup

from .base import Job

SOURCE = "xing.com"
BASE_URL = "https://www.xing.com"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.5",
}

SEARCHES = [
    {"keywords": "talent acquisition", "location": "Zug, Schweiz"},
    {"keywords": "talent acquisition", "location": "Zürich, Schweiz"},
    {"keywords": "recruiter", "location": "Zug, Schweiz"},
    {"keywords": "recruiter", "location": "Zürich, Schweiz"},
    {"keywords": "talent partner", "location": "Zürich, Schweiz"},
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
            print(f"[xing] Error ({cfg['keywords']} / {cfg['location']}): {e}")

    return all_jobs


def _fetch(cfg: dict) -> list:
    resp = requests.get(
        f"{BASE_URL}/jobs/search",
        params={"keywords": cfg["keywords"], "location": cfg["location"]},
        headers=HEADERS,
        timeout=20,
    )
    resp.raise_for_status()

    soup = BeautifulSoup(resp.text, "lxml")
    jobs = []

    # XING server-side renders a subset of job cards
    cards = [
        el for el in soup.find_all(True)
        if any("job-teaser-list-item-styles__Card" in c for c in el.get("class", []))
    ]

    for card in cards:
        try:
            title_el = _find_by_class_prefix(card, "headline-styles__Headline")
            company_el = _find_by_class_prefix(card, "body-copy-styles__BodyCopy")
            location_el = _find_by_class_prefix(card, "multi-location-display-styles__Container")
            link_el = _find_by_class_prefix(card, "card-styles__CardLink", tag="a")

            if not title_el or not link_el:
                continue

            title = title_el.get_text(strip=True)
            company = company_el.get_text(strip=True) if company_el else "Unknown"
            location = location_el.get_text(strip=True).replace("+ 0 more", "").strip() \
                if location_el else cfg["location"]

            href = link_el.get("href", "")
            if not href.startswith("http"):
                href = BASE_URL + href

            match = re.search(r"-(\d+)$", href)
            job_id = match.group(1) if match else hashlib.md5(href.encode()).hexdigest()[:16]

            jobs.append(
                Job(
                    title=title,
                    company=company,
                    location=location,
                    url=href,
                    description=f"{title} {company} {location}",
                    source=SOURCE,
                    job_id=job_id,
                )
            )
        except Exception:
            continue

    return jobs


def _find_by_class_prefix(element, prefix: str, tag: str = None):
    for el in element.find_all(tag or True):
        if any(prefix in c for c in el.get("class", [])):
            return el
    return None
