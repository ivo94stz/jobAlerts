import logging
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import List

from config import EMAIL_ADDRESS, EMAIL_PASSWORD, EMAIL_TO
from scrapers.base import Job

log = logging.getLogger(__name__)


def send_no_jobs_email():
    """Send a 'nothing found' reply for manual runs."""
    _send(
        subject="JobAlerts — No new positions found",
        html=f"""
<!DOCTYPE html>
<html>
<body style="margin:0;padding:20px;background:#f4f4f4;font-family:Arial,sans-serif;">
  <div style="max-width:620px;margin:auto;">
    <div style="background:#0a66c2;padding:20px 24px;border-radius:8px 8px 0 0;">
      <h2 style="margin:0;color:#fff;font-size:20px;">JobAlerts — Manual Check</h2>
      <p style="margin:4px 0 0;color:#cde4f7;font-size:13px;">
        Talent Acquisition &amp; Recruiter — Kanton Zug &amp; Stadt Zürich
      </p>
    </div>
    <div style="background:#fff;border-radius:0 0 8px 8px;padding:24px 20px;
                box-shadow:0 2px 8px rgba(0,0,0,.08);text-align:center;">
      <p style="font-size:15px;color:#444;margin:0 0 8px;">
        No new positions matching your criteria were found at this time.
      </p>
      <p style="font-size:13px;color:#999;margin:0;">
        LinkedIn &bull; jobscout24.ch &bull; jobagent.ch &mdash; all checked.
      </p>
    </div>
  </div>
</body>
</html>
""",
    )


def send_email(jobs: List[Job]):
    if not jobs:
        return

    count = len(jobs)
    subject = f"JobAlerts — {count} new position{'s' if count > 1 else ''} | Talent Acquisition | Zug & Zürich"

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = EMAIL_ADDRESS
    msg["To"] = EMAIL_TO
    msg.attach(MIMEText(_build_html(jobs), "html", "utf-8"))

    _send(subject=subject, html=_build_html(jobs))
    log.info(f"Email sent: {count} job(s)")


def _send(subject: str, html: str):
    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = EMAIL_ADDRESS
    msg["To"] = EMAIL_TO
    msg.attach(MIMEText(html, "html", "utf-8"))
    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
            server.sendmail(EMAIL_ADDRESS, [EMAIL_TO], msg.as_string())
    except Exception as e:
        log.error(f"Email failed: {e}")


def _build_html(jobs: List[Job]) -> str:
    rows = ""
    for job in jobs:
        rows += f"""
        <tr>
          <td style="padding:14px 16px;border-bottom:1px solid #f0f0f0;">
            <a href="{job.url}"
               style="font-size:15px;font-weight:600;color:#0a66c2;text-decoration:none;">
              {job.title}
            </a><br>
            <span style="color:#333;font-size:13px;">&#127970; {job.company}</span>
            &nbsp;&nbsp;
            <span style="color:#555;font-size:13px;">&#128205; {job.location}</span><br>
            <span style="color:#999;font-size:11px;margin-top:4px;display:inline-block;">
              via {job.source}
            </span>
          </td>
        </tr>
        """

    return f"""
<!DOCTYPE html>
<html>
<body style="margin:0;padding:20px;background:#f4f4f4;font-family:Arial,sans-serif;">
  <div style="max-width:620px;margin:auto;">

    <div style="background:#0a66c2;padding:20px 24px;border-radius:8px 8px 0 0;">
      <h2 style="margin:0;color:#fff;font-size:20px;">JobAlerts</h2>
      <p style="margin:4px 0 0;color:#cde4f7;font-size:13px;">
        Talent Acquisition &amp; Recruiter — Kanton Zug &amp; Stadt Zürich
      </p>
    </div>

    <div style="background:#fff;border-radius:0 0 8px 8px;overflow:hidden;
                box-shadow:0 2px 8px rgba(0,0,0,.08);">
      <table style="width:100%;border-collapse:collapse;">
        {rows}
      </table>
      <div style="padding:14px 16px;background:#fafafa;
                  border-top:1px solid #eee;text-align:center;
                  color:#aaa;font-size:11px;">
        Автоматично генерирано от JobAlerts &bull; проверява на всеки 2 часа (07:00–17:00 CET)
      </div>
    </div>

  </div>
</body>
</html>
"""
