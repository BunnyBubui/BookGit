import os
from hooks.useGPU import ConnectGPU
from hooks.useFileLoad import loadFile
from hooks.useCleanData import UseCleanData
from hooks.usePreprocessing import UsePreprocessing
from hooks.useTrainModel import UseTrainModel
from hooks.useSaveModel import UseSaveModel
from config.Config import save_dir, target_locations, MODEL_TYPE, Colors

os.system('cls' if os.name == 'nt' else 'clear')

print(f"{Colors.BOLD}{Colors.CYAN}================================================================={Colors.RESET}")
print(f"{Colors.BOLD}{Colors.CYAN} 🧠 STARTING MODEL TRAINING PROCESS | ARCHITECTURE: {MODEL_TYPE}{Colors.RESET}")
print(f"{Colors.BOLD}{Colors.CYAN}=================================================================\n{Colors.RESET}")

print(f"{Colors.CYAN}⏳ [STEP 1] Checking Hardware Resources (GPU/CPU)...{Colors.RESET}")
gpus = ConnectGPU()
os.makedirs(save_dir, exist_ok=True)

print(f"\n{Colors.CYAN}⏳ [STEP 2] Loading and Cleaning Raw Data...{Colors.RESET}")
df_list = loadFile()
df_resampled = UseCleanData(df_list)

print(f"\n{Colors.CYAN}⏳ [STEP 3] Preprocessing and Train/Test Splitting...{Colors.RESET}")
X_train, X_test, y_train, y_test = UsePreprocessing(df_resampled)

print(f"\n{Colors.CYAN}⏳ [STEP 4] Constructing and Training {MODEL_TYPE} Model...{Colors.RESET}")
model, history = UseTrainModel(X_train, X_test, y_train, y_test, MODEL_TYPE, gpus)

print(f"\n{Colors.CYAN}⏳ [STEP 5] Saving Model to Disk...{Colors.RESET}")
UseSaveModel(model, MODEL_TYPE, target_locations, save_dir)

print(f"\n{Colors.BOLD}{Colors.GREEN}🎉 Training Process Successfully Completed! Ready for Prediction.{Colors.RESET}")