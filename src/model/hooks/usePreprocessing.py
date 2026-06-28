import os
import pandas as pd
import numpy as np
import joblib
from sklearn.preprocessing import MinMaxScaler
from config.Config import save_dir, SCALER_PATH, RESAMPLE_MINUTES, LOOKBACK_STEPS, Colors

def UsePreprocessing(cleaned_dfs):
    print(f"{Colors.CYAN}   -> [1/4] Initializing 4-Feature Agnostic MinMaxScaler...{Colors.RESET}")
    lookback = LOOKBACK_STEPS # ✅ ดึงค่า 180 steps มาจาก Config

    # คำนวณสเต็ปอนาคตสำหรับ [3ชม., 6ชม., 9ชม., 12ชม.] อัตโนมัติ!
    target_hours = [3, 6, 9, 12]
    steps_future = [int((h * 60) / RESAMPLE_MINUTES) for h in target_hours] # ถ้า 1min -> [180, 360, 540, 720]
    max_step = max(steps_future)

    all_values = np.vstack([df.values for df in cleaned_dfs])
    scaler = MinMaxScaler(feature_range=(0, 1))
    scaler.fit(all_values)
    
    print(f"{Colors.CYAN}   -> [2/4] Saving Dynamic Scaler to: {SCALER_PATH}...{Colors.RESET}")
    joblib.dump(scaler, SCALER_PATH)

    print(f"{Colors.CYAN}   -> [3/4] Slicing strictly continuous sequences (Interval: {RESAMPLE_MINUTES}m)...{Colors.RESET}")
    X, y = [], []
    
    # ✅ ปลดล็อกสมการเช็คความต่อเนื่อง: ใช้คูณด้วย RESAMPLE_MINUTES ตัวจริง!
    expected_time_delta = pd.Timedelta(minutes=RESAMPLE_MINUTES * (lookback + max_step - 1))

    for df in cleaned_dfs:
        data_scaled = scaler.transform(df.values)
        timestamps = df.index
        
        for i in range(len(data_scaled) - lookback - max_step):
            actual_time_delta = timestamps[i + lookback + max_step - 1] - timestamps[i]
            if actual_time_delta == expected_time_delta:
                X.append(data_scaled[i : i + lookback])
                y.append([
                    data_scaled[i + lookback + steps_future[0] - 1, 0],
                    data_scaled[i + lookback + steps_future[1] - 1, 0],
                    data_scaled[i + lookback + steps_future[2] - 1, 0],
                    data_scaled[i + lookback + steps_future[3] - 1, 0]
                ])

    X, y = np.array(X), np.array(y)

    print(f"{Colors.CYAN}   -> [4/4] Splitting High-Resolution Data (Train 70% / Test 30%)...{Colors.RESET}")
    split = int(0.7 * len(X))
    X_train, X_test = X[:split], X[split:]
    y_train, y_test = y[:split], y[split:]

    print(f"{Colors.BOLD}{Colors.GREEN}   -> [Done] Sliced {len(X_train):,} Train | {len(X_test):,} Test (Shape: {X_train.shape}){Colors.RESET}")
    return X_train, X_test, y_train, y_test