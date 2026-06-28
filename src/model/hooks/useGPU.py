import os
import tensorflow as tf
from config.Config import Colors

os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'
tf.get_logger().setLevel('ERROR')

def ConnectGPU():
    print(f"{Colors.CYAN}   -> Checking hardware resources...{Colors.RESET}")
    gpus = tf.config.list_physical_devices('GPU')
    if gpus:
        try:
            for gpu in gpus: 
                tf.config.experimental.set_memory_growth(gpu, True)
            print(f"{Colors.GREEN}   -> GPU Enabled: {len(gpus)} device(s) found.{Colors.RESET}")
            return gpus
        except Exception as e:
            pass
    
    print(f"{Colors.GREEN}   -> Hardware: CPU Optimized (High-Speed Inference Mode).{Colors.RESET}")
    return None