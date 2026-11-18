"""Fetch every quota order from TARIC and save data/latest.json (run by GitHub Actions).

Orders that fail keep their previous value, so one bad fetch never blanks the site.
If TARIC is down for the whole run, the previous file is kept and the run only fails once data is stale.
Run locally:  py scripts/fetch_taric.py
"""

import json
import os
import re
import time
from datetime import date, datetime, timezone

import taric

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CATALOG = os.path.join(ROOT, "catalog.js")
OUT_FILE = os.path.join(ROOT, "data", "latest.json")
RETRIES = 3                  # attempts when every request fails
RETRY_WAIT = 180             # seconds between attempts
STALE_HOURS = 30             # only fail the run (GitHub e-mails the owner) when data is older than this


def main():
    with open(CATALOG, encoding="utf-8") as f:
        orders = re.findall(r'\["(09\.\d{4})",', f.read())
    start = taric.quarter_start(date.today())

    old = {}
    if os.path.exists(OUT_FILE):
        with open(OUT_FILE, encoding="utf-8") as f:
            old = json.load(f)
    items = old.get("items", {}) if old.get("start") == start else {}

    # TARIC is sometimes briefly unreachable (e.g. early-morning maintenance): retry before giving up
    for attempt in range(1, RETRIES + 1):
        result = taric.fetch_many(orders, start, force=True)
        if result["success"]:
            break
        print(f"Attempt {attempt}: all {len(orders)} requests failed - e.g. {result['items'][0]['error']}")
        if attempt < RETRIES:
            time.sleep(RETRY_WAIT)
    else:
        # keep the previous file untouched; only fail the run (→ e-mail) if data is getting stale
        last = old.get("updatedAt")
        age_h = (datetime.now(timezone.utc) - datetime.fromisoformat(last)).total_seconds() / 3600 if last else 1e9
        if age_h > STALE_HOURS:
            raise SystemExit(f"All TARIC requests failed and data is {age_h:.0f} h old")
        print(f"::warning::TARIC unreachable this run; keeping data from {last} ({age_h:.0f} h old)")
        return

    for it in result["items"]:
        if not it["error"]:
            items[it["orderNo"]] = it

    os.makedirs(os.path.dirname(OUT_FILE), exist_ok=True)
    with open(OUT_FILE, "w", encoding="utf-8") as f:
        json.dump({"start": start, "updatedAt": result["completedAt"],
                   "success": result["success"], "failed": result["failed"],
                   "items": items}, f, ensure_ascii=False)
    print(f"{result['success']} ok, {result['failed']} failed, {result['seconds']} s")


if __name__ == "__main__":
    main()
