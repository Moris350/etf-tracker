import os
import sys
import csv
import subprocess
from flask import Flask, render_template, jsonify
from datetime import datetime

app = Flask(__name__)

def read_fund_data(filepath, val_col, is_harel=False):
    data_dict = {}
    if os.path.isfile(filepath):
        with open(filepath, mode='r', newline='') as f:
            for row in csv.DictReader(f):
                try:
                    date_obj = datetime.strptime(row['Date'], '%Y-%m-%d')
                    val = float(row[val_col])
                    if is_harel or val_col == "Units": 
                        val /= 1000000  # Scale down generic 'Units' data to millions for symmetric design display
                    data_dict[date_obj] = val
                except: pass
    return data_dict

@app.route('/')
def index():
    return render_template('index.html', active_nav='/', sectors=SECTOR_CONFIG)

SECTOR_CONFIG = {
    'tech': {
        'title': 'ת"א טכנולוגיה',
        'color': '#3b82f6',
        'bg_color': 'rgba(59,130,246,0.1)',
        'unit_title': "מ' יחידות (הון רשום למסחר)",
        'funds': [
            {'name': 'KSM Tech', 'csv_file': 'tech_ksm.csv', 'tase_id': '5130927'},
            {'name': 'MTF Tech', 'csv_file': 'tech_mtf.csv', 'tase_id': '1169408'}
        ]
    },
    'realestate': {
        'title': 'ת"א נדל"ן',
        'color': '#a78bfa',
        'bg_color': 'rgba(167,139,250,0.1)',
        'unit_title': "מ' יחידות (הון רשום למסחר)",
        'funds': [
            {'name': 'KSM Real Estate', 'csv_file': 'realestate_ksm.csv', 'tase_id': '1146547'},
            {'name': 'Tachlit Real Estate', 'csv_file': 'realestate_tachlit.csv', 'tase_id': '1144559'},
            {'name': 'MTF Real Estate', 'csv_file': 'realestate_mtf.csv', 'tase_id': '1183953'}
        ]
    },
    'harel': {
        'title': 'הראל ת"א ביטחוניות',
        'color': '#14b8a6',
        'bg_color': 'rgba(20,184,166,0.1)',
        'unit_title': "מ' יחידות (הון רשום למסחר)",
        'funds': [
            {'name': 'Harel Defense', 'csv_file': 'harel_history.csv', 'tase_id': '1233170'}
        ]
    },
    'ibi': {
        'title': 'IBI נכסים מחקרית',
        'color': '#f59e0b',
        'bg_color': 'rgba(245,158,11,0.1)',
        'unit_title': 'במיליוני ש"ח (שווי נכסים)',
        'funds': [
            {'name': 'IBI Core', 'csv_file': 'ibi_history.csv', 'tase_id': None}
        ]
    },
    'banks': {
        'title': 'ת"א בנקים',
        'color': '#06b6d4',
        'bg_color': 'rgba(6,182,212,0.1)',
        'unit_title': "מ' יחידות (הון רשום למסחר)",
        'funds': [
            {'name': 'KSM Banks', 'csv_file': 'banks_ksm.csv', 'tase_id': '1146430'},
            {'name': 'Harel Banks', 'csv_file': 'banks_harel.csv', 'tase_id': '1148949'},
            {'name': 'Tachlit Banks', 'csv_file': 'banks_tachlit.csv', 'tase_id': '1143726'}
        ]
    },
    'oil': {
        'title': 'ת"א נפט וגז',
        'color': '#f97316',
        'bg_color': 'rgba(249,115,22,0.1)',
        'unit_title': "מ' יחידות (הון רשום למסחר)",
        'funds': [
            {'name': 'Oil ETF', 'csv_file': 'oil_history.csv', 'tase_id': '5140595'}
        ]
    },
    'construction': {
        'title': 'ת"א בנייה',
        'color': '#84cc16',
        'bg_color': 'rgba(132,204,22,0.1)',
        'unit_title': "מ' יחידות (הון רשום למסחר)",
        'funds': [
            {'name': 'Construction ETF', 'csv_file': 'construction_history.csv', 'tase_id': '1165653'}
        ]
    },
    'ta35': {
        'title': 'ת"א 35',
        'color': '#e11d48',
        'bg_color': 'rgba(225,29,72,0.1)',
        'unit_title': "מ' יחידות (הון רשום למסחר)",
        'funds': [
            {'name': 'TA-35 MTF', 'csv_file': 'ta35_history.csv', 'tase_id': '1150184'}
        ]
    },
    'ta90': {
        'title': 'ת"א 90',
        'color': '#8b5cf6',
        'bg_color': 'rgba(139,92,246,0.1)',
        'unit_title': "מ' יחידות (הון רשום למסחר)",
        'funds': [
            {'name': 'TA-90 MTF', 'csv_file': 'ta90_history.csv', 'tase_id': '1150259'}
        ]
    },
    'ta125': {
        'title': 'ת"א 125',
        'color': '#ec4899',
        'bg_color': 'rgba(236,72,153,0.1)',
        'unit_title': "מ' יחידות (הון רשום למסחר)",
        'funds': [
            {'name': 'TA-125 MTF', 'csv_file': 'ta125_history.csv', 'tase_id': '1150283'}
        ]
    },
}

