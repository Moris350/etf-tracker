"""
Fetches 5-year EOD capital registered for trading history from TASE API
for the given security IDs and writes to their respective CSV files.

Securities:
  1150184 -> ta35_history.csv
  1150259 -> ta90_history.csv
  1150283 -> ta125_history.csv
  1165653 -> construction_history.csv
"""

import requests
import csv
import os
import datetime
import time

DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")

SECURITIES = {
    "1150184": "ta35_history.csv",
    "1150259": "ta90_history.csv",
    "1150283": "ta125_history.csv",
    "1165653": "construction_history.csv",
}

# pType=7 = Capital Registered for Trading (הון רשום למסחר)
API_URL = "https://api.tase.co.il/api/security/{sec_id}/historicaleod"

HEADERS = {
    "Accept": "application/json",
    "Accept-Language": "he",
    "Referer": "https://market.tase.co.il/",
    "Origin": "https://market.tase.co.il",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
}


def fetch_history(sec_id: str) -> list[dict]:
    """Fetch 5-year EOD history for a security from TASE API."""
    today = datetime.date.today()
    five_years_ago = today - datetime.timedelta(days=5 * 366)

    params = {
        "pType": 7,          # Capital Registered for Trading
        "oId": f"0{sec_id}", # Original ID with leading zero (TASE format)
        "fromDate": five_years_ago.strftime("%Y-%m-%d"),
        "toDate": today.strftime("%Y-%m-%d"),
    }

    url = API_URL.format(sec_id=sec_id)
    print(f"  Fetching: {url}")
    print(f"  Params: {params}")

    resp = requests.get(url, params=params, headers=HEADERS, timeout=30)
    resp.raise_for_status()
    data = resp.json()
    return data


def parse_records(data) -> list[tuple[str, str]]:
    """
    Parse the TASE JSON response and return sorted list of (date, value) tuples.
    The JSON structure is typically: list of dicts with 'tradeDate' and 'capitalListedForTrading'.
    """
    records = []

    if isinstance(data, list):
        items = data
    elif isinstance(data, dict):
        # Try common keys
        for key in ("historicalData", "data", "items", "results", "EODData", "eodData"):
            if key in data:
                items = data[key]
                break
        else:
            print(f"  Unknown JSON structure, keys: {list(data.keys())}")
            print(f"  Sample: {str(data)[:500]}")
            return records
    else:
        print(f"  Unexpected data type: {type(data)}")
        return records

    for item in items:
        if not isinstance(item, dict):
            continue

        # Find date field
        date_val = None
        for key in ("tradeDate", "date", "Date", "TradeDate", "dateStr"):
            if key in item:
                date_val = item[key]
                break

        # Find value field (pType=7 = capital registered)
        value_val = None
        for key in ("capitalListedForTrading", "capital", "value", "Value", "unitQuantity",
                    "quantity", "registeredCapital", "capitalForTrading", "listedCapital",
                    "sharesRegistered", "sharesRegisteredForTrading"):
            if key in item:
                value_val = item[key]
                break

        if date_val and value_val is not None:
            # Normalize date to YYYY-MM-DD
            if isinstance(date_val, str) and "T" in date_val:
                date_val = date_val.split("T")[0]
            records.append((str(date_val), str(value_val)))

    # Sort by date ascending
    records.sort(key=lambda x: x[0])
    return records


def write_csv(filepath: str, records: list[tuple[str, str]]):
    """Write records to CSV, preserving existing data and merging new data."""
    existing = {}

    # Read existing data if file exists
    if os.path.exists(filepath):
        with open(filepath, "r", encoding="utf-8-sig") as f:
            reader = csv.reader(f)
            next(reader, None)  # skip header
            for row in reader:
                if len(row) >= 2:
                    existing[row[0]] = row[1]

    # Merge new records
    for date, value in records:
        existing[date] = value

    # Sort and write
    sorted_items = sorted(existing.items())
    with open(filepath, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["Date", "Units"])
        for date, value in sorted_items:
            writer.writerow([date, value])

    print(f"  Written {len(sorted_items)} rows to {os.path.basename(filepath)}")


def dump_sample(sec_id, data):
    """Dump JSON sample to help debugging."""
    import json
    sample_path = os.path.join(DATA_DIR, f"_sample_{sec_id}.json")
    with open(sample_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"  Saved sample JSON to {sample_path}")


def main():
    os.makedirs(DATA_DIR, exist_ok=True)

    for sec_id, csv_filename in SECURITIES.items():
        csv_path = os.path.join(DATA_DIR, csv_filename)
        print(f"\n{'='*60}")
        print(f"Security: {sec_id} -> {csv_filename}")

        try:
            data = fetch_history(sec_id)
            dump_sample(sec_id, data)

            records = parse_records(data)
            print(f"  Parsed {len(records)} records")

            if records:
                write_csv(csv_path, records)
            else:
                print(f"  WARNING: No records parsed! Check sample JSON.")

        except requests.HTTPError as e:
            print(f"  HTTP Error: {e} (status={e.response.status_code})")
            if e.response is not None:
                print(f"  Response body: {e.response.text[:500]}")
        except Exception as e:
            print(f"  Error: {e}")
            import traceback
            traceback.print_exc()

        time.sleep(1.5)  # Be polite to the API

    print(f"\n{'='*60}")
    print("Done!")


if __name__ == "__main__":
    main()
