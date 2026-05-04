import os
from dotenv import load_dotenv

load_dotenv()

EMAIL_ADDRESS = os.getenv("EMAIL_ADDRESS", "")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD", "")
EMAIL_TO = os.getenv("EMAIL_TO", "")

SCHEDULE_INTERVAL_HOURS = 2
SCHEDULE_START_HOUR = 7
SCHEDULE_END_HOUR = 17
TIMEZONE = "Europe/Zurich"

SEARCH_TERMS = ["talent acquisition", "recruiter", "talent partner"]

ZUG_CITIES = [
    "zug", "baar", "cham", "risch", "rotkreuz", "hunenberg", "hünenberg",
    "steinhausen", "menzingen", "neuheim", "oberägeri", "oberageri",
    "unterägeri", "unterageri", "walchwil", "canton zug", "kanton zug",
]

ZURICH_CITY = ["zürich", "zurich", "city of zurich"]

ACCEPTED_LOCATIONS = ZUG_CITIES + ZURICH_CITY

ENGLISH_REQUIRED_PATTERNS = [
    r"english\s+(is\s+)?(required|mandatory|a must|essential)",
    r"(fluent|proficient|native|excellent|strong)\s+(in\s+)?english",
    r"english\s+(fluency|proficiency|level)",
    r"english[\s\-]speaking",
    r"working\s+language[^.]*english",
    r"language[^.]*english[^.]*required",
    r"business\s+english",
]

GERMAN_MANDATORY_PATTERNS = [
    r"german\s+(is\s+)?(required|mandatory|a must|essential|zwingend)",
    r"(native|muttersprache)\s+(german|deutsch)",
    r"deutsch\s+muttersprache",
    r"(c1|c2)\s+german",
    r"german\s+(c1|c2)",
    r"flie.end\s+deutsch",
    r"deutschkenntnisse\s+(zwingend|erforderlich)",
]
