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
    return render_template('index.html', active_nav='/')

SECTOR_CONFIG = {
    'tech': {
        'title': 'ת"א טכנולוגיה',
        'color': '#2980b9',
        'bg_color': 'rgba(41, 128, 185, 0.1)',
        'unit_title': "מ' יחידות (הון רשום למסחר)"
    },
    'realestate': {
        'title': 'ת"א נדל"ן',
        'color': '#34495e',
        'bg_color': 'rgba(52, 73, 94, 0.1)',
        'unit_title': "מ' יחידות (הון רשום למסחר)"
    },
    'harel': {
        'title': 'הראל ת"א ביטחוניות',
        'color': '#1abc9c',
        'bg_color': 'rgba(26, 188, 156, 0.1)',
        'unit_title': "מ' יחידות (הון רשום למסחר)"
    },
    'ibi': {
        'title': 'אי.בי.אי מחקרית',
        'color': '#e67e22',
        'bg_color': 'rgba(230, 126, 34, 0.1)',
        'unit_title': 'במיליוני ש"ח (שווי נכסים)'
    }
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
    harel_data = read_fund_data(os.path.join(base_dir, "data", "harel_history.csv"), "Units", True)
    ibi_data = read_fund_data(os.path.join(base_dir, "data", "ibi_history.csv"), "Assets", False)
    tech_data = read_fund_data(os.path.join(base_dir, "data", "tech_history.csv"), "Units", False)
    realestate_data = read_fund_data(os.path.join(base_dir, "data", "realestate_history.csv"), "Units", False)
    
    def format_fund(data_dict):
        dates = sorted(data_dict.keys())
        return {
            'dates': [d.strftime('%Y-%m-%d') for d in dates],
            'values': [round(data_dict[d], 3) for d in dates]
        }
        
    return jsonify({
        'harel': format_fund(harel_data), 
        'ibi': format_fund(ibi_data),
        'tech': format_fund(tech_data),
        'realestate': format_fund(realestate_data)
    })

@app.route('/force-update', methods=['POST'])
def force_update():
    try:
        # Use sys.executable to ensure we use the correct python interpreter inside docker
        python_bin = sys.executable
        base_dir = os.path.dirname(os.path.abspath(__file__))
        script_path = os.path.join(base_dir, 'track_etf_units.py')
        
        # Run all updates
        res_harel = subprocess.run([python_bin, script_path, 'harel'], capture_output=True, text=True)
        res_ibi = subprocess.run([python_bin, script_path, 'ibi'], capture_output=True, text=True)
        res_tech = subprocess.run([python_bin, script_path, 'tech'], capture_output=True, text=True)
        res_realestate = subprocess.run([python_bin, script_path, 'realestate'], capture_output=True, text=True)
        
        # Combine logs
        logs = f"--- Harel Update ---\nSTDOUT:\n{res_harel.stdout}\nSTDERR:\n{res_harel.stderr}\n\n"
        logs += f"--- IBI Update ---\nSTDOUT:\n{res_ibi.stdout}\nSTDERR:\n{res_ibi.stderr}\n\n"
        logs += f"--- Technology Update ---\nSTDOUT:\n{res_tech.stdout}\nSTDERR:\n{res_tech.stderr}\n\n"
        logs += f"--- Real Estate Update ---\nSTDOUT:\n{res_realestate.stdout}\nSTDERR:\n{res_realestate.stderr}"
        
        if "FAILED completely on all sources" in logs or any(c != 0 for c in [res_harel.returncode, res_ibi.returncode, res_tech.returncode, res_realestate.returncode]):
            print(f"Update failed. Logs: {logs}") # Print to docker logs for debugging
            return jsonify({"status": "error", "message": f"השאיבה נכשלה בחלק מהקרנות. פירוט טכני:\n\n{logs}"}), 500
            
        print(f"Update successful. Logs: {logs}")
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