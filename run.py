"""
Single-run entry point — used by GitHub Actions (and for manual local runs).
Flags:
  --manual  : always run, send 'no new jobs' email if nothing found
  --weekly  : send weekly digest of all jobs found in the last 7 days
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
from job_checker import run_job_check, run_weekly_digest

SEEN_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "seen_jobs.json")
MANUAL = "--manual" in sys.argv or os.getenv("MANUAL_RUN", "").lower() == "true"
WEEKLY = "--weekly" in sys.argv or os.getenv("WEEKLY_DIGEST", "").lower() == "true"

log = logging.getLogger(__name__)

if os.path.exists(SEEN_FILE):
    log.info(f"Loading seen jobs from {SEEN_FILE}")
    import_from_json(SEEN_FILE)

if WEEKLY:
    log.info("Running weekly digest...")
    run_weekly_digest()
else:
    run_job_check(manual=MANUAL)

log.info(f"Saving seen jobs to {SEEN_FILE}")
export_to_json(SEEN_FILE)
