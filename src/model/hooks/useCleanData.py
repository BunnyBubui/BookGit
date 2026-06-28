import pandas as pd
import numpy as np
from config.Config import Resample, Colors

def UseCleanData(file_data_list):
    print(f"\n{Colors.BOLD}{Colors.CYAN}   -> [STEP 2.2] Fast Sandboxed Cleaning & Injecting Label Features...{Colors.RESET}")
    cleaned_dfs = []
    total_raw, total_final, total_dropped = 0, 0, 0

    for idx, item in enumerate(file_data_list, 1):
        fname, df = item['filename'], item['df']
        env_label, is_indoor_val = item['env_label'], item['is_indoor']

        print(f"{Colors.CYAN}      -> [{idx}/{len(file_data_list)}] Cleaning: {Colors.YELLOW}{fname} {Colors.CYAN}({env_label}){Colors.RESET}")
        
        raw_rows = len(df)
        total_raw += raw_rows

        target_cols = [c for c in ['PM2_5', 'temperature', 'humidity'] if c in df.columns]
        
        if target_cols:
            # ✅ Downcast เป็น float32 ลดการกิน RAM ลง 50% ทันที
            df_sub = df[target_cols].astype(np.float32)

            # ✅ คำนวณตัด Outliers ด้วย Numpy Array (ไวกว่า Pandas .quantile() หลายเท่าตัว)
            vals = df_sub.values
            q1 = np.nanpercentile(vals, 1, axis=0)
            q99 = np.nanpercentile(vals, 99, axis=0)
            clipped_vals = np.clip(vals, q1, q99)
            
            df_clipped = pd.DataFrame(clipped_vals, index=df_sub.index, columns=target_cols)

            # Resample สเกลเวลาตาม Config
            df_resampled = df_clipped.resample(Resample).mean()
            resampled_rows = len(df_resampled)

            df_cleaned = df_resampled.interpolate(method='linear', limit=3).dropna().copy()
            df_cleaned['is_indoor'] = np.float32(is_indoor_val)

            final_rows = len(df_cleaned)
            dropped = resampled_rows - final_rows
            
            total_final += final_rows
            total_dropped += dropped
            cleaned_dfs.append(df_cleaned)

    print(f"\n{Colors.CYAN}      -> Audit Summary Across All Environments:{Colors.RESET}")
    print(f"         • Total Raw Rows:       {total_raw:,} rows")
    print(f"         • Dropped Dead Gaps:    {total_dropped:,} rows")
    print(f"         • {Colors.BOLD}{Colors.GREEN}Ready 4-Feature Rows:   {total_final:,} rows (100% Isolated & Labeled){Colors.RESET}")

    return cleaned_dfs