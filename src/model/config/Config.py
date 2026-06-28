import os

# ==============================================================================
# 🎨 UI Design System (ANSI Color Palette)
# ==============================================================================
class Colors:
    CYAN = '\033[96m'      # Processing Step
    GREEN = '\033[92m'     # Success / Healthy
    YELLOW = '\033[93m'    # Warning / Moderate
    RED = '\033[91m'       # Error / Unhealthy
    BOLD = '\033[1m'       # Emphasis
    RESET = '\033[0m'      # Reset Color

# ==============================================================================
# 🔇 Clean Environment Engine (Disable TF Warnings)
# ==============================================================================
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'  
os.environ['TF_ENABLE_ONEDNN_OPTS'] = '0' 

# Split Room in ModelTest
LOCATION_ENV_MAP = {
    'knbd': {'label': 'INDOOR 🏠', 'is_indoor': 1.0},
    'supat': {'label': 'INDOOR 🏠', 'is_indoor': 1.0},
    'merge_PM_Original': {'label': 'OUTDOOR 🌳', 'is_indoor': 0.0}
}

ROOM_NODES = {
    "Dean's Office": {
        'dust': 'SAC/DustSensor/c3_knbd/Point01',
        'dht': 'SAC/DHT22/c3_knbd/Point01',
        'is_indoor': 1.0  # ✅ ระบุว่าเป็นห้องปิด
    },
    "Ajarn Supat's Office": {
        'dust': 'SAC/DustSensor/c3_supat/Point01',
        'dht': 'SAC/DHT22/c3_supat/Point01',
        'is_indoor': 1.0  # ✅ ระบุว่าเป็นห้องปิด
    }
}

FIREBASE_COLUMNS_MAP = {
    'PM2_5': 'PM2_5', 'PM25': 'PM2_5',              
    'temp': 'temperature', 'Temp': 'temperature', 'temperature': 'temperature', 
    'humidity': 'humidity', 'hum': 'humidity', 'Hum': 'humidity'
}

# Train Path
folder_path = r'D:\BookProject\BookGit\src\data'
save_dir = r'D:\BookProject\BookGit\src\model\file'

# ⚙️ Setting Firebase
CREDENTIAL_PATH = r'D:\BookProject\BookGit\firebase_setting.json' 
DATABASE_URL = 'https://lab68-118f4-default-rtdb.asia-southeast1.firebasedatabase.app/'

# ⚙️ Setting Model
MODEL_TYPE = "LSTM"
target_locations = ['knbd', 'supat', 'merge_PM_Original']
loc_suffix = '_'.join(target_locations) if target_locations else 'all'
MODEL_PATH = save_dir + fr'\pm25_{MODEL_TYPE.lower()}_multi_{loc_suffix}.keras'
SCALER_PATH = save_dir + fr'\pm25_scaler_{loc_suffix}.pkl'

# Model Train Rate
RESAMPLE_MINUTES = 5
Resample = f"{RESAMPLE_MINUTES}min"
Epochs = 200
BatchSize = 32
EPOCHS_MAX = 500
PATIENCE_VALUE = 50

# Conv1D
KernelSize = 5
Filters = 128
KernelRegularizer = 0.005
Activation = "relu"
DropoutValue = 0.2
Units = 256

#MaxPooling1D
PoolSize = 2

#Model Compile
Optimizer = "adam"
Metrics = "mae"
DenseValue = 64

# ⚙️ Setting for Testing
LOOKBACK_STEPS = int(180 / RESAMPLE_MINUTES)
TimeInterval = 10
LimitData = 15000

# ⚙️ ตั้งค่าพิกัดโฟลเดอร์ต้นทาง (ไฟล์ดิบ) และปลายทาง (ไฟล์รวม)
DATA_SOURCE_MODE = 'LOCAL' #LOCAL || FIREBASE
FILE_TEST = "merge_PM_Original"
DATE_TEST = "27-06-2026"

TEST_FILE_PATH = f'D:\BookProject\BookGit\src\data\{FILE_TEST}_{DATE_TEST}.csv'
RAW_FOLDER = r"D:\BookProject\BookGit\src\data\old_data" # โฟลเดอร์ที่คุณเอาไฟล์ดิบมาวาง
OUTPUT_FOLDER = r"D:\BookProject\BookGit\src\data"  # โฟลเดอร์ปลายทางที่ระบบพยากรณ์รออ่าน