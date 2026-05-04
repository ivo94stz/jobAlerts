import logging
import sys
import time
from datetime import datetime

import pytz
import schedule

from config import SCHEDULE_END_HOUR, SCHEDULE_INTERVAL_HOURS, SCHEDULE_START_HOUR, TIMEZONE
from job_checker import run_job_check

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler("jobalerts.log", encoding="utf-8"),
        logging.StreamHandler(sys.stdout),
    ],
)
log = logging.getLogger(__name__)


def _in_working_hours() -> bool:
    tz = pytz.timezone(TIMEZONE)
    hour = datetime.now(tz).hour
    return SCHEDULE_START_HOUR <= hour <= SCHEDULE_END_HOUR


def _scheduled_task():
    if _in_working_hours():
        run_job_check()
    else:
        log.info(
            f"Outside working hours ({SCHEDULE_START_HOUR}:00–{SCHEDULE_END_HOUR}:00 CET). Skipping."
        )


schedule.every(SCHEDULE_INTERVAL_HOURS).hours.do(_scheduled_task)

if __name__ == "__main__":
    log.info("=" * 55)
    log.info("JobAlerts started")
    log.info(f"Schedule : every {SCHEDULE_INTERVAL_HOURS}h | {SCHEDULE_START_HOUR}:00–{SCHEDULE_END_HOUR}:00 CET")
    log.info(f"Notify   : {__import__('config').EMAIL_TO}")
    log.info("=" * 55)

    if _in_working_hours():
        log.info("Running initial check immediately...")
        run_job_check()
    else:
        log.info("Started outside working hours — first check at next scheduled slot.")

    while True:
        schedule.run_pending()
        time.sleep(60)
