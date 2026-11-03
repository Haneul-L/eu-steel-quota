import json
from datetime import date

import azure.functions as func

from ..shared_code import taric

MAX_ORDERS = 40              # per request; the page sends 30 at a time (keeps each call well under the 45 s limit)


def main(req: func.HttpRequest) -> func.HttpResponse:
    orders = [o for o in req.params.get("orders", "").split(",") if taric.ORDER_RE.match(o)][:MAX_ORDERS]
    start = req.params.get("start", "")
    if not taric.DATE_RE.match(start):
        start = taric.quarter_start(date.today())
    force = req.params.get("force") == "1"
    if not orders:
        return func.HttpResponse(json.dumps({"error": "orders parameter is required"}),
                                 status_code=400, mimetype="application/json")

    body = taric.fetch_many(orders, start, force)
    return func.HttpResponse(json.dumps(body, ensure_ascii=False), mimetype="application/json",
                             headers={"Cache-Control": "no-store"})
