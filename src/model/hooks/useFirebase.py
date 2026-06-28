import firebase_admin
from firebase_admin import credentials, db
import pandas as pd
from config.Config import CREDENTIAL_PATH, DATABASE_URL, FIREBASE_COLUMNS_MAP, LimitData, Colors

def ConnectFirebase():
    print(f"{Colors.CYAN}⏳ [STEP 1] Connecting to Firebase Database...{Colors.RESET}")
    try:
        if not firebase_admin._apps:
            cred = credentials.Certificate(CREDENTIAL_PATH)
            firebase_admin.initialize_app(cred, {'databaseURL': DATABASE_URL})
        print(f"{Colors.GREEN}✅ Firebase connected successfully!{Colors.RESET}")
    except Exception as e:
        print(f"{Colors.RED}❌ Firebase connection failed: {e}{Colors.RESET}"); exit()

def GetLatestFirebase(node_paths):
    print(f"      {Colors.CYAN}-> Fetching sensor data from database...{Colors.RESET}")
    raw_dust = db.reference(node_paths['dust']).order_by_key().limit_to_last(LimitData).get()
    raw_dht = db.reference(node_paths['dht']).order_by_key().limit_to_last(LimitData).get()
    
    if not raw_dust or not raw_dht:
        raise ValueError("Incomplete sensor data received")
    
    print(f"      {Colors.CYAN}-> Processing and interpolating timeline...{Colors.RESET}")
    df_dust = pd.DataFrame.from_dict(raw_dust, orient='index')
    df_dht = pd.DataFrame.from_dict(raw_dht, orient='index')
    
    df_dust.rename(columns=FIREBASE_COLUMNS_MAP, inplace=True)
    df_dht.rename(columns=FIREBASE_COLUMNS_MAP, inplace=True)
    
    def process_time(df):
        if 'datetime' in df.columns:
            df['datetime'] = pd.to_datetime(df['datetime'], format='%d-%m-%Y-%H-%M-%S', errors='coerce')
            df.set_index('datetime', inplace=True)
        else:
            try: df.index = pd.to_datetime(df.index, format='%d-%m-%Y-%H-%M-%S')
            except: df.index = pd.to_datetime(df.index)
        return df

    df_dust = process_time(df_dust)
    df_dht = process_time(df_dht)
    
    if 'PM2_5' in df_dust.columns: df_dust['PM2_5'] = pd.to_numeric(df_dust['PM2_5'], errors='coerce')
    if 'temperature' in df_dht.columns: df_dht['temperature'] = pd.to_numeric(df_dht['temperature'], errors='coerce')
    if 'humidity' in df_dht.columns: df_dht['humidity'] = pd.to_numeric(df_dht['humidity'], errors='coerce')
        
    df_combined = pd.concat([df_dust, df_dht], axis=1, sort=False)
    
    if not all(col in df_combined.columns for col in ['PM2_5', 'temperature', 'humidity']):
        raise ValueError("Missing required columns (PM2_5, temperature, or humidity)")
        
    df_final = df_combined[['PM2_5', 'temperature', 'humidity']]
    df_resampled = df_final.resample('5min').mean()
    df_resampled = df_resampled.interpolate(method='linear', limit=3).dropna()
    
    return df_resampled