@app.route('/sector/<sector_id>')
def sector(sector_id):
    if sector_id not in SECTOR_CONFIG:
        return jsonify({"error": "Unknown sector"}), 404
        
    cfg = SECTOR_CONFIG[sector_id]
    return render_template(
        'sector.html', 
        active_nav=sector_id,
        sector_id=sector_id,
        sector_title=cfg['title'],
        color=cfg['color'],
        bg_color=cfg['bg_color'],
        unit_title=cfg['unit_title']
    )

@app.route('/data')
def get_data():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    
    def format_fund(data_dict):
        dates = sorted(data_dict.keys())
        return {
            'dates': [d.strftime('%Y-%m-%d') for d in dates],
            'values': [round(data_dict[d], 3) for d in dates]
        }
    
    result = {}
    for sector_id, cfg in SECTOR_CONFIG.items():
        val_col = 'Assets' if sector_id == 'ibi' else 'Units'
        is_harel = sector_id == 'harel'
        
        sector_funds = []
        for fund in cfg['funds']:
            filepath = os.path.join(base_dir, 'data', fund['csv_file'])
            fund_data = format_fund(read_fund_data(filepath, val_col, is_harel))
            fund_data['name'] = fund['name']
            sector_funds.append(fund_data)
            
        all_dates_set = set()
        for f in sector_funds:
            all_dates_set.update(f['dates'])
        master_dates = sorted(list(all_dates_set))
        
        datasets = []
        for f in sector_funds:
            f_values = []
            f_date_dict = dict(zip(f['dates'], f['values']))
            for d in master_dates:
                f_values.append(f_date_dict.get(d, None))
            datasets.append({
                'label': f['name'],
                'data': f_values
            })
            
        result[sector_id] = {
            'master_dates': master_dates,
            'datasets': datasets
        }
    
    return jsonify(result)

@app.route('/force-update', methods=['POST'])
def force_update():
    try:
        # Use sys.executable to ensure we use the correct python interpreter inside docker
        python_bin = sys.executable
        base_dir = os.path.dirname(os.path.abspath(__file__))
        script_path = os.path.join(base_dir, 'track_etf_units.py')
        
        logs = ""
        has_errors = False
        
        for sector_id in SECTOR_CONFIG.keys():
            res = subprocess.run([python_bin, script_path, sector_id], capture_output=True, text=True)
            logs += f"--- {sector_id.upper()} Update ---\nSTDOUT:\n{res.stdout}\nSTDERR:\n{res.stderr}\n\n"
            if res.returncode != 0 or "FAILED" in res.stdout:
                has_errors = True
        
        if has_errors:
            print(f"Update finished with some errors. Logs:\n{logs}")
            return jsonify({"status": "partial_error", "message": "השאיבה נכשלה בחלק מהקרנות או בכולן. ראה לוג במסוף.", "logs": logs}), 207
            
        print(f"Update successful. Logs:\n{logs}")
        return jsonify({"status": "success", "logs": logs})
        
    except FileNotFoundError as e:
        error_msg = f"שגיאה: הקובץ לא נמצא. {str(e)}"
        print(error_msg)
        return jsonify({"status": "error", "message": error_msg}), 500
    except subprocess.CalledProcessError as e:
        error_msg = f"שגיאת הרצה של הסקריפט: {e.output}"
        print(error_msg)
        return jsonify({"status": "error", "message": error_msg}), 500
    except Exception as e:
        # Catch ANY other error and send it back to the browser instead of crashing silently
        error_msg = f"שגיאה כללית בשרת: {str(e)}"
        print(error_msg)
        return jsonify({"status": "error", "message": error_msg}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=3333)