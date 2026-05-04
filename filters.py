import re

from config import ACCEPTED_LOCATIONS, ENGLISH_REQUIRED_PATTERNS, GERMAN_MANDATORY_PATTERNS
from scrapers.base import Job

RELEVANT_TITLE_KEYWORDS = [
    "talent acquisition",
    "talent partner",
    "talent manager",
    "talent specialist",
    "recruiter",
    "recruiting",
    "recruitment",
    "head of talent",
    "hr partner",
    "hr specialist",
    "hr manager",
    "human resources",
    "people partner",
    "people acquisition",
    "sourcer",
    "sourcing",
]


def is_relevant(job: Job) -> bool:
    return (
        _has_relevant_title(job.title)
        and _valid_location(job.location, job.title)
        and _passes_language(job.description, job.title)
    )


def _has_relevant_title(title: str) -> bool:
    t = title.lower()
    return any(kw in t for kw in RELEVANT_TITLE_KEYWORDS)


def _valid_location(location: str, title: str) -> bool:
    text = (location + " " + title).lower()
    return any(city in text for city in ACCEPTED_LOCATIONS)


def _passes_language(description: str, title: str) -> bool:
    if not description and not title:
        return True

    text = (description + " " + title).lower()

    english_required = any(re.search(p, text) for p in ENGLISH_REQUIRED_PATTERNS)
    if english_required:
        return True

    # Strict German requirement without English as alternative
    german_strict = any(re.search(p, text) for p in GERMAN_MANDATORY_PATTERNS)
    if german_strict and "english" not in text:
        return False

    # Default: include (no language requirement or unclear)
    return True
