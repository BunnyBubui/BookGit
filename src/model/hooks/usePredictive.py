import numpy as np
import tensorflow as tf
from config.Config import LOOKBACK_STEPS, Colors

def UsePredictFuturePM(recent_data_df, is_indoor_flag, model, scaler, gpus):
    print(f"      {Colors.CYAN}-> Generating 4-Feature conditioned predictions...{Colors.RESET}")
    if len(recent_data_df) < LOOKBACK_STEPS:
        raise ValueError(f"Insufficient data (Got {len(recent_data_df)}/{LOOKBACK_STEPS} rows)")
        
    data_to_predict = recent_data_df.tail(LOOKBACK_STEPS).copy()
    
    # ประกอบร่าง Input 4 ฟีเจอร์: [PM2.5, Temp, Hum, Is_Indoor]
    df_input = data_to_predict[['PM2_5', 'temperature', 'humidity']].copy()
    df_input['is_indoor'] = float(is_indoor_flag)
    
    data_values = df_input.values
    data_scaled = scaler.transform(data_values)
    
    X_input = data_scaled.reshape(1, LOOKBACK_STEPS, 4) # ✅ มิติรับเข้าเป็น 4
    
    with tf.device('/GPU:0') if gpus else tf.device('/CPU:0'):
        predicted_scaled = model.predict(X_input, verbose=0)[0]

    future_values = []
    for pred in predicted_scaled:
        dummy_array = np.zeros((1, 4)) # ✅ ดัมมี่อาร์เรย์ 4 ช่อง
        dummy_array[0, 0] = pred       # ช่อง 0 คือ PM2_5
        real_val = scaler.inverse_transform(dummy_array)[0, 0]
        future_values.append(max(0.0, real_val))
        
    return future_values