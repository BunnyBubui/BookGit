import os
import csv
import datetime
from config.Config import save_dir

LOG_TXT_PATH = os.path.join(save_dir, "logs/system_runtime.log")
LOG_CSV_PATH = os.path.join(save_dir, "csv/prediction_history.csv")

def SaveTextLog(message):
    """บันทึกข้อความเหตุการณ์ลงไฟล์ .log"""
    now_str = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    with open(LOG_TXT_PATH, mode='a', encoding='utf-8') as f:
        # ลบโค้ดสี ANSI ออกก่อนบันทึกลงไฟล์เท็กซ์
        clean_msg = import_re().sub('', message)
        f.write(f"[{now_str}] {clean_msg}\n")

def SavePredictionCSV(room_name, now_dt, preds):
    """บันทึกตัวเลขพยากรณ์ลงตาราง .csv"""
    file_exists = os.path.isfile(LOG_CSV_PATH)
    with open(LOG_CSV_PATH, mode='a', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow(['timestamp', 'room', 'pred_3h', 'pred_6h', 'pred_9h', 'pred_12h'])
        writer.writerow([
            now_dt.strftime('%Y-%m-%d %H:%M:%S'),
            room_name,
            f"{preds[0]:.2f}",
            f"{preds[1]:.2f}",
            f"{preds[2]:.2f}",
            f"{preds[3]:.2f}"
        ])

def import_re():
    import re
    return re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')