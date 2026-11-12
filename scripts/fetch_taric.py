"""Fetch every quota order from TARIC and save data/latest.json (run by GitHub Actions).

Orders that fail keep their previous value, so one bad fetch never blanks the site.
Run locally:  py scripts/fetch_taric.py
"""

import json
import os
import re
from datetime import date

import taric

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CATALOG = os.path.join(ROOT, "catalog.js")
OUT_FILE = os.path.join(ROOT, "data", "latest.json")


def main():
    with open(CATALOG, encoding="utf-8") as f:
        orders = re.findall(r'\["(09\.\d{4})",', f.read())
    start = taric.quarter_start(date.today())

    old = {}
    if os.path.exists(OUT_FILE):
        with open(OUT_FILE, encoding="utf-8") as f:
            old = json.load(f)
    items = old.get("items", {}) if old.get("start") == start else {}

    result = taric.fetch_many(orders, start, force=True)
    for it in result["items"]:
        if not it["error"]:
            items[it["orderNo"]] = it

    os.makedirs(os.path.dirname(OUT_FILE), exist_ok=True)
    with open(OUT_FILE, "w", encoding="utf-8") as f:
        json.dump({"start": start, "updatedAt": result["completedAt"],
                   "success": result["success"], "failed": result["failed"],
                   "items": items}, f, ensure_ascii=False)
    print(f"{result['success']} ok, {result['failed']} failed, {result['seconds']} s")
    if result["success"] == 0:
        raise SystemExit("All TARIC requests failed")


if __name__ == "__main__":
    main()
