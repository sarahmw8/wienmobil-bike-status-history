#!/usr/bin/env python3
import json
from datetime import datetime, timezone
from pathlib import Path

import requests # download data from the WienMobil API.

STATUS_URL = "https://api.wstw.at/gateway/WL_WIENMOBIL_API/1/station_status.json"    #current bike availability at each station (live data).
INFO_URL   = "https://api.wstw.at/gateway/WL_WIENMOBIL_API/1/station_information.json" # static info like name, coordinates, and address.

OUT_DIR = Path("data")  # defines a folder called data
OUT_FILE = OUT_DIR / "history.jsonl"  # combines the folder with the filename history.jsonl (newline-delimited JSON)

def get_json(url, timeout=30): # Sends a GET request to the given url.
    r = requests.get(url, timeout=timeout)
    r.raise_for_status() #If the server responds with an error (like 404 or 500), r.raise_for_status() raises an exception instead of silently failing. Returns the parsed JSON content (r.json() turns it into a Python dict or list).
    return r.json() # Returns the JSON content (r.json() turns it into a Python dict or list).


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True) # Creates the data/ directory if it doesn’t already exist. parents=True - also create parent directories if needed; exist_ok=True → no error if it already exists.
    ts = datetime.now(timezone.utc).isoformat(timespec="seconds") # Gets the current time (in UTC and Converts it to a format like

    # Fetch status + station info - Calls the helper function twice to download both JSON datasets.
    status_json = get_json(STATUS_URL)
    info_json   = get_json(INFO_URL)


    status_by_id = {s["station_id"]: s for s in status_json.get("data", {}).get("stations", [])} # This line reorganizes the list of stations into a dictionary, so that each station can be quickly found using its station_id
    info_by_id   = {s["station_id"]: s for s in info_json.get("data", {}).get("stations", [])}

    # Join by station_id and flatten to one record per station
    joined_records = [] # Create an empty list
    for station_id, status in status_by_id.items(): # Loop over each station in the live status data.
        info = info_by_id.get(station_id, {}) # Look up the corresponding info record
        # Combine both into one flat dictionary
        rec = {
            "timestamp": ts,
            "station_id": station_id,
            "name": info.get("name"),
            "lat": info.get("lat"),
            "lon": info.get("lon"),
            "num_bikes_available": status.get("num_bikes_available"),
            "num_docks_available": status.get("num_docks_available"),
        }
        joined_records.append(rec) # Append this combined record to the list

    if not joined_records: # If for some reason the API is empty or broken, this avoids writing an empty file.
        print("No stations found; nothing to append.")
        return

    # This part is what saves the collected data permanently. Each time the script is being run: It takes all stations from the API, Converts them to text,
    with open(OUT_FILE, "a", encoding="utf-8") as f:
        for rec in joined_records:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")

    print(f"Appended {len(joined_records)} station records at {ts} to {OUT_FILE}")

if __name__ == "__main__":
    try: # Runs main() inside a try block.
        main()
    except requests.exceptions.RequestException as e:   #If a network or HTTP error happens (like timeout, 404, etc.), it catches it and prints a friendly message.
        print(f"Network/API error: {e}")
    except Exception as e:
        print(f"Unexpected error: {e}")
