"""
Single-run entry point — used by GitHub Actions (and for manual local runs).
Flags:
  --manual  : always run, send 'no new jobs' email if nothing found
  --weekly  : send weekly digest of all jobs found in the last 7 days
"""
import json
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

SEEN_FILE   = os.path.join(os.path.dirname(os.path.abspath(__file__)), "seen_jobs.json")
CONFIG_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "schedule_config.json")
MANUAL = "--manual" in sys.argv or os.getenv("MANUAL_RUN", "").lower() == "true"
WEEKLY = "--weekly" in sys.argv or os.getenv("WEEKLY_DIGEST", "").lower() == "true"

log = logging.getLogger(__name__)


def _should_run_now() -> bool:
    """Return False if schedule_config.json says this day/hour is inactive."""
    if not os.path.exists(CONFIG_FILE):
        return True
    try:
        with open(CONFIG_FILE) as f:
            cfg = json.load(f)
    except Exception:
        return True

    if not cfg.get("active", True):
        log.info("Schedule disabled in config — skipping.")
        return False

    import pytz
    from datetime import datetime
    tz  = pytz.timezone("Europe/Zurich")
    now = datetime.now(tz)

    days = cfg.get("days", list(range(1, 8)))
    if now.isoweekday() not in days:
        log.info(f"Not scheduled for {now.strftime('%A')} — skipping.")
        return False

    start_h  = cfg.get("start_hour_cest", 7)
    end_h    = cfg.get("end_hour_cest",   17)
    interval = max(1, cfg.get("interval_hours", 2))
    active_hours = list(range(start_h, end_h, interval))

    if now.hour not in active_hours:
        log.info(f"Not scheduled at {now.hour:02d}:xx CEST (active: {active_hours}) — skipping.")
        return False

    return True


if os.path.exists(SEEN_FILE):
    log.info(f"Loading seen jobs from {SEEN_FILE}")
    import_from_json(SEEN_FILE)

if not MANUAL and not WEEKLY and not _should_run_now():
    sys.exit(0)

if WEEKLY:
    log.info("Running weekly digest...")
    run_weekly_digest()
else:
    run_job_check(manual=MANUAL)

log.info(f"Saving seen jobs to {SEEN_FILE}")
export_to_json(SEEN_FILE)
