import hashlib
import re
import time

import requests
from bs4 import BeautifulSoup

from .base import Job

SOURCE = "jobagent.ch"
BASE_URL = "https://www.jobagent.ch"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Accept-Language": "en-US,en;q=0.9",
}

# Province codes: ZG = Kanton Zug, ZH = Kanton Zürich
PROVINCES = ["ZG", "ZH"]
SEARCH_TERMS = ["talent acquisition", "recruiter", "talent partner"]


def scrape():
    all_jobs = []
    seen_ids: set = set()
    session = requests.Session()
    session.headers.update(HEADERS)

    # Warm-up request to get cookies and avoid 403
    try:
        session.get("https://www.jobagent.ch/", timeout=10)
        time.sleep(2)
    except Exception:
        pass

    for term in SEARCH_TERMS:
        try:
            jobs = _search(term, session)
            for job in jobs:
                if job.job_id not in seen_ids:
                    seen_ids.add(job.job_id)
                    all_jobs.append(job)
            time.sleep(3)
        except Exception as e:
            print(f"[jobagent] Error ({term}): {e}")

    return all_jobs


def _search(term: str, session: requests.Session = None) -> list:
    params = [("terms", term)] + [("provinces", p) for p in PROVINCES]
    caller = session or requests

    resp = caller.get(
        f"{BASE_URL}/search",
        params=params,
        timeout=15,
    )
    resp.raise_for_status()
    resp.encoding = resp.apparent_encoding or "utf-8"

    soup = BeautifulSoup(resp.text, "lxml")
    jobs = []

    for card in soup.select("li.item"):
        try:
            title_el = card.select_one("span.jobtitle, a.jobtitle, h2, h3")
            company_el = card.select_one("span.company")
            location_el = card.select_one("span.location, span.city")
            link_el = card.select_one("a[href*='/job/']") or card.select_one("a[href]")

            if not title_el or not link_el:
                continue

            href = link_el.get("href", "")
            if not href.startswith("http"):
                href = BASE_URL + href

            match = re.search(r"/job/(\d+)", href)
            job_id = match.group(1) if match else hashlib.md5(href.encode()).hexdigest()[:16]

            jobs.append(
                Job(
                    title=title_el.get_text(strip=True),
                    company=company_el.get_text(strip=True) if company_el else "Unknown",
                    location=location_el.get_text(strip=True) if location_el else "",
                    url=href,
                    description=card.get_text(separator=" ", strip=True)[:1500],
                    source=SOURCE,
                    job_id=job_id,
                )
            )
        except Exception:
            continue

    return jobs
