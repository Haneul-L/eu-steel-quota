"""TARIC quota page fetch + parse (same logic as eng/server.py)."""

import html
import re
import threading
import time
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from datetime import date, datetime, timezone

TARIC_URL = "https://ec.europa.eu/taxation_customs/dds2/taric/quota_tariff_details.jsp"
CACHE_TTL = 10 * 60          # same order is fetched from TARIC at most once per 10 minutes
MAX_WORKERS = 6              # parallel TARIC requests (too many may get blocked)
ORDER_RE = re.compile(r"^09\.\d{4}$")
DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")

_cache = {}                  # key: (orderNo, startDate) -> (fetched_ts, item); lives while the instance is warm
_lock = threading.Lock()


def quarter_start(d: date) -> str:
    return date(d.year, (d.month - 1) // 3 * 3 + 1, 1).isoformat()


def dmy_to_iso(s):
    if not s:
        return None
    d, m, y = s.split("-")
    return f"{y}-{m}-{d}"


def num(s):
    return float(s.replace(",", "")) if s else None


def parse_taric(page: str) -> dict:
    text = re.sub(r"<[^>]+>", " ", page)
    text = html.unescape(text).replace("\xa0", " ")
    text = re.sub(r"\s+", " ", text)

    def find(pattern):
        m = re.search(pattern, text)
        return m.group(1).strip() if m else None

    amount = num(find(r"\bAmount ([\d.,]+) ?Kilogram"))
    balance = num(find(r"\bBalance ([\d.,]+) ?Kilogram"))
    if amount is None or balance is None:
        raise ValueError("Amount/Balance not found on TARIC page (no quota for this period?)")
    awaiting = num(find(r"Total awaiting allocation ?\( ?indicative ?\) ?([\d.,]+)")) or 0.0
    validity = re.search(r"Validity period (\d{2}-\d{2}-\d{4}) ?- ?(\d{2}-\d{2}-\d{4})", text)

    return {
        "quota": amount / 1000,          # kg -> t
        "balance": balance / 1000,
        "awaiting": awaiting / 1000,
        "initialQuota": (num(find(r"Initial amount ([\d.,]+) ?Kilogram")) or amount) / 1000,
        "originLive": find(r"Origin (.+?) Initial amount"),
        "taricUpdated": dmy_to_iso(find(r"Last TARIC update: ?(\d{2}-\d{2}-\d{4})")),
        "periodStart": dmy_to_iso(validity.group(1)) if validity else None,
        "periodEnd": dmy_to_iso(validity.group(2)) if validity else None,
        "allocationDate": dmy_to_iso(find(r"Last allocation date (\d{2}-\d{2}-\d{4})")),
        "lastImportDate": dmy_to_iso(find(r"Last import date (\d{2}-\d{2}-\d{4})")),
        "exhaustionDate": dmy_to_iso(find(r"Exhaustion date (\d{2}-\d{2}-\d{4})")),
        "critical": find(r"Critical (Yes|No)"),
        "closedForDrawing": find(r"Closed for drawing requests (Yes|No)"),
    }


def source_url(order_no: str, start: str) -> str:
    code = order_no.replace(".", "")
    return f"{TARIC_URL}?Code={code}&Lang=en&StartDate={start}"


def now_iso():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def fetch_order(order_no: str, start: str, force: bool) -> dict:
    key = (order_no, start)
    now = time.time()
    with _lock:
        hit = _cache.get(key)
    if hit and not force and now - hit[0] < CACHE_TTL:
        return hit[1]

    url = source_url(order_no, start)
    item = {"orderNo": order_no, "sourceUrl": url, "error": None}
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (EU steel quota monitor)"})
        with urllib.request.urlopen(req, timeout=20) as res:
            page = res.read().decode("utf-8", errors="replace")
        item.update(parse_taric(page))
    except Exception as e:  # one failure does not stop the rest
        item["error"] = str(e)[:200]
    item["fetchedAt"] = now_iso()

    if not item["error"]:
        with _lock:
            _cache[key] = (now, item)
    return item


def fetch_many(orders, start, force):
    started = time.time()
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as ex:
        items = list(ex.map(lambda o: fetch_order(o, start, force), orders))
    return {
        "start": start,
        "requested": len(orders),
        "success": sum(1 for i in items if not i["error"]),
        "failed": sum(1 for i in items if i["error"]),
        "seconds": round(time.time() - started, 1),
        "completedAt": now_iso(),
        "items": items,
    }
