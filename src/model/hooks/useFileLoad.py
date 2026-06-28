import os
import glob
from concurrent.futures import ThreadPoolExecutor
import pandas as pd
from config.Config import folder_path, target_locations, LOCATION_ENV_MAP, Colors

def _process_single_file(file):
    """🛠️ Worker Function สำหรับอ่านและแปลงวันที่แยกรันในแต่ละ Thread (Case-Insensitive Edition)"""
    filename = os.path.basename(file)
    filename_lower = filename.lower()
    
    # ✅ เปลี่ยนมาค้นหาแบบไม่สนใจพิมพ์ใหญ่พิมพ์เล็ก (Case-Insensitive Match)
    matched_key = next((k for k in target_locations if k.lower() in filename_lower), None)
    if not matched_key: 
        return None 

    # ดึงค่า Config ให้สอดคล้องกัน
    env_info = LOCATION_ENV_MAP.get(matched_key, {'label': 'UNKNOWN', 'is_indoor': 1.0})
    env_label, is_indoor_val = env_info['label'], env_info['is_indoor']

    try:
        temp_df = pd.read_csv(file, on_bad_lines='skip')
        
        if 'datetime' in temp_df.columns:
            temp_df['datetime'] = pd.to_datetime(temp_df['datetime'], format='%d-%m-%Y-%H-%M-%S', errors='coerce')
            temp_df = temp_df.dropna(subset=['datetime']).set_index('datetime').sort_index()
            
            if len(temp_df) > 1:
                time_diffs = temp_df.index.to_series().diff().dt.total_seconds() / 60.0
                gaps = time_diffs[time_diffs > 15.0]
                gap_msg = f"{Colors.YELLOW}⚠️ [GAP: {len(gaps)} points]{Colors.RESET}" if len(gaps)>0 else f"{Colors.GREEN}✅ [HEALTHY]{Colors.RESET}"
                print(f"      {Colors.CYAN}[{env_label}]{Colors.RESET} Loaded: {filename:<35} {gap_msg}")
        
        return {
            'filename': filename, 'df': temp_df, 
            'env_label': env_label, 'is_indoor': is_indoor_val
        }
    except Exception as e:
        print(f"      {Colors.RED}❌ [CORRUPTED] {filename}: ({e}){Colors.RESET}")
        return None

def loadFile():
    print(f"{Colors.BOLD}{Colors.CYAN}   -> [STEP 2.1] High-Speed Parallel Scanning & Loading Datasets...{Colors.RESET}")
    
    # ✅ ดึงไฟล์นามสกุล .csv ทั้งหมดแบบตรงๆ
    all_files = glob.glob(os.path.join(folder_path, "*.csv"))
    
    if not all_files:
        print(f"      {Colors.RED}⚠️ WARNING: ไม่พบไฟล์นามสกุล .csv ใดๆ เลยในโฟลเดอร์:\n      -> {folder_path}{Colors.RESET}")
        return []

    with ThreadPoolExecutor() as executor:
        results = list(executor.map(_process_single_file, all_files))
    
    valid_results = [r for r in results if r is not None]
    
    if len(valid_results) == 0 and len(all_files) > 0:
        print(f"      {Colors.RED}⚠️ WARNING: เจอไฟล์ CSV {len(all_files)} ไฟล์ แต่ไม่มีไฟล์ไหนที่มีคำว่า {target_locations} ในชื่อไฟล์เลยสักอันเดียว!{Colors.RESET}")
        
    return valid_results