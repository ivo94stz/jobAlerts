import hashlib
import re
import time

import requests
from bs4 import BeautifulSoup

from .base import Job

SOURCE = "talent.com"
BASE_URL = "https://ch.talent.com"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Accept-Language": "en-US,en;q=0.9",
}

SEARCHES = [
    {"k": "talent acquisition", "l": "Zug", "radius": "15"},
    {"k": "talent acquisition recruiter", "l": "Zurich", "radius": "20"},
    {"k": "talent partner hr recruiter", "l": "Zurich", "radius": "20"},
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
            time.sleep(2)
        except Exception as e:
            print(f"[talent] Error ({cfg['k']} / {cfg['l']}): {e}")

    return all_jobs


def _search(cfg: dict) -> list:
    resp = requests.get(
        f"{BASE_URL}/en/jobs",
        params=cfg,
        headers=HEADERS,
        timeout=20,
    )
    resp.raise_for_status()

    soup = BeautifulSoup(resp.text, "lxml")
    jobs = []

    # talent.com SSR cards — Next.js CSS Module class prefix is stable
    cards = [
        el for el in soup.find_all(True)
        if any("JobCard_card__" in c for c in el.get("class", []))
    ]

    for card in cards:
        try:
            title_el = _by_prefix(card, "JobCard_title__")
            company_el = _by_prefix(card, "JobCard_company__")
            location_el = _by_prefix(card, "JobCard_location__")
            link_el = card.find_parent("a") or card.select_one("a[href*='/view']")

            if not title_el or not link_el:
                continue

            href = link_el.get("href", "")
            if not href.startswith("http"):
                href = BASE_URL + href

            match = re.search(r"id=(\d+)", href)
            job_id = match.group(1) if match else hashlib.md5(href.encode()).hexdigest()[:16]

            jobs.append(
                Job(
                    title=title_el.get_text(strip=True),
                    company=company_el.get_text(strip=True) if company_el else "Unknown",
                    location=location_el.get_text(strip=True) if location_el else cfg["l"],
                    url=href,
                    description=card.get_text(separator=" ", strip=True)[:1500],
                    source=SOURCE,
                    job_id=job_id,
                )
            )
        except Exception:
            continue

    return jobs


def _by_prefix(element, prefix: str):
    for el in element.find_all(True):
        if any(prefix in c for c in el.get("class", [])):
            return el
    return None
