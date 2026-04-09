import os
import sys
import csv
import re
import math
from datetime import datetime
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright

HAREL_ID = "1233170"
IBI_ID = "5141189"

from app import SECTOR_CONFIG

def check_logical_value(val, fund_type):
    """
    Validates if the extracted number fits the expected logical range for the fund.
    """
    if fund_type == 'harel':
        # Target: ~5.3 million
        if 1000000 < val < 50000000:
            return val
    elif fund_type == 'units':
        # Abstract tracking funds can have significantly different unit metrics
        if val > 0:
            return val
    elif fund_type == 'ibi':
        # Avoid common percentage figures
        if val in [0.0, 10.0, 20.0, 30.0, 40.0, 50.0, 60.0, 70.0, 80.0, 90.0, 100.0]:
            return None
            
        # Target: between 50 and 5000 (millions) OR > 100000 (shown in thousands)
        if 50 < val < 5000:
            return val
        elif val > 100000:
            return val / 1000
    return None

def extract_historical_table(html, fund_type):
    soup = BeautifulSoup(html, 'html.parser')
    results = {}
    
    tables = soup.find_all('table')
    for table in tables:
        headers = [th.get_text(strip=True) for th in table.find_all('th')]
        if "תאריך" in headers and "הון רשום למסחר" in headers:
            date_idx = headers.index("תאריך")
            units_idx = headers.index("הון רשום למסחר")
            
            rows = table.find_all('tr')
            for row in rows:
                cols = row.find_all('td')
                if len(cols) > max(date_idx, units_idx):
                    date_str = cols[date_idx].get_text(strip=True)
                    units_str = cols[units_idx].get_text(strip=True)
                    
                    try:
                        parts = date_str.split('/')
                        if len(parts) == 3:
                            d, m, y = parts
                            if len(y) == 2:
                                y = "20" + y
                            iso_date = f"{y}-{m.zfill(2)}-{d.zfill(2)}"
                            
                            val = float(units_str.replace(',', ''))
                            valid_val = check_logical_value(val, fund_type)
                            if valid_val is not None:
                                results[iso_date] = valid_val
                    except:
                        continue
            if results:
                return results
    return None

def extract_from_html(html, fund_type):
    """
    Extracts purely based on regular expression scraping or intelligent DOM scraping.
    """
    soup = BeautifulSoup(html, 'html.parser')
    
    if fund_type == 'ibi':
        keywords = ["היקף נכסים", "שווי נכסים", "שווי שוק"]
    elif fund_type in ['units', 'harel']:
        keywords = ["הון רשום למסחר"]
    else:
        keywords = []

    for kw in keywords:
        elements = soup.find_all(string=re.compile(kw))
        for element in elements:
            parent = element.parent
            for _ in range(5):
                if parent is None: break
                text = parent.get_text(separator=' ')
                numbers = re.findall(r'(?<![\d.])(\d{1,3}(?:,\d{3})*(?:\.\d+)?)(?![\d.])', text)
                for num_str in numbers:
                    try:
                        val = float(num_str.replace(',', ''))
                        valid_val = check_logical_value(val, fund_type)
                        if valid_val is not None:
                            return valid_val
                    except ValueError:
                        continue
                parent = parent.parent
    return None

