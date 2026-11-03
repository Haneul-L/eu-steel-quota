import json
from datetime import date

import azure.functions as func

from ..shared_code import taric


def main(req: func.HttpRequest) -> func.HttpResponse:
    today = date.today()
    body = {"ok": True, "today": today.isoformat(), "start": taric.quarter_start(today)}
    return func.HttpResponse(json.dumps(body), mimetype="application/json",
                             headers={"Cache-Control": "no-store"})
