"""
Merge local seen_jobs.json with the version on origin/master.
Called by the workflow before committing to preserve entries from concurrent runs.
"""
import json
import subprocess
import sys


def merge(path: str = "seen_jobs.json") -> None:
    r = subprocess.run(
        ["git", "show", "origin/master:seen_jobs.json"],
        capture_output=True,
        text=True,
    )
    origin = json.loads(r.stdout) if r.returncode == 0 else []

    with open(path, encoding="utf-8") as f:
        local = json.load(f)

    # Union by (source, job_id); local (this run) wins on duplicates
    merged: dict = {(d["source"], d["job_id"]): d for d in origin}
    merged.update({(d["source"], d["job_id"]): d for d in local})
    result = list(merged.values())

    with open(path, "w", encoding="utf-8") as f:
        json.dump(result, f)

    print(
        f"[merge_seen] origin={len(origin)}, local={len(local)}, merged={len(result)}"
    )


if __name__ == "__main__":
    merge(sys.argv[1] if len(sys.argv) > 1 else "seen_jobs.json")
