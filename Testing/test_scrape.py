import json
from curl_cffi import requests

def test_url(url, keywords=[]):
    print(f"Testing {url}")
    try:
        response = requests.get(url, impersonate="chrome110", timeout=15)
        print(f"Status Code: {response.status_code}")
        
        text = response.text
        if "Just a moment" in text or "Cloudflare" in text:
            print("Blocked by Cloudflare!")
            return
            
        print("Success! Response size:", len(text))
        
        # Look for keywords or numbers
        import re
        numbers = re.findall(r'(?<![\d.])(\d{1,3}(?:,\d{3})*(?:\.\d+)?)(?![\d.])', text)
        for num_str in set(numbers):
            try:
                val = float(num_str.replace(',', ''))
                if 1000000 < val < 50000000:  # Harel logic
                    print(f"Found potential Harel value: {val} (Original: {num_str})")
                elif 50 < val < 5000 and val not in [90.0, 100.0, 0.0, 10.0, 20.0, 30.0, 40.0, 50.0, 60.0, 70.0, 80.0]: # IBI logic
                    print(f"Found potential IBI value: {val} (Original: {num_str})")
            except ValueError:
                pass
                
    except Exception as e:
        print(f"Error: {e}")

print("--- HAREL ---")
test_url("https://www.funder.co.il/fund/1233170")
test_url("https://www.globes.co.il/portal/instrument.aspx?instrumentid=620912")
test_url("https://market.tase.co.il/he/market_data/security/1233170/major_data")
