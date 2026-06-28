import os
import glob
import pandas as pd
import numpy as np
import datetime
import re
from config.Config import folder_path, target_locations, save_dir, Colors

def clean_ansi(text):
    """ฟังก์ชันล้างโค้ดสี ANSI ออกจากข้อความก่อนบันทึกลงไฟล์ .log"""
    ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
    return ansi_escape.sub('', text)

def DiagnoseDataHealth():
    os.makedirs(save_dir, exist_ok=True)
    log_file_path = os.path.join(save_dir, "data_health_diagnostic.log")
    
    # ตัวเก็บสะสมข้อความเพื่อรอเขียนลงไฟล์ทีเดียว
    log_lines = []
    
    def emit(msg=""):
        """พิมพ์ออกหน้าจอพร้อมสะสมข้อความลง Log"""
        print(msg)
        log_lines.append(clean_ansi(msg))

    now_str = datetime.datetime.now().strftime('%d/%m/%Y %H:%M:%S')
    emit(f"{Colors.BOLD}{Colors.CYAN}================================================================={Colors.RESET}")
    emit(f"{Colors.BOLD}{Colors.CYAN} 🩺 DATA HEALTH DIAGNOSTIC SYSTEM (ระบบตรวจสุขภาพไฟล์ข้อมูล){Colors.RESET}")
    emit(f"{Colors.BOLD}{Colors.CYAN}    Diagnostic Date: {now_str}{Colors.RESET}")
    emit(f"{Colors.BOLD}{Colors.CYAN}=================================================================\n{Colors.RESET}")

    all_files = glob.glob(os.path.join(folder_path, "*.csv"))
    if not all_files:
        emit(f"{Colors.RED}❌ ไม่พบไฟล์ CSV ในโฟลเดอร์: {folder_path}{Colors.RESET}")
        with open(log_file_path, mode='w', encoding='utf-8') as f:
            f.write('\n'.join(log_lines))
        return

    GAP_THRESHOLD_MINUTES = 15.0 

    for file in all_files:
        filename = os.path.basename(file)
        if target_locations and not any(loc in filename for loc in target_locations): 
            continue

        emit(f"{Colors.BOLD}📄 ตรวจสอบไฟล์: {Colors.YELLOW}{filename}{Colors.RESET}")
        try:
            df = pd.read_csv(file, on_bad_lines='skip')
            if 'datetime' not in df.columns:
                emit(f"   {Colors.RED}❌ พัง: ไม่พบคอลัมน์ 'datetime'{Colors.RESET}\n")
                continue

            # 1. แปลงเวลาและเรียงลำดับจากอดีต -> ปัจจุบัน
            df['dt'] = pd.to_datetime(df['datetime'], format='%d-%m-%Y-%H-%M-%S', errors='coerce')
            df = df.dropna(subset=['dt']).sort_values('dt').reset_index(drop=True)

            if len(df) == 0:
                emit(f"   {Colors.RED}❌ พัง: ข้อมูลวันที่ใช้งานไม่ได้เลย{Colors.RESET}\n")
                continue

            total_rows = len(df)
            start_time = df['dt'].iloc[0].strftime('%d/%m/%Y %H:%M')
            end_time = df['dt'].iloc[-1].strftime('%d/%m/%Y %H:%M')

            # 2. คำนวณหาระยะห่างของเวลาระหว่างบรรทัด (Time Delta)
            time_diffs = df['dt'].diff().dt.total_seconds() / 60.0

            gaps = time_diffs[time_diffs > GAP_THRESHOLD_MINUTES]
            total_gaps = len(gaps)
            max_gap_duration = gaps.max() if total_gaps > 0 else 0

            emit(f"   📅 ช่วงเวลา: {start_time}  ถึง  {end_time} (รวม {total_rows:,} แถว)")

            # 3. ตัดเกรดประเมินผลเสียต่อโมเดล AI
            if total_gaps == 0:
                status = f"{Colors.GREEN}🟢 สุขภาพดีเยี่ยม (Healthy) - เวลาต่อเนื่องสมบูรณ์ 100%{Colors.RESET}"
                impact = "ไม่มีผลเสีย: โมเดลจะเรียนรู้มิติเวลาได้อย่างแม่นยำที่สุด"
            elif total_gaps <= 5 and max_gap_duration <= 60:
                status = f"{Colors.YELLOW}🟡 พอใช้ (Moderate Gaps) - พบจุดขาดช่วง {total_gaps} ครั้ง (นานสุด {max_gap_duration:.0f} นาที){Colors.RESET}"
                impact = "ผลเสียปานกลาง: Linear Interpolation ยังพอเดาค่าเติมให้ได้"
            else:
                status = f"{Colors.RED}🔴 อันตราย (Severely Broken) - พบจุดขาดช่วงถึง {total_gaps} ครั้ง! (แอบหลับนานสุด {max_gap_duration/60:.1f} ชั่วโมง){Colors.RESET}"
                impact = f"{Colors.RED}ผลเสียร้ายแรง: เสี่ยงเกิด Time-jump ผิดพลาด ส่งผลให้พยากรณ์อนาคตแกว่งและมั่ว{Colors.RESET}"

            emit(f"   🩺 ผลการตรวจ: {status}")
            emit(f"   ⚠️ คำแนะนำ:   {impact}")

            # โชว์ตัวอย่างจุดที่ขาดช่วงที่นานที่สุด 3 อันดับแรก
            if total_gaps > 0:
                emit(f"   🔍 ตัวอย่างจุดที่ข้อมูลขาดช่วงนานที่สุด:")
                top_gaps_idx = gaps.nlargest(3).index
                for idx in top_gaps_idx:
                    t_before = df['dt'].iloc[idx-1].strftime('%d/%m %H:%M')
                    t_after = df['dt'].iloc[idx].strftime('%d/%m %H:%M')
                    duration = time_diffs.iloc[idx]
                    emit(f"      - ดับไปตอน [{t_before}] แล้ววาร์ปมาติดอีกที [{t_after}] ({Colors.RED}หายไป {duration:.0f} นาที{Colors.RESET})")

        except Exception as e:
            emit(f"   {Colors.RED}❌ อ่านไฟล์ไม่ได้: {e}{Colors.RESET}")
        
        emit("-" * 65)

    # 4. ทำการบันทึก Log ทั้งหมดลงไดรฟ์
    with open(log_file_path, mode='w', encoding='utf-8') as f:
        f.write('\n'.join(log_lines))
    
    print(f"\n{Colors.BOLD}{Colors.GREEN}✅ บันทึกรายงานผลการตรวจทั้งหมดลงไฟล์เรียบร้อยแล้วที่:{Colors.RESET}")
    print(f"   -> {Colors.CYAN}{log_file_path}{Colors.RESET}\n")

if __name__ == "__main__":
    DiagnoseDataHealth()