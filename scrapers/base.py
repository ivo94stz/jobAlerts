from dataclasses import dataclass
from typing import Optional


@dataclass
class Job:
    title: str
    company: str
    location: str
    url: str
    description: str
    source: str
    job_id: str
    posted_date: Optional[str] = None
