import logging
import re

from config import ACCEPTED_LOCATIONS, ENGLISH_REQUIRED_PATTERNS, GERMAN_MANDATORY_PATTERNS
from scrapers.base import Job

log = logging.getLogger(__name__)

try:
    from langdetect import DetectorFactory, detect
    DetectorFactory.seed = 42
    _LANGDETECT = True
except ImportError:
    _LANGDETECT = False

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

# Phrases that signal the posting is written in German
_GERMAN_WRITING = [
    "wir suchen", "ihr profil", "ihre aufgaben", "was wir bieten",
    "stellenbeschreibung", "aufgaben:", "anforderungen:",
    "was sie mitbringen", "arbeitsort", "pensum", "über uns",
    "wir bieten", "stellenanzeige", "ihre bewerbung",
    "freude an", "sie verfügen", "sie bringen",
]

# Phrases that signal French-language posting
_FRENCH_WRITING = [
    "nous recherchons", "votre profil", "vos missions",
    "nous offrons", "description du poste", "profil recherché",
    "lieu de travail", "nous vous offrons",
]


def is_relevant(job: Job) -> bool:
    return (
        _has_relevant_title(job.title)
        and _valid_location(job.location, job.title)
        and _is_english_posting(job.title, job.description)
        and _no_mandatory_german(job.description, job.title)
    )


def _has_relevant_title(title: str) -> bool:
    t = title.lower()
    return any(kw in t for kw in RELEVANT_TITLE_KEYWORDS)


def _valid_location(location: str, title: str) -> bool:
    text = (location + " " + title).lower()
    return any(city in text for city in ACCEPTED_LOCATIONS)


def _is_english_posting(title: str, description: str) -> bool:
    """Returns True only if the job posting is written in English."""
    combined = f"{title} {description}".strip()
    if len(combined) < 30:
        return True  # Too short to determine — don't exclude

    text_lower = combined.lower()

    # Fast keyword check: 2+ German writing phrases → clearly German posting
    german_score = sum(1 for kw in _GERMAN_WRITING if kw in text_lower)
    if german_score >= 2:
        log.debug(f"Skipped (German posting, score={german_score}): {title[:60]}")
        return False

    french_score = sum(1 for kw in _FRENCH_WRITING if kw in text_lower)
    if french_score >= 2:
        log.debug(f"Skipped (French posting): {title[:60]}")
        return False

    # langdetect on longer texts
    if _LANGDETECT and len(combined) > 120:
        try:
            lang = detect(combined[:1500])
            if lang in ("de", "fr", "it", "nl"):
                log.debug(f"Skipped (language={lang}): {title[:60]}")
                return False
        except Exception:
            pass  # Detection failed — don't exclude

    return True


def _no_mandatory_german(description: str, title: str) -> bool:
    """Returns True if German is NOT listed as a mandatory requirement."""
    text = (description + " " + title).lower()
    mandatory = any(re.search(p, text) for p in GERMAN_MANDATORY_PATTERNS)
    if mandatory:
        log.debug(f"Skipped (German mandatory): {title[:60]}")
        return False
    return True
