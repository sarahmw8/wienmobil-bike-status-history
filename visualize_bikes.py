#!/usr/bin/env python3
import json
from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt

DATA_FILE = Path("data/history.jsonl")
OUT_DIR = Path("site")
OUT_DIR.mkdir(parents=True, exist_ok=True)
OUT_FILE = OUT_DIR / "chart.png"

def load_data():
    # Read the JSONL file into a pandas DataFrame
    df = pd.read_json(DATA_FILE, lines=True)

    # Keep only relevant columns
    df = df[["timestamp", "station_id", "num_bikes_available"]]

    # Convert timestamp column to datetime
    df["timestamp"] = pd.to_datetime(df["timestamp"])

    # Group by timestamp (sum all available bikes at that time)
    totals = df.groupby("timestamp")["num_bikes_available"].sum().reset_index()

    return totals

def plot_data(df):
    plt.figure(figsize=(10, 5))
    plt.plot(df["timestamp"], df["num_bikes_available"], marker="o", linewidth=1.5)
    plt.title("🚲 Total Available Bikes in Vienna Over Time")
    plt.xlabel("Timestamp (UTC)")
    plt.ylabel("Number of Bikes Available")
    plt.grid(True)
    plt.tight_layout()
    plt.savefig(OUT_FILE, dpi=160)
    plt.close()
    print(f"✅ Chart saved to {OUT_FILE}")

def main():
    if not DATA_FILE.exists():
        print("❌ No data file found. Run fetch_wienmobil.py first.")
        return

    df = load_data()
    if df.empty:
        print("❌ No data to visualize.")
        return

    plot_data(df)

if __name__ == "__main__":
    main()
