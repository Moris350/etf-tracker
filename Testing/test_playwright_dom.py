from playwright.sync_api import sync_playwright
import re

def main():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        
        # Test Harel on Funder
        print("Testing Harel on Funder...")
        page.goto("https://www.funder.co.il/fund/1233170", wait_until="networkidle")
        html = page.content()
        numbers = set(re.findall(r'(?<![\d.])(\d{1,3}(?:,\d{3})*(?:\.\d+)?)(?![\d.])', html))
        for num_str in numbers:
            try:
                val = float(num_str.replace(',', ''))
                if 1000000 < val < 50000000:
                    print(f"Harel Funder FOUND: {val}")
            except: pass

        # Test Harel on Globes
        print("Testing Harel on Globes...")
        page.goto("https://www.globes.co.il/portal/instrument.aspx?instrumentid=620912", wait_until="networkidle")
        html = page.content()
        numbers = set(re.findall(r'(?<![\d.])(\d{1,3}(?:,\d{3})*(?:\.\d+)?)(?![\d.])', html))
        for num_str in numbers:
            try:
                val = float(num_str.replace(',', ''))
                if 1000000 < val < 50000000:
                    print(f"Harel Globes FOUND: {val}")
            except: pass

        # Test IBI on Globes
        print("Testing IBI on Globes...")
        page.goto("https://www.globes.co.il/portal/fund.aspx?instrumentid=596791", wait_until="networkidle")
        html = page.content()
        numbers = set(re.findall(r'(?<![\d.])(\d{1,3}(?:,\d{3})*(?:\.\d+)?)(?![\d.])', html))
        for num_str in numbers:
            try:
                val = float(num_str.replace(',', ''))
                if (50 < val < 5000 and val not in [90.0, 100.0, 0.0, 10.0, 20.0, 30.0, 40.0, 50.0, 60.0, 70.0, 80.0]) or val > 100000:
                    print(f"IBI Globes FOUND: {val}")
            except: pass

        browser.close()

if __name__ == "__main__":
    main()
