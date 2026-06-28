import os
import time
import datetime
import pandas as pd
from config.Config import (
    ROOM_NODES, TimeInterval, MODEL_TYPE, Colors, 
    DATA_SOURCE_MODE, TEST_FILE_PATH, LOOKBACK_STEPS
)
from hooks.useGPU import ConnectGPU
from hooks.useFirebase import ConnectFirebase, GetLatestFirebase
from hooks.useRunModel import ConnectModel
from utils.getStatus import GetStatus
from hooks.usePredictive import UsePredictFuturePM
from hooks.useLogger import SaveTextLog, SavePredictionCSV 

os.system('cls' if os.name == 'nt' else 'clear')

# เชื่อมต่อระบบพื้นฐาน
if DATA_SOURCE_MODE == 'FIREBASE':
    ConnectFirebase()
gpus = ConnectGPU()
model, scaler = ConnectModel()

def ValidatePredictionPerformance(preds):
    """🩺 ฟังก์ชันสแกนความสมเหตุสมผลของตัวเลขพยากรณ์"""
    for p in preds:
        if p < 0: return f"{Colors.RED}[⚠️ INVALID: AI ทายติดลบ]{Colors.RESET}"
        if p > 1000: return f"{Colors.RED}[⚠️ OUT OF BOUND: สูงเกินจริง]{Colors.RESET}"
    return ""

if __name__ == "__main__":
    mode_color = Colors.YELLOW if DATA_SOURCE_MODE == 'LOCAL' else Colors.GREEN
    header = f"🟢 REAL-TIME PREDICTION RUNNING! | ARCHITECTURE: {MODEL_TYPE} | SOURCE: {mode_color}{DATA_SOURCE_MODE}{Colors.RESET}"
    
    print(f"{Colors.BOLD}{'='*75}\n {header}\n{'='*75}{Colors.RESET}")
    SaveTextLog(f"SYSTEM STARTED [MODE: {DATA_SOURCE_MODE}]")
    
    try:
        while True:
            now = datetime.datetime.now()
            cycle_msg = f"🕒 PREDICTION CYCLE: {now.strftime('%H:%M:%S')} | SOURCE: {DATA_SOURCE_MODE}"
            print(f"\n{Colors.BOLD}{Colors.CYAN}{cycle_msg}{Colors.RESET}\n" + "-" * 75)
            SaveTextLog(cycle_msg)
            
            future_hours = [3, 6, 9, 12]
            future_times_str = [
                f"{('Today' if (now + datetime.timedelta(hours=h)).date() == now.date() else 'Tomorrow')} {(now + datetime.timedelta(hours=h)).strftime('%H:%M')}"
                for h in future_hours
            ]
                
            for room_name, node_paths in ROOM_NODES.items():
                try:
                    # 1. เลือกลอจิกดึงข้อมูลตามสวิตช์ DATA_SOURCE_MODE
                    if DATA_SOURCE_MODE == 'FIREBASE':
                        recent_df = GetLatestFirebase(node_paths)
                    else:
                        print(f"   📂 [LOCAL MODE] Reading dataset: {Colors.YELLOW}{os.path.basename(TEST_FILE_PATH)}{Colors.RESET}")
                        temp_df = pd.read_csv(TEST_FILE_PATH, on_bad_lines='skip')
                        
                        # จัดชื่อคอลัมน์ให้อยู่ในฟอร์แมตมาตรฐานที่ AI รออ่าน
                        col_map = {
                            'PM2.5': 'PM2_5', 'PM25': 'PM2_5',
                            'Temp': 'temperature', 'temp': 'temperature',
                            'Humidity (%)': 'humidity', 'hum': 'humidity'
                        }
                        temp_df.rename(columns=col_map, inplace=True)
                        recent_df = temp_df.dropna(subset=['PM2_5', 'temperature', 'humidity']).copy()

                    # 2. ตรวจสอบความยาวข้อมูลว่าพอสำหรับ Lookback ไหม
                    if len(recent_df) < LOOKBACK_STEPS:
                        raise ValueError(f"ข้อมูลสั้นเกินไป (ต้องการ {LOOKBACK_STEPS} แถว แต่มี {len(recent_df)} แถว)")

                    # 3. ส่งข้อมูลเข้าสมอง AI (พร้อมป้ายกำกับ is_indoor)
                    indoor_flag = node_paths.get('is_indoor', 1.0)
                    preds = UsePredictFuturePM(recent_df, indoor_flag, model, scaler, gpus)
                    
                    SavePredictionCSV(room_name, now, preds) 
                    
                    room_header = f"🏠 {room_name} (Environment Label: {'Indoor 🏠' if indoor_flag==1.0 else 'Outdoor 🌳'}):"
                    print(f"{Colors.BOLD}{room_header}{Colors.RESET}")
                    SaveTextLog(room_header)
                    
                    val_warning = ValidatePredictionPerformance(preds)
                    
                    for idx, h in enumerate(future_hours):
                        status_str = GetStatus(preds[idx])
                        print(f"   Next {h:2d} hrs ({future_times_str[idx]:<14}) -> PM2.5 {Colors.BOLD}{preds[idx]:6.2f}{Colors.RESET} μg/m³ | {status_str} {val_warning}")
                        SaveTextLog(f"   Next {h:2d} hrs ({future_times_str[idx]:<14}) -> PM2.5 {preds[idx]:6.2f} μg/m³ | {status_str}")
                    
                except Exception as e:
                    err_msg = f"🏠 {room_name} -> ❌ Error: {e}"
                    print(f"{Colors.RED}{err_msg}{Colors.RESET}")
                    SaveTextLog(err_msg)
            
            time.sleep(TimeInterval)
            
    except KeyboardInterrupt:
        stop_msg = "🛑 Real-time Prediction System Terminated by User."
        print(f"\n{Colors.RED}{stop_msg}{Colors.RESET}")
        SaveTextLog(stop_msg)