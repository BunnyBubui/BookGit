import joblib
from tensorflow.keras.models import load_model
from config.Config import MODEL_PATH, SCALER_PATH, MODEL_TYPE, Colors

def ConnectModel():
    print(f"{Colors.CYAN}⏳ [STEP 2] Loading {MODEL_TYPE} model and scaler...{Colors.RESET}")
    model = load_model(MODEL_PATH, compile=False)
    scaler = joblib.load(SCALER_PATH)
    print(f"{Colors.GREEN}✅ {MODEL_TYPE} Model and Scaler loaded successfully!{Colors.RESET}\n")
    return model, scaler