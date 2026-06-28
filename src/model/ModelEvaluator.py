import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from sklearn.metrics import r2_score, mean_absolute_error, mean_squared_error
from config.Config import save_dir, SCALER_PATH, MODEL_PATH, Colors, RESAMPLE_MINUTES
from hooks.useRunModel import ConnectModel
from hooks.useFileLoad import loadFile
from hooks.useCleanData import UseCleanData
from hooks.usePreprocessing import UsePreprocessing

def EvaluateModelPerformance():
    os.system('cls' if os.name == 'nt' else 'clear')
    print(f"{Colors.BOLD}{Colors.CYAN}================================================================={Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.CYAN} 🩺 AUTOMATED AI HEALTH AUDIT & PERFORMANCE EVALUATOR (v3 Snapshot){Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.CYAN}=================================================================\n{Colors.RESET}")

    print(f"{Colors.CYAN}⏳ [1/5] Loading trained AI Model & Scaler...{Colors.RESET}")
    try:
        model, scaler = ConnectModel()
    except Exception as e:
        print(f"{Colors.RED}❌ ไม่สามารถโหลดโมเดลได้: {e}{Colors.RESET}"); return

    print(f"{Colors.CYAN}⏳ [2/5] Preparing unseen Test Datasets...{Colors.RESET}")
    raw_files = loadFile()
    if not raw_files: return

    cleaned_dfs = UseCleanData(raw_files)
    _, X_test, _, y_test_scaled = UsePreprocessing(cleaned_dfs)

    if len(X_test) == 0: return

    print(f"{Colors.CYAN}⏳ [3/5] Running high-speed batch inference on {len(X_test):,} test sequences...{Colors.RESET}")
    y_pred_scaled = model.predict(X_test, batch_size=128, verbose=0)

    print(f"{Colors.CYAN}⏳ [4/5] Exact Tensor Denormalizing to real PM2.5 units (μg/m³)...{Colors.RESET}")
    
    def denormalize_exact(tensor_2d):
        samples, horizons = tensor_2d.shape
        flat_vals = tensor_2d.flatten()
        dummy_matrix = np.zeros((len(flat_vals), 4))
        dummy_matrix[:, 0] = flat_vals
        real_flat = scaler.inverse_transform(dummy_matrix)[:, 0]
        return real_flat.reshape(samples, horizons)

    y_test_real = denormalize_exact(y_test_scaled) 
    y_pred_real = denormalize_exact(y_pred_scaled)

    actual_3h = y_test_real[:, 0]
    pred_3h = y_pred_real[:, 0]

    mae = mean_absolute_error(actual_3h, pred_3h)
    rmse = np.sqrt(mean_squared_error(actual_3h, pred_3h))
    r2 = r2_score(actual_3h, pred_3h)
    
    actual_diff = np.diff(actual_3h)
    pred_diff = np.diff(pred_3h) 
    active_moves = np.abs(actual_diff) > 0.1
    dir_acc = np.mean((actual_diff[active_moves] * pred_diff[active_moves]) > 0) * 100.0

    print(f"\n{Colors.BOLD}{Colors.GREEN}================================================================={Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.GREEN} 🏆 AI PERFORMANCE AUDIT REPORT (ผลการสอบสมองกลอนุกรมเวลา){Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.GREEN}================================================================={Colors.RESET}")
    print(f" 1. R² Score (ค่าความสัมพันธ์ข้อมูล):  {Colors.BOLD}{r2:6.4f}{Colors.RESET}  ({('🟢 เกรด A+ สมบูรณ์เยี่ยม' if r2>0.8 else '🟡 พอใช้ได้' if r2>0.6 else '🔴 สอบตก')})")
    print(f" 2. Directional Accuracy (ทายถูกทิศ): {Colors.BOLD}{dir_acc:6.2f}%{Colors.RESET} ({('🟢 เชื่อถือได้' if dir_acc>75 else '🔴 เสี่ยงเปิดเครื่องฟอกพลาด')})")
    print(f" 3. MAE (ทายพลาดเฉลี่ย):               {Colors.BOLD}{mae:6.2f}{Colors.RESET}  μg/m³")
    print(f" 4. RMSE (ลงโทษความพลาดจุดใหญ่):      {Colors.BOLD}{rmse:6.2f}{Colors.RESET}  μg/m³")
    print(f"{Colors.GREEN}=================================================================\n{Colors.RESET}")

    print(f"{Colors.CYAN}⏳ [5/5] Refreshing Master Dashboard & Versioning Snapshot...{Colors.RESET}")
    
    fig = plt.figure(figsize=(16, 10))
    model_basename = os.path.splitext(os.path.basename(MODEL_PATH))[0]
    fig.suptitle(f"AI Evaluation: [{model_basename.upper()}] (Resolution: {RESAMPLE_MINUTES}m)", fontsize=15, fontweight='bold', y=0.96)

    ax1 = fig.add_subplot(2, 2, 1)
    sample_slice = slice(0, min(250, len(actual_3h)))
    ax1.plot(actual_3h[sample_slice], label='Actual PM2.5 (Sensor)', color='#1f77b4', linewidth=2)
    ax1.plot(pred_3h[sample_slice], label='AI Predicted PM2.5', color='#ff7f0e', linestyle='--', linewidth=1.8)
    ax1.set_title("A. Prediction Waveform Tracking (250 Unseen Steps)", fontweight='bold')
    ax1.set_ylabel("PM2.5 (μg/m³)")
    ax1.grid(True, linestyle=':', alpha=0.6)
    ax1.legend(loc='upper right')

    ax2 = fig.add_subplot(2, 2, 2)
    ax2.scatter(actual_3h, pred_3h, alpha=0.3, color='#2ca02c', s=15)
    max_val = max(np.max(actual_3h), np.max(pred_3h))
    ax2.plot([0, max_val], [0, max_val], color='red', linestyle='-', linewidth=2, label='Ideal Perfect Fit (y=x)')
    ax2.set_title(f"B. Correlation Scatter Plot (R² = {r2:.3f})", fontweight='bold')
    ax2.set_xlabel("Actual PM2.5 (μg/m³)")
    ax2.set_ylabel("Predicted PM2.5 (μg/m³)")
    ax2.grid(True, linestyle=':', alpha=0.6)
    ax2.legend(loc='upper left')

    ax3 = fig.add_subplot(2, 2, 3)
    residuals = actual_3h - pred_3h
    ax3.hist(residuals, bins=40, color='#9467bd', edgecolor='black', alpha=0.75)
    ax3.axvline(0, color='red', linestyle='--', linewidth=2, label='Zero Bias Center')
    ax3.set_title(f"C. Residual Error Distribution (Mean Bias: {np.mean(residuals):.2f})", fontweight='bold')
    ax3.set_xlabel("Prediction Error (Actual - Pred μg/m³)")
    ax3.set_ylabel("Frequency count")
    ax3.grid(True, linestyle=':', alpha=0.6)
    ax3.legend(loc='upper right')

    ax4 = fig.add_subplot(2, 2, 4)
    horizons_labels = ['Next 3h', 'Next 6h', 'Next 9h', 'Next 12h']
    rmse_by_h = [np.sqrt(mean_squared_error(y_test_real[:, h], y_pred_real[:, h])) for h in range(4)]
    bars = ax4.bar(horizons_labels, rmse_by_h, color=['#1f77b4', '#aec7e8', '#ff7f0e', '#ffbb78'], width=0.55, edgecolor='black')
    ax4.set_title("D. RMSE Error Growth Across Time Horizons", fontweight='bold')
    ax4.set_ylabel("RMSE Error (μg/m³)")
    ax4.grid(True, axis='y', linestyle=':', alpha=0.6)
    
    for bar in bars:
        yval = bar.get_height()
        ax4.text(bar.get_x() + bar.get_width()/2.0, yval + 0.1, f"{yval:.2f}", ha='center', va='bottom', fontweight='bold')

    plt.tight_layout(rect=[0, 0.03, 1, 0.94])
    
    # =========================================================================
    # 📁 SMART SNAPSHOT ENGINE (บันทึกรูปลงโฟลเดอร์ pictures แยกตามสถาปัตยกรรม)
    # =========================================================================
    pictures_dir = os.path.join(save_dir, "pictures")
    os.makedirs(pictures_dir, exist_ok=True)

    first_snapshot_path = os.path.join(pictures_dir, f"{model_basename}_eval_FIRST.png")
    latest_snapshot_path = os.path.join(pictures_dir, f"{model_basename}_eval_LATEST.png")

    # ถ้ายังไม่มีรูป FIRST แสดงว่าเป็นเทสครั้งแรกของโมเดลนี้! ให้เซฟเก็บไว้เป็นเกณฑ์อ้างอิงทันที
    if not os.path.exists(first_snapshot_path):
        plt.savefig(first_snapshot_path, dpi=300)
        print(f"{Colors.BOLD}{Colors.YELLOW}🌟 [NEW MODEL BASELINE] บันทึกภาพผลทดสอบครั้งแรกสุดไว้ที่:\n   -> {first_snapshot_path}{Colors.RESET}")

    # บันทึกภาพปัจจุบันลงไฟล์ LATEST เสมอเพื่อรอเอาไปเปิดวางข้างๆ เทียบกับใบ FIRST
    plt.savefig(latest_snapshot_path, dpi=300)
    print(f"{Colors.GREEN}✅ บันทึกผลทดสอบเวอร์ชั่นล่าสุดเรียบร้อยที่:\n   -> {latest_snapshot_path}{Colors.RESET}\n")
    
    plt.show()

if __name__ == "__main__":
    EvaluateModelPerformance()