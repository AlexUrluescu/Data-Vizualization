"""
configs/routes/v1/data_ingest.py

POST /api/v1/data   — receives sensor readings and writes them to sensor_data.

Expected JSON body (single reading):
{
    "device_id":   "1600013B",
    "location":    "Centru",
    "timestamp":   "2025-04-03T14:30:00",   ← ISO-8601, optional (defaults to now)
    "temperature": 21.4,
    "pressure":    1012.3,
    "humidity":    58.2,
    "pm1":         4.1,
    "pm25":        8.7,
    "pm10":        12.0
}

Or a batch (array of the above):
[
    { "device_id": "1600013B", "location": "Centru", ... },
    { "device_id": "1600019F", "location": "Terezian", ... }
]

Authentication:
    All requests must include the correct API headers:
        X-User-id:   <user_id stored in api_keys>
        X-User-hash: <user_hash stored in api_keys>
    
    The endpoint validates these against the api_keys table.
"""

from flask import Blueprint, request, jsonify
import pandas as pd
from datetime import datetime, timezone
from db import save_to_db, list_api_keys

data_ingest_bp = Blueprint("data_ingest", __name__)

REQUIRED_FIELDS = {"device_id", "location"}
NUMERIC_FIELDS  = ("temperature", "pressure", "humidity", "pm1", "pm25", "pm10")


def _authenticate(req) -> tuple[bool, str]:
    """
    Validates X-User-id / X-User-hash headers against active api_keys rows.
    Returns (ok: bool, error_message: str).
    """
    uid   = req.headers.get("X-User-id",   "").strip()
    uhash = req.headers.get("X-User-hash", "").strip()

    if not uid or not uhash:
        return False, "Missing X-User-id or X-User-hash header."

    active_keys = [k for k in list_api_keys() if k.get("is_active")]
    matched = any(
        k["user_id"] == uid and k["user_hash"] == uhash
        for k in active_keys
    )
    if not matched:
        return False, "Invalid or inactive API credentials."

    return True, ""


def _parse_record(raw: dict) -> tuple[dict | None, str]:
    missing = REQUIRED_FIELDS - raw.keys()
    if missing:
        return None, f"Missing required fields: {', '.join(sorted(missing))}"

    record = {
        "device_id": str(raw["device_id"]).strip(),
        "location":  str(raw["location"]).strip(),
    }

    ts_raw = raw.get("timestamp")
    if ts_raw:
        try:
            ts = datetime.fromisoformat(str(ts_raw).replace("Z", "+00:00"))
        except ValueError:
            return None, f"Invalid timestamp format: '{ts_raw}'. Use ISO-8601."
    else:
        ts = datetime.now(timezone.utc)

    record["timestamp"] = ts.replace(tzinfo=None)

    for field in NUMERIC_FIELDS:
        val = raw.get(field)
        if val is None:
            record[field] = None
        else:
            try:
                record[field] = float(val)
            except (TypeError, ValueError):
                return None, f"Field '{field}' must be a number, got: {val!r}"

    return record, ""



@data_ingest_bp.route("/data", methods=["POST"])
def ingest_data():

    ok, err = _authenticate(request)
    if not ok:
        return jsonify({"ok": False, "error": err}), 401

    if not request.is_json:
        return jsonify({"ok": False, "error": "Content-Type must be application/json"}), 400

    body = request.get_json(silent=True)
    if body is None:
        return jsonify({"ok": False, "error": "Empty or invalid JSON body."}), 400

    raw_list = body if isinstance(body, list) else [body]
    if not raw_list:
        return jsonify({"ok": False, "error": "Empty data array."}), 400

   
    records, errors = [], []
    for i, raw in enumerate(raw_list):
        record, err = _parse_record(raw)
        if err:
            errors.append({"index": i, "error": err})
        else:
            records.append(record)

  
    if errors:
        return jsonify({
            "ok":     False,
            "error":  "Validation failed for one or more records.",
            "detail": errors,
        }), 422

    df_all = pd.DataFrame(records)
    df_all["timestamp"] = pd.to_datetime(df_all["timestamp"])

    inserted = 0
    for (device_id, location), group in df_all.groupby(["device_id", "location"]):
        save_to_db(group.reset_index(drop=True), device_id=device_id, location=location)
        inserted += len(group)

    return jsonify({
        "ok":       True,
        "inserted": inserted,
        "skipped":  len(raw_list) - inserted,
    }), 201



@data_ingest_bp.route("/data/health", methods=["GET"])
def health():
    """Quick liveness check — no auth required."""
    return jsonify({"ok": True, "timestamp": datetime.utcnow().isoformat()}), 200