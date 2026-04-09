import os
import csv
from datetime import datetime
from track_etf_units import save_to_csv
from app import SECTOR_CONFIG

def main():
    data_dir = '/app/data'
    
    # Build reverse map: tase_id -> csv_file
    tase_to_csv = {}
    for sector, cfg in SECTOR_CONFIG.items():
        if 'funds' in cfg:
            for fund in cfg['funds']:
                if fund['tase_id']:
                    tase_to_csv[fund['tase_id']] = fund['csv_file']
    
    # Find all {tase_id}.csv files in data_dir
    files = [f for f in os.listdir(data_dir) if f.endswith('.csv') and f.split('.')[0].isdigit()]
    
    for file in files:
        tase_id = file.split('.')[0]
        if tase_id not in tase_to_csv:
            print(f"Skipping {file} - not in SECTOR_CONFIG")
            continue
            
        csv_path = os.path.join(data_dir, file)
        target_csv = tase_to_csv[tase_id]
        
        data_dict = {}
        with open(csv_path, 'r', encoding='utf-8') as f:
            reader = csv.reader(f)
            headers = []
            
            # Find the header row
            for row in reader:
                if 'תאריך' in row and 'הון רשום למסחר' in row:
                    headers = row
                    break
            
            if not headers:
                print(f"FAILED: Could not find headers in {file}")
                continue
                
            date_idx = headers.index('תאריך')
            units_idx = headers.index('הון רשום למסחר')
            
            for row in reader:
                # Some rows might be empty or short
                if len(row) <= max(date_idx, units_idx):
                    continue
                    
                date_str = row[date_idx].strip()
                unit_str = row[units_idx].strip().replace(',', '')
                
                if not date_str or not unit_str:
                    continue
                    
                try:
                    # Parse DD/MM/YYYY
                    dt = datetime.strptime(date_str, '%d/%m/%Y')
                    iso_date = dt.strftime('%Y-%m-%d')
                    val = float(unit_str)
                    
                    if val > 0:
                        data_dict[iso_date] = val
                except Exception as e:
                    pass
                    
        if data_dict:
            print(f"Importing {len(data_dict)} records from {file} into {target_csv}")
            save_to_csv(os.path.join(data_dir, target_csv), data_dict, "Units")
        else:
            print(f"No valid records found in {file}")

if __name__ == '__main__':
    main()
