import os
import logging
import base64
import json
from crate import client as crate_client  # pip: crate

logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Management CrateDB cluster needs the following environment variables
CRATEDB_HOST = os.getenv("CRATEDB_HOST")
CRATEDB_USER = os.getenv("CRATEDB_USER")
CRATEDB_PORT = os.getenv("CRATEDB_PORT")
CRATEDB_PASS = os.getenv("CRATEDB_PASS")
CRATEDB_DB = os.getenv("CRATEDB_DB")
SOURCE_TOPIC = os.getenv("SOURCE_TOPIC")

# Globals
_cold_start = True
_crate_http = None
_cratedb_conn = None


def _init_cratedb_connection():
    global _crate_http, _cratedb_conn

    if _cratedb_conn:
        return _cratedb_conn

    try:
        _crate_http = crate_client
        uri = f"https://{CRATEDB_HOST}:{CRATEDB_PORT}"

        conn = crate_client.connect(
            [uri],
            username=CRATEDB_USER,
            password=CRATEDB_PASS,
            schema=CRATEDB_DB,
            verify_ssl_cert=True,
            ca_cert=None,
        )

        # Smoke test
        cur = conn.cursor()
        cur.execute("SELECT 1")
        _ = cur.fetchone()

        _cratedb_conn = conn
        logger.info("Connected to CrateDB via HTTP client at %s", uri)
        return _cratedb_conn

    except Exception as e:
        logger.error("Failed to establish CrateDB HTTP connection: %s", e)
        return None


def _row_from_payload(p):
    """
    Map a payload dict to (timestamp, temperature, u10, v10, pressure, latitude, longitude) tuple.
    Returns (tuple, None) on success, or (None, reason) on failure.
    """
    ts = p.get("timestamp")
    tmp = p.get("temperature")
    u10 = p.get("u10")
    v10 = p.get("v10")
    pressure = p.get("pressure")
    lat = p.get("latitude")
    lon = p.get("longitude")

    try:
        ts = int(ts) / 1000000000  # This is because the received data is in ns, not ms
        tmp = float(tmp) - 273.15 # Adjust from Kelvin to C
        u10 = float(u10)
        v10 = float(v10)
        pressure = float(pressure)
        lat = float(lat)
        lon = float(lon)
    except (TypeError, ValueError):
        return None, "Non-numeric timestamp/temp/lat/lon/u10/v10/pressure"

    return (ts, lon, lat, lon, lat, tmp, u10, v10, pressure), None


def _cratedb_insert(payloads):
    """
    Insert an array of payload dicts into demo.temperature.
    Uses bulk executemany with the CrateDB HTTP client.
    """
    conn = _init_cratedb_connection()
    if not conn:
        return {"ok": False, "error": "No CrateDB connection."}

    rows, errors = [], []
    for i, p in enumerate(payloads or []):
        row, err = _row_from_payload(p)
        if row is not None:
            rows.append(row)
        else:
            errors.append({"index": i, "payload": p, "error": err})

    if not rows:
        return {
            "ok": False,
            "inserted": 0,
            "skipped": len(errors),
            "errors": errors or ["No valid rows"],
        }

    try:
        cur = conn.cursor()
        # Quote the column name "timestamp" to avoid conflicts with reserved words
        result = cur.executemany(
            'INSERT INTO demo.climate_data(timestamp, geo_location, data) VALUES (?, [?, ?], {"longitude" = ?, "latitude" = ?, "temperature" = ?, "u10" = ?, "v10" = ?, "pressure" = ?});',
            rows,
        )

        # Suggestion from Niklas, to also add return value for rows inserted
        actual_inserted = 0
        for i in result:
            actual_inserted += int(i["rowcount"])

        return {
            "ok": True,
            "inserted": len(rows),
            "actual_inserted": actual_inserted,
            "all_inserted": len(rows) == actual_inserted,
            "skipped": len(errors),
            "errors": errors,  # keep for visibility
        }
    except Exception as e:
        logger.error("CrateDB bulk insert failed: %s", e)
        return {
            "ok": False,
            "error": str(e),
            "inserted": 0,
            "skipped": len(errors),
            "errors": errors,
        }


def lambda_handler(event, context):
    global _cold_start

    # Decompose the 'event' JSON parameter, there are other elements that are ignored here
    records = event["records"][str(SOURCE_TOPIC)]
    payloads = []
    for m in records:
        if "value" not in m:
            continue
        txt = base64.b64decode(m["value"]).decode("utf-8", errors="replace")
        try:
            payloads.append(json.loads(txt))
        except json.JSONDecodeError:
            payloads.append(txt)
    logger.debug(payloads)

    # On cold start, test connections
    if _cold_start:
        logger.info("Cold start: initialising stubs.")
        _init_cratedb_connection()
        _cold_start = False

    cratedb_result = _cratedb_insert(payloads)

    body = {
        "message": "Hello from CrateDB!",
        "cratedb_write": cratedb_result,
    }

    return {
        "statusCode": 200,
        "body": json.dumps(body),
    }