def fetch_data(fund_id, fund_type):
    today_str = datetime.now().strftime('%Y-%m-%d')
    combined_results = {}

    if fund_type in ['harel', 'units']:
        urls = [
            f"https://market.tase.co.il/he/market_data/security/{fund_id}/historical_data/eod",
            f"https://market.tase.co.il/he/market_data/security/{fund_id}/major_data"
        ]
    else:
        urls = [
            f"https://www.bizportal.co.il/mutualfunds/quote/generalview/{fund_id}",
            f"https://market.tase.co.il/he/market_data/fund/{fund_id}/major_data"
        ]

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
            )
            page = context.new_page()

            for url in urls:
                try:
                    print(f"[{fund_id}] Trying {url}...")
                    
                    page.goto(url, wait_until="domcontentloaded", timeout=25000)
                    page.wait_for_timeout(3000)
                    
                    html = page.content()
                    
                    if "Just a moment" in html or "Cloudflare" in html:
                        print(f"[{fund_id}] Blocked by Cloudflare on this site.")
                        continue

                    if fund_type in ['harel', 'units']:
                        if "historical_data" in url:
                            val = extract_historical_table(html, fund_type)
                            if val:
                                combined_results.update(val)
                                print(f"[{fund_id}] SUCCESS! Extracted {len(val)} history records.")
                        else:
                            val = extract_from_html(html, fund_type)
                            if val:
                                combined_results[today_str] = val
                                print(f"[{fund_id}] SUCCESS! Extracted LIVE today value: {val}")
                    else:
                        val = extract_from_html(html, fund_type)
                        if val:
                            combined_results[today_str] = val
                            print(f"[{fund_id}] SUCCESS! Extracted LIVE today value: {val}")
                            browser.close()
                            return combined_results

                except Exception as e:
                    print(f"[{fund_id}] Error connecting to {url}: {e}")

            browser.close()
            
            if combined_results:
                return combined_results
            
    except Exception as e:
        print(f"[{fund_id}] Playwright error: {e}")

    print(f"[{fund_id}] FAILED completely on all sources.")
    return None

def save_to_csv(filepath, data_dict, col_name):
    merged_data = {}
    
    # Read existing
    if os.path.isfile(filepath):
        with open(filepath, mode='r', newline='', encoding='utf-8') as file:
            reader = csv.reader(file)
            headers = next(reader, None) # Skip header
            for row in reader:
                if len(row) == 2:
                    merged_data[row[0]] = row[1]
                    
    # Update with new data (Upsert implicitly updates values or appends missing ones)
    for date_key, val in data_dict.items():
        merged_data[date_key] = val
        
    # Sort chronologically by date keys (YYYY-MM-DD naturally sorts alphabetically)
    sorted_dates = sorted(merged_data.keys())
    
    # Write back
    rows = [['Date', col_name]]
    for date_key in sorted_dates:
        rows.append([date_key, merged_data[date_key]])
        
    with open(filepath, mode='w', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        writer.writerows(rows)
        
    print(f"[{col_name}] Synced CSV with {len(data_dict)} records. Total archive size: {len(sorted_dates)}")

def main():
    if len(sys.argv) < 2:
        print("FAILED: Missing argument. Expected sector code.")
        return
        
    fund_target = sys.argv[1].lower()
    today_str = datetime.now().strftime('%Y-%m-%d')
    
    if fund_target not in SECTOR_CONFIG:
        print(f"FAILED: Unknown fund target '{fund_target}'")
        return
        
    base_dir = os.path.dirname(os.path.abspath(__file__))
    data_dir = os.path.join(base_dir, "data")
    os.makedirs(data_dir, exist_ok=True)
    
    cfg = SECTOR_CONFIG[fund_target]
    for fund in cfg['funds']:
        fund_id = fund['tase_id']
        csv_file = fund['csv_file']
        
        if not fund_id:
            continue
            
        logic_type = 'units'
        if fund_target == 'harel':
            logic_type = 'harel'
        elif fund_target == 'ibi':
            logic_type = 'ibi'
            
        print(f"--- Fetching {fund['name']} [{fund_id}] ---")
        val = fetch_data(fund_id, logic_type)
        
        if val is not None:
            if logic_type in ['harel', 'units']:
                save_to_csv(os.path.join(data_dir, csv_file), val, "Units")
            else:
                save_to_csv(os.path.join(data_dir, csv_file), {today_str: round(val, 2)}, "Assets")
        else:
            print(f"FAILED to update {fund['name']}.")

if __name__ == "__main__":
    main()