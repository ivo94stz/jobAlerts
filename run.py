"""
Single-run entry point — used by GitHub Actions (and for manual local runs).
Loads seen-jobs from JSON (cloud persistence), runs one check, saves back.
"""
import logging
import os
import sys

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)

from database import export_to_json, import_from_json
from job_checker import run_job_check

SEEN_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "seen_jobs.json")
MANUAL = "--manual" in sys.argv or os.getenv("MANUAL_RUN", "").lower() == "true"

log = logging.getLogger(__name__)

if os.path.exists(SEEN_FILE):
    log.info(f"Loading seen jobs from {SEEN_FILE}")
    import_from_json(SEEN_FILE)

run_job_check(manual=MANUAL)

log.info(f"Saving seen jobs to {SEEN_FILE}")
export_to_json(SEEN_FILE)
