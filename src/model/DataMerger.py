import os
import glob
import re
import pandas as pd
from config.Config import Colors, RAW_FOLDER, OUTPUT_FOLDER

def safe_read_csv(file_path):
    """🩺 ฟังก์ชันอ่าน CSV อัจฉริยะ: สลับเข้ารหัสอัตโนมัติป้องกันบั๊กองศา (°C)"""
    encodings_to_try = ['utf-8', 'cp1252', 'latin1', 'tis-620']
    for enc in encodings_to_try:
        try:
            return pd.read_csv(file_path, encoding=enc, on_bad_lines='skip')
        except UnicodeDecodeError:
            continue
    # หากพังหมดทุกรหัส บังคับอ่านด้วย latin1 (รองรับทุกไบต์บนโลกโดยไม่ดีด Error)
    return pd.read_csv(file_path, encoding='latin1', on_bad_lines='skip')

def MergeRawSensorData():
    os.system('cls' if os.name == 'nt' else 'clear')
    os.makedirs(OUTPUT_FOLDER, exist_ok=True)

    print(f"{Colors.BOLD}{Colors.CYAN}================================================================={Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.CYAN} 🔄 AUTOMATED SENSOR DATA MERGER (ระบบรวมไฟล์ DHT22 + PM Original){Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.CYAN}=================================================================\n{Colors.RESET}")

    print(f"{Colors.CYAN}⏳ [STEP 1] Scanning raw directory for CSV files...{Colors.RESET}")
    pm_files = glob.glob(os.path.join(RAW_FOLDER, "PM_Original_*.csv"))
    dht_files = glob.glob(os.path.join(RAW_FOLDER, "DHT22_*.csv"))

    if not pm_files and not dht_files:
        print(f"{Colors.RED}❌ ไม่พบไฟล์ดิบใน: {RAW_FOLDER}{Colors.RESET}"); return

    date_pattern = re.compile(r"(\d{2}-\d{2}-\d{4})")

    pm_dict = {date_pattern.search(f).group(1): f for f in pm_files if date_pattern.search(f)}
    dht_dict = {date_pattern.search(f).group(1): f for f in dht_files if date_pattern.search(f)}

    matched_dates = sorted(list(set(pm_dict.keys()).intersection(set(dht_dict.keys()))))

    print(f"{Colors.GREEN}   -> Found {len(matched_dates)} matched pair(s) ready for merging.{Colors.RESET}\n")

    if not matched_dates: return

    target_columns_order = [
        'datetime', 'humidity', 'temperature', 
        'PC0_1', 'PC0_3', 'PC0_5', 'PC10', 'PC1_0', 'PC2_5', 'PC5_0', 
        'PM0_1', 'PM0_3', 'PM0_5', 'PM10', 'PM1_0', 'PM2_5', 'PM5_0'
    ]

    success_count = 0
    fail_count = 0

    for idx, date_str in enumerate(matched_dates, 1):
        print(f"{Colors.BOLD}📦 [STEP 2.{idx}] Processing Date: {Colors.YELLOW}{date_str}{Colors.RESET}")
        
        pm_path = pm_dict[date_str]
        dht_path = dht_dict[date_str]
        
        try:
            print(f"      {Colors.CYAN}-> Reading PM_Original & DHT22 datasets (Auto-Encoding)...{Colors.RESET}")
            df_pm = safe_read_csv(pm_path)   # ✅ เรียกใช้ฟังก์ชันอ่านปลอดภัย
            df_dht = safe_read_csv(dht_path) # ✅ เรียกใช้ฟังก์ชันอ่านปลอดภัย

            df_pm['dt'] = pd.to_datetime(df_pm['Date'].astype(str) + ' ' + df_pm['Time'].astype(str), format='%d/%m/%Y %H:%M:%S', errors='coerce')
            df_dht['dt'] = pd.to_datetime(df_dht['Date'].astype(str) + ' ' + df_dht['Time'].astype(str), format='%d/%m/%Y %H:%M:%S', errors='coerce')

            df_pm = df_pm.dropna(subset=['dt']).sort_values('dt')
            df_dht = df_dht.dropna(subset=['dt']).sort_values('dt')

            print(f"      {Colors.CYAN}-> Cleaning & Mapping column formats...{Colors.RESET}")
            df_pm.columns = [col.replace('.', '_') for col in df_pm.columns]
            
            # ค้นหาคอลัมน์ความชื้นและอุณหภูมิแบบยืดหยุ่น (เผื่อบางไฟล์ชื่อคอลัมน์พิมพ์ต่างกัน)
            hum_col = next((c for c in df_dht.columns if 'hum' in c.lower()), None)
            temp_col = next((c for c in df_dht.columns if 'temp' in c.lower()), None)
            
            rename_map = {}
            if hum_col: rename_map[hum_col] = 'humidity'
            if temp_col: rename_map[temp_col] = 'temperature'
            df_dht.rename(columns=rename_map, inplace=True)

            print(f"      {Colors.CYAN}-> Merging timelines (Smart Outer Join & Fill)...{Colors.RESET}")
            
            cols_pm = ['dt', 'PC0_1', 'PC0_3', 'PC0_5', 'PC1_0', 'PC2_5', 'PC5_0', 'PC10', 'PM0_1', 'PM0_3', 'PM0_5', 'PM1_0', 'PM2_5', 'PM5_0', 'PM10']
            available_pm_cols = [c for c in cols_pm if c in df_pm.columns]

            merged_df = pd.merge(
                df_pm[available_pm_cols],
                df_dht[['dt', 'humidity', 'temperature']],
                on='dt', how='outer'
            ).sort_values('dt').ffill().bfill()

            merged_df['datetime'] = merged_df['dt'].dt.strftime('%d-%m-%Y-%H-%M-%S')

            # เติมคอลัมน์ที่ขาดไปให้ครบถ้าไฟล์บางวันส่งเซนเซอร์มาไม่ครบ
            for col in target_columns_order:
                if col not in merged_df.columns:
                    merged_df[col] = 0.0

            final_df = merged_df[target_columns_order]

            output_filename = f"merge_PM_Original_{date_str}.csv"
            save_full_path = os.path.join(OUTPUT_FOLDER, output_filename)
            
            final_df.to_csv(save_full_path, index=False)
            print(f"      {Colors.GREEN}✅ [MERGED SUCCESSFULLY] Saved ({len(final_df):,} rows) -> {output_filename}{Colors.RESET}\n")
            success_count += 1

        except Exception as e:
            print(f"      {Colors.RED}❌ [FAILED] Cannot merge date {date_str}: {e}{Colors.RESET}\n")
            fail_count += 1

    print(f"{Colors.BOLD}{Colors.GREEN}================================================================={Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.GREEN} 🎉 SUMMARY: Merged {success_count} file(s) | Failed {fail_count} file(s){Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.GREEN}================================================================={Colors.RESET}")

if __name__ == "__main__":
    MergeRawSensorData()