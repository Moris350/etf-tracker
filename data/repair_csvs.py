"""
One-time repair script: fixes CSVs that had Python dict strings written
into the 'Units' column due to a save_to_csv bug.
Converts: Date,"{'units': X, 'assets': Y}"  -->  Date,X,Y (3-column format)
"""
import csv
import os
import ast
from datetime import datetime

DATA_DIR = os.path.dirname(os.path.abspath(__file__))

# Files that may be corrupted
TARGETS = [
    'banks_ksm.csv', 'banks_harel.csv', 'banks_tachlit.csv',
    'realestate_ksm.csv', 'realestate_mtf.csv', 'tech_mtf.csv',
]

def repair(filepath):
    if not os.path.isfile(filepath):
        print(f"SKIP: {filepath} not found")
        return

    rows_repaired = 0
    rows_clean = 0
    merged = {}

    with open(filepath, 'r', newline='', encoding='utf-8') as f:
        reader = csv.reader(f)
        header = next(reader, None)
        
        for row in reader:
            if not row or not row[0]:
                continue
            date_str = row[0].strip()

            # Case 1: already 3-column clean row
            if len(row) >= 3:
                try:
                    units = float(row[1]) if row[1] else 0.0
                    assets = float(row[2]) if row[2] else 0.0
                    merged[date_str] = {'units': units, 'assets': assets}
                    rows_clean += 1
                    continue
                except ValueError:
                    pass  # fall through to dict-string parsing

            # Case 2: 2-column, value is a plain number
            val_str = row[1].strip() if len(row) >= 2 else ''
            try:
                units = float(val_str)
                merged[date_str] = {'units': units, 'assets': 0.0}
                rows_clean += 1
                continue
            except ValueError:
                pass

            # Case 3: 2-column, value is a stringified dict like "{'units': X, 'assets': Y}"
            try:
                d = ast.literal_eval(val_str)
                if isinstance(d, dict) and 'units' in d:
                    merged[date_str] = {'units': float(d['units']), 'assets': float(d.get('assets', 0))}
                    rows_repaired += 1
                    continue
            except:
                pass

            print(f"  WARNING: could not parse row: {row}")

    if rows_repaired == 0:
        print(f"  OK: {os.path.basename(filepath)} — no corrupted rows found ({rows_clean} clean)")
        return

    # Write repaired file
    sorted_dates = sorted(merged.keys(), key=lambda x: datetime.strptime(x, '%Y-%m-%d'))
    with open(filepath, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['Date', 'Units', 'Assets'])
        for d in sorted_dates:
            units = merged[d]['units']
            u_str = f"{int(units)}" if units == int(units) else f"{units}"
            assets = merged[d]['assets']
            a_str = f"{assets:.2f}" if assets > 0 else ""
            writer.writerow([d, u_str, a_str])

    print(f"  REPAIRED: {os.path.basename(filepath)} — {rows_repaired} corrupted rows fixed, {rows_clean} were clean. Total: {len(sorted_dates)}")

if __name__ == '__main__':
    print("=== CSV Repair Tool ===")
    for fname in TARGETS:
        fpath = os.path.join(DATA_DIR, fname)
        print(f"Processing {fname}...")
        repair(fpath)
    print("=== Done ===")
