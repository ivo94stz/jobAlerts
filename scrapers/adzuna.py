import hashlib
import re
import time

import requests
from bs4 import BeautifulSoup

from .base import Job

SOURCE = "adzuna.ch"
BASE_URL = "https://www.adzuna.ch"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Accept-Language": "en-US,en;q=0.9",
}

SEARCHES = [
    {"q": "talent acquisition recruiter", "where": "Zug"},
    {"q": "talent acquisition recruiter", "where": "Zurich"},
    {"q": "talent partner hr recruiter", "where": "Zurich"},
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
            print(f"[adzuna] Error ({cfg['where']}): {e}")

    return all_jobs


def _search(cfg: dict) -> list:
    resp = requests.get(
        f"{BASE_URL}/search",
        params=cfg,
        headers=HEADERS,
        timeout=20,
    )
    resp.raise_for_status()
    resp.encoding = resp.apparent_encoding or "utf-8"

    soup = BeautifulSoup(resp.text, "lxml")
    jobs = []

    # Each job card has an h2 with the title link
    for title_link in soup.select("h2 a"):
        try:
            href = title_link.get("href", "")
            if not href or "adzuna.ch" not in href:
                continue
            if "terms" in href or "privacy" in href:
                continue

            title = title_link.get_text(strip=True)
            if not title:
                continue

            # Walk up to find the card container
            card = title_link.find_parent("div", class_=True)
            for _ in range(4):
                if card and card.find("div", class_="ui-company"):
                    break
                card = card.find_parent("div", class_=True) if card else None

            company_el = card.select_one("div.ui-company") if card else None
            info_el = card.select_one("div.ui-job-card-info") if card else None

            company = company_el.get_text(strip=True) if company_el else "Unknown"

            # Location: second div inside ui-job-card-info
            location = cfg["where"]
            if info_el:
                parts = info_el.find_all("div", recursive=False)
                if len(parts) >= 2:
                    location = parts[1].get_text(strip=True).split(",")[0].strip()

            match = re.search(r"/(\d+)(?:/|$|\?)", href)
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
