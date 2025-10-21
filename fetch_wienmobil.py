#!/usr/bin/env python3
import json
from datetime import datetime, timezone
from pathlib import Path

import requests

STATUS_URL = "https://api.wstw.at/gateway/WL_WIENMOBIL_API/1/station_status.json"
INFO_URL   = "https://api.wstw.at/gateway/WL_WIENMOBIL_API/1/station_information.json"

OUT_DIR = Path("data")
OUT_FILE = OUT_DIR / "history.jsonl"  # single file, append-only (newline-delimited JSON)

def get_json(url, timeout=30):
    r = requests.get(url, timeout=timeout)
    r.raise_for_status()
    return r.json()

def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    ts = datetime.now(timezone.utc).isoformat(timespec="seconds")

    # 1) Fetch status + station info
    status_json = get_json(STATUS_URL)
    info_json   = get_json(INFO_URL)

    # Expect structures like:
    # status_json: {"data": {"stations": [ { "station_id": "...", "is_renting": 1, "num_bikes_available": 5, ... }, ... ]}}
    # info_json:   {"data": {"stations": [ { "station_id": "...", "name": "...", "lat": 48.2, "lon": 16.37, ... }, ... ]}}

    status_by_id = {s["station_id"]: s for s in status_json.get("data", {}).get("stations", [])}
    info_by_id   = {s["station_id"]: s for s in info_json.get("data", {}).get("stations", [])}

    # 2) Join by station_id and flatten to one record per station
    joined_records = []
    for station_id, status in status_by_id.items():
        info = info_by_id.get(station_id, {})
        rec = {
            "timestamp": ts,
            "station_id": station_id,
            "name": info.get("name"),
            "lat": info.get("lat"),
            "lon": info.get("lon"),
            "num_bikes_available": status.get("num_bikes_available"),
            "num_docks_available": status.get("num_docks_available"),
        }
        joined_records.append(rec)

    if not joined_records:
        print("No stations found; nothing to append.")
        return

    # 3) Append to one single file (newline-delimited JSON to keep file always valid)
    with open(OUT_FILE, "a", encoding="utf-8") as f:
        for rec in joined_records:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")

    print(f"Appended {len(joined_records)} station records at {ts} to {OUT_FILE}")

if __name__ == "__main__":
    try:
        main()
    except requests.exceptions.RequestException as e:
        print(f"Network/API error: {e}")
    except Exception as e:
        print(f"Unexpected error: {e}")
