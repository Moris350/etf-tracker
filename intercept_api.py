from playwright.sync_api import sync_playwright
import time
import json
import re

TARGETS = {
    "1233170": {
        "urls": [
            "https://market.tase.co.il/he/market_data/security/1233170/major_data",
            "https://www.globes.co.il/portal/instrument.aspx?instrumentid=620912"
        ],
        "check": lambda v: 1000000 < v < 50000000
    },
    "5141189": {
        "urls": [
            "https://market.tase.co.il/he/market_data/fund/5141189/major_data",
            "https://www.globes.co.il/portal/fund.aspx?instrumentid=596791"
        ],
        "check": lambda v: (50 < v < 5000 and v not in [90.0, 100.0, 0.0, 10.0, 20.0, 30.0, 40.0, 50.0, 60.0, 70.0, 80.0]) or v > 100000
    }
}

def check_number(text, check_func, url, req_url):
    numbers = re.findall(r'(?<![\d.])(\d{1,3}(?:,\d{3})*(?:\.\d+)?)(?![\d.])', text)
    found = False
    for num_str in set(numbers):
        try:
            val = float(num_str.replace(',', ''))
            if check_func(val):
                print(f"[HIT] Found {val} in request: {req_url}")
                found = True
        except: pass
    if found:
        print(f"--- PREVIEW OF {req_url[:100]} ---")
        print(text[:500])
        print("-----------------------------------")

def main():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        for fund_id, data in TARGETS.items():
            print(f"=== Testing {fund_id} ===")
            for url in data["urls"]:
                print(f"  -> Navigating to {url}")
                page = browser.new_page()
                
                # Listen to responses
                def handle_response(response):
                    if response.request.resource_type in ["fetch", "xhr", "document"]:
                        try:
                            text = response.text()
                            check_number(text, data["check"], url, response.url)
                        except Exception as e:
                            pass
                
                page.on("response", handle_response)
                try:
                    page.goto(url, wait_until="networkidle", timeout=15000)
                    time.sleep(2)
                except Exception as e:
                    print(f"Error navigating: {e}")
                
                page.close()
        browser.close()

if __name__ == "__main__":
    main()
