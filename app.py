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
                    if is_harel: val /= 1000000
                    data_dict[date_obj] = val
                except: pass
    return data_dict

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/data')
def get_data():
    harel_data = read_fund_data("/app/data/harel_history.csv", "Units", True)
    ibi_data = read_fund_data("/app/data/ibi_history.csv", "Assets", False)
    
    all_dates = sorted(list(set(harel_data.keys()).union(set(ibi_data.keys()))))
    
    dates_str, harel_list, ibi_list = [], [], []
    last_harel, last_ibi = None, None

    for d in all_dates:
        dates_str.append(d.strftime('%Y-%m-%d'))
        if d in harel_data: last_harel = harel_data[d]
        if d in ibi_data: last_ibi = ibi_data[d]
        
        harel_list.append(round(last_harel, 3) if last_harel else None)
        ibi_list.append(round(last_ibi, 2) if last_ibi else None)
        
    return jsonify({'dates': dates_str, 'harel': harel_list, 'ibi': ibi_list})

@app.route('/force-update', methods=['POST'])
def force_update():
    try:
        # Use sys.executable to ensure we use the correct python interpreter inside docker
        python_bin = sys.executable
        script_path = '/app/track_etf_units.py'
        
        # Run Harel update
        res_harel = subprocess.run([python_bin, script_path, 'harel'], capture_output=True, text=True)
        # Run IBI update
        res_ibi = subprocess.run([python_bin, script_path, 'ibi'], capture_output=True, text=True)
        
        # Combine logs
        logs = f"--- Harel Update ---\nSTDOUT:\n{res_harel.stdout}\nSTDERR:\n{res_harel.stderr}\n\n"
        logs += f"--- IBI Update ---\nSTDOUT:\n{res_ibi.stdout}\nSTDERR:\n{res_ibi.stderr}"
        
        # Check for FAILED or if the script returned an error code
        if "FAILED" in logs or res_harel.returncode != 0 or res_ibi.returncode != 0:
            print(f"Update failed. Logs: {logs}") # Print to docker logs for debugging
            return jsonify({"status": "error", "message": f"השאיבה נכשלה. פירוט טכני:\n\n{logs}"}), 500
            
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