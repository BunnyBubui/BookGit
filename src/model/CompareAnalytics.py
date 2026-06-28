import os
import glob
import pandas as pd
import matplotlib.pyplot as plt
from config.Config import folder_path, target_locations, save_dir, Colors

def GenerateMasterComparisonChart():
    print(f"{Colors.BOLD}{Colors.CYAN}================================================================={Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.CYAN} 📊 MASTER COMPARATIVE ANALYTICS (ระบบสร้างกราฟเปรียบเทียบทุกห้อง){Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.CYAN}=================================================================\n{Colors.RESET}")

    all_files = glob.glob(os.path.join(folder_path, "*.csv"))
    if not all_files:
        print(f"{Colors.RED}❌ ไม่พบข้อมูลไฟล์ CSV ใน: {folder_path}{Colors.RESET}"); return

    room_dfs = {}
    
    for loc in target_locations:
        matched_files = [f for f in all_files if loc in os.path.basename(f)]
        if not matched_files: continue
        
        df_list = []
        for file in matched_files:
            try:
                temp = pd.read_csv(file, on_bad_lines='skip')
                temp['datetime'] = pd.to_datetime(temp['datetime'], format='%d-%m-%Y-%H-%M-%S', errors='coerce')
                df_list.append(temp.dropna(subset=['datetime']))
            except: pass
            
        if df_list:
            combined = pd.concat(df_list).sort_values('datetime').set_index('datetime')
            room_dfs[loc.upper()] = combined[['PM2_5', 'temperature', 'humidity']].resample('1h').mean().interpolate(limit=3)

    if not room_dfs: return

    print(f"{Colors.CYAN}⏳ กำลังวาดกราฟเปรียบเทียบมิติข้อมูล...{Colors.RESET}")

    fig, axes = plt.subplots(3, 1, figsize=(14, 10), sharex=True)
    fig.suptitle('Master Sensor Analytics Comparison Across All Rooms', fontsize=16, fontweight='bold', y=0.96)

    colors_map = {'KNBD': '#1f77b4', 'SUPAT': '#ff7f0e'} 
    variables = [
        ('PM2_5', 'PM2.5 Concentration (μg/m³)', axes[0]),
        ('temperature', 'Temperature (°C)', axes[1]),
        ('humidity', 'Relative Humidity (%)', axes[2])
    ]

    for col_name, ylabel, ax in variables:
        for room_key, df in room_dfs.items():
            if col_name in df.columns:
                ax.plot(df.index, df[col_name], label=f"Room: {room_key}", color=colors_map.get(room_key), linewidth=1.8, alpha=0.85)
        
        ax.set_ylabel(ylabel, fontsize=11, fontweight='bold')
        ax.grid(True, linestyle='--', alpha=0.5)
        ax.legend(loc='upper right', frameon=True)

    axes[2].set_xlabel('Timeline (Date-Time)', fontsize=12, fontweight='bold')
    plt.tight_layout(rect=[0, 0.03, 1, 0.94])

    # ✅ ย้ายมาเซฟลงใน src/model/file/pictures เหมือนกัน
    pictures_dir = os.path.join(save_dir, "pictures")
    os.makedirs(pictures_dir, exist_ok=True)
    output_img = os.path.join(pictures_dir, "master_rooms_comparison_chart.png")
    
    plt.savefig(output_img, dpi=300)
    print(f"{Colors.GREEN}✅ บันทึกไฟล์กราฟเปรียบเทียบเรียบร้อยที่:\n   -> {output_img}{Colors.RESET}\n")
    plt.show()

if __name__ == "__main__":
    GenerateMasterComparisonChart()