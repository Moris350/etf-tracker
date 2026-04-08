"""
Parse downloaded TASE securityHistoryEOD CSV files and extract
Date + Capital Registered for Trading (הון רשום למסחר) into our app CSVs.

Mapping:
  securityHistoryEOD.csv     -> construction_history.csv  (ת"א בנייה)
  securityHistoryEOD (1).csv -> ta90_history.csv          (ת"א 90)
  securityHistoryEOD (2).csv -> ta125_history.csv         (ת"א 125)
  securityHistoryEOD (3).csv -> ta35_history.csv          (ת"א 35)
"""

import csv
import os
from datetime import datetime

DOWNLOADS = r"C:\Users\segev\Downloads"
DATA_DIR = r"c:\Projects\track_etf\data"

FILE_MAP = {
    "securityHistoryEOD.csv":     "construction_history.csv",
    "securityHistoryEOD (1).csv": "ta90_history.csv",
    "securityHistoryEOD (2).csv": "ta125_history.csv",
    "securityHistoryEOD (3).csv": "ta35_history.csv",
}

# Column index for "הון רשום למסחר" (Capital Registered for Trading)
CAPITAL_COL = 9
DATE_COL = 0


def parse_file(src_path: str) -> list[tuple[str, int]]:
    """Parse a TASE EOD CSV and return list of (YYYY-MM-DD, units)."""
    records = []

    # Try multiple encodings
    content = None
    for enc in ("utf-8-sig", "utf-16", "windows-1255", "iso-8859-8", "latin-1"):
        try:
            with open(src_path, "r", encoding=enc) as f:
                content = f.read()
            break
        except (UnicodeDecodeError, UnicodeError):
            continue

    if content is None:
        print(f"  ERROR: Could not decode {src_path}")
        return records

    lines = content.strip().split("\n")
    # Skip header rows (first 3 lines are title, date range, column headers)
    data_lines = lines[3:]

    for line in data_lines:
        line = line.strip()
        if not line:
            continue

        parts = line.split(",")
        if len(parts) <= CAPITAL_COL:
            continue

        date_str = parts[DATE_COL].strip()
        capital_str = parts[CAPITAL_COL].strip()

        # Skip if not a valid data row
        if not date_str or not capital_str:
            continue

        # Parse date from DD/MM/YYYY to YYYY-MM-DD
        try:
            dt = datetime.strptime(date_str, "%d/%m/%Y")
            iso_date = dt.strftime("%Y-%m-%d")
        except ValueError:
            continue

        # Parse capital value (remove decimals, commas)
        try:
            capital = int(float(capital_str.replace(",", "")))
        except ValueError:
            continue

        if capital > 0:
            records.append((iso_date, capital))

    # Sort ascending by date
    records.sort(key=lambda x: x[0])
    return records


def write_csv(filepath: str, records: list[tuple[str, int]]):
    """Write Date,Units CSV."""
    with open(filepath, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["Date", "Units"])
        for date, units in records:
            writer.writerow([date, units])
    print(f"  -> Written {len(records)} rows to {os.path.basename(filepath)}")


def main():
    os.makedirs(DATA_DIR, exist_ok=True)

    for src_name, dst_name in FILE_MAP.items():
        src_path = os.path.join(DOWNLOADS, src_name)
        dst_path = os.path.join(DATA_DIR, dst_name)

        print(f"\n{'='*60}")
        print(f"Source: {src_name}")
        print(f"Target: {dst_name}")

        if not os.path.exists(src_path):
            print(f"  FILE NOT FOUND: {src_path}")
            continue

        records = parse_file(src_path)
        print(f"  Parsed {len(records)} records")

        if records:
            print(f"  Date range: {records[0][0]} .. {records[-1][0]}")
            print(f"  First value: {records[0][1]:,}")
            print(f"  Last value:  {records[-1][1]:,}")
            write_csv(dst_path, records)
        else:
            print(f"  WARNING: No records parsed!")

    print(f"\n{'='*60}")
    print("Done!")


if __name__ == "__main__":
    main()
