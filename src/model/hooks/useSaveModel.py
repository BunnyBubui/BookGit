import os
from config.Config import Colors

def UseSaveModel(model, model_type, target_locations, save_dir):
    print(f"{Colors.CYAN}   -> Saving model files...{Colors.RESET}")
    prefix = f'pm25_{model_type.lower()}_multi_'
    model_filename = prefix + '_'.join(target_locations) + '.keras' if target_locations else f'pm25_{model_type.lower()}_multi_all.keras'
    
    full_path = os.path.join(save_dir, model_filename)
    model.save(full_path)
    print(f"{Colors.GREEN}   -> [OK] Saved successfully as: {model_filename}{Colors.RESET}")