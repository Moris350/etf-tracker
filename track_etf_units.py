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

def check_logical_value(val, fund_type):
    """
    Validates if the extracted number fits the expected logical range for the fund.
    """
    if fund_type == 'harel':
        # Target: ~5.3 million
        if 1000000 < val < 50000000:
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
                        d, m, y = date_str.split('/')
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

    return None

def fetch_data(fund_id, fund_type):
    if fund_type == 'harel':
        urls = [
            f"https://market.tase.co.il/he/market_data/security/{fund_id}/historical_data/eod"
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
                    
                    # Navigate and wait for DOM completely loaded, plus 3 seconds for XHR/React hydrate
                    page.goto(url, wait_until="domcontentloaded", timeout=25000)
                    page.wait_for_timeout(3000)
                    
                    html = page.content()
                    
                    if "Just a moment" in html or "Cloudflare" in html:
                        print(f"[{fund_id}] Blocked by Cloudflare on this site.")
                        continue
                        
                    # DEBUG SNAPSHOT
                    base_dir = os.path.dirname(os.path.abspath(__file__))
                    data_dir = os.path.join(base_dir, "data")
                    os.makedirs(data_dir, exist_ok=True)
                    with open(os.path.join(data_dir, "debug.html"), "w", encoding="utf-8") as f:
                        f.write(html)

                    if fund_type == 'harel':
                        val = extract_historical_table(html, fund_type)
                    else:
                        val = extract_from_html(html, fund_type)
                        
                    if val is not None and (isinstance(val, dict) and len(val) > 0 or not isinstance(val, dict)):
                        success_msg = f"SUCCESS! Found {len(val)} records" if isinstance(val, dict) else f"SUCCESS! Found logical value -> {val}"
                        print(f"[{fund_id}] {success_msg} on {url}")
                        browser.close()
                        return val
                    else:
                        print(f"[{fund_id}] Page loaded, but no logical numbers matched.")

                except Exception as e:
                    print(f"[{fund_id}] Error connecting to {url}: {e}")

            browser.close()
            
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
        print("FAILED: Missing argument. Expected 'harel' or 'ibi'.")
        return
        
    fund_target = sys.argv[1].lower()
    today_str = datetime.now().strftime('%Y-%m-%d')
    fund_id = HAREL_ID if fund_target == 'harel' else IBI_ID
    
    val = fetch_data(fund_id, fund_target)
    
    if val is not None:
        base_dir = os.path.dirname(os.path.abspath(__file__))
        data_dir = os.path.join(base_dir, "data")
        os.makedirs(data_dir, exist_ok=True)
        
        if fund_target == 'harel':
            # val is already a dictionary mapped from TASE
            save_to_csv(os.path.join(data_dir, "harel_history.csv"), val, "Units")
        else:
            # IBI truncated to 2 decimals, dynamically cast into a single-entry dict to fit unified function
            save_to_csv(os.path.join(data_dir, "ibi_history.csv"), {today_str: round(val, 2)}, "Assets")
    else:
        print(f"FAILED to update {fund_target.upper()}.")

if __name__ == "__main__":
    main()