import pandas as pd
import numpy as np
from config.Config import Resample, Colors

def UseCleanData(file_data_list):
    print(f"\n{Colors.BOLD}{Colors.CYAN}   -> [STEP 2.2] Advanced Elastic Cleaning & Dictionary Dynamic Mapping...{Colors.RESET}")
    cleaned_dfs = []
    total_raw, total_final, total_dropped = 0, 0, 0

    # 딕ชันนารี แปลงชื่อคอลัมน์จากหน้าบ้านทุกรูปแบบให้เข้าฟอร์แมตหลักของ AI
    FUZZY_MAP = {
        'PM2.5': 'PM2_5', 'PM25': 'PM2_5', 'pm25': 'PM2_5', 'PM2_5': 'PM2_5',
        'Temp': 'temperature', 'temp': 'temperature', 'Temperature': 'temperature', 'temperature': 'temperature',
        'Humidity (%)': 'humidity', 'humidity': 'humidity', 'hum': 'humidity', 'Hum': 'humidity'
    }

    for idx, item in enumerate(file_data_list, 1):
        fname, df = item['filename'], item['df'].copy()
        env_label, is_indoor_val = item['env_label'], item['is_indoor']

        # ✅ แปลงชื่อคอลัมน์ที่มีทั้งหมดในไฟล์ให้เป็นชื่อมาตรฐานก่อนทำอะไรทั้งสิ้น
        df.rename(columns=FUZZY_MAP, inplace=True)

        raw_rows = len(df)
        total_raw += raw_rows

        # ตรวจสอบฟีเจอร์หลักที่ AI บังคับใช้เรียน
        core_cols = ['PM2_5', 'temperature', 'humidity']
        available_cols = [c for c in core_cols if c in df.columns]
        
        # ถ้าในไฟล์มีคอลัมน์หลักไม่ครบ 3 ตัว ให้ข้ามไปก่อนเพื่อป้องกันคณิตศาสตร์พัง
        if len(available_cols) < 3:
            print(f"      {Colors.RED}⚠️ [{idx}/{len(file_data_list)}] Skipped: {fname} (Columns missing! Found only {available_cols}){Colors.RESET}")
            continue

        print(f"{Colors.CYAN}      -> [{idx}/{len(file_data_list)}] Processing & Imputing: {Colors.YELLOW}{fname} {Colors.CYAN}({env_label}){Colors.RESET}")
        
        # แปลงข้อมูลเป็น float32 รีด RAM
        df_sub = df[core_cols].astype(np.float32)

        # ตัด Outliers ระดับบน-ล่าง 1% ด้วยสปีด Numpy
        vals = df_sub.values
        q1 = np.nanpercentile(vals, 1, axis=0)
        q99 = np.nanpercentile(vals, 99, axis=0)
        clipped_vals = np.clip(vals, q1, q99)
        
        df_clipped = pd.DataFrame(clipped_vals, index=df_sub.index, columns=core_cols)

        # จัดกลุ่มบีบอัดเวลาตามมิติ Config (เช่น 5min)
        df_resampled = df_clipped.resample(Resample).mean()
        resampled_rows = len(df_resampled)

        # ✅ ขยายเกณฑ์ยอมรับการ Interpolate เพิ่มขึ้นเป็น limit=12 (ยอมให้เดาข้อมูลช่วงสั้นๆ ได้กว้างขึ้น)
        # และใช้ ffill/bfill ประคองหัวท้ายตาราง เพื่อไม่ให้ .dropna() สั่งลบข้อมูลทิ้งจนหมดเกลี้ยง
        df_filled = df_resampled.interpolate(method='linear', limit=12)
        df_filled = df_filled.ffill().bfill() 
        df_cleaned = df_filled.dropna().copy()

        # แปะป้ายฟีเจอร์ที่ 4 (is_indoor)
        df_cleaned['is_indoor'] = np.float32(is_indoor_val)

        final_rows = len(df_cleaned)
        if final_rows > 0:
            dropped = resampled_rows - final_rows
            total_final += final_rows
            total_dropped += dropped
            cleaned_dfs.append(df_cleaned)
        else:
            print(f"      {Colors.RED}⚠️ WARNING: {fname} กลายเป็นตารางว่างเปล่าหลัง Dropna!{Colors.RESET}")

    print(f"\n{Colors.CYAN}      -> Audit Summary Across All Environments:{Colors.RESET}")
    print(f"         • Total Raw Rows:       {total_raw:,} rows")
    print(f"         • Dropped Dead Gaps:    {total_dropped:,} rows")
    
    if len(cleaned_dfs) == 0:
        print(f"         • {Colors.BOLD}{Colors.RED}Ready 4-Feature Rows:   0 rows ❌ (ระบบวิกฤต ข้อมูลถูกลบทิ้งหมด!){Colors.RESET}")
    else:
        print(f"         • {Colors.BOLD}{Colors.GREEN}Ready 4-Feature Rows:   {total_final:,} rows (100% Isolated & Labeled){Colors.RESET}")

    return cleaned_dfs