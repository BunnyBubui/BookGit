import os
import glob
import pandas as pd
from config.Config import folder_path, Colors

# ==============================================================================
# 🎯 TARGET FILENAME PREFIXES (กำหนดชื่อไฟล์เริ่มต้นที่ต้องการคลีนตรงนี้)
# ==============================================================================
TARGET_PREFIXES = [
    "merge_PM_Original"
]

def DeduplicateAndSortData():
    os.system('cls' if os.name == 'nt' else 'clear')
    print(f"{Colors.BOLD}{Colors.CYAN}================================================================={Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.CYAN} 🧹 MASTER DATA DEDUPLICATOR & CHRONOLOGICAL SORTER{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.CYAN}    Targets: {TARGET_PREFIXES}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.CYAN}=================================================================\n{Colors.RESET}")

    all_files = glob.glob(os.path.join(folder_path, "*.csv"))
    if not all_files:
        print(f"{Colors.RED}❌ ไม่พบไฟล์ CSV ในโฟลเดอร์: {folder_path}{Colors.RESET}")
        return

    total_files_processed = 0
    total_dups_removed = 0

    for file in all_files:
        filename = os.path.basename(file)
        
        # กรองเฉพาะไฟล์ที่ขึ้นต้นด้วยชื่อใน Array TARGET_PREFIXES
        if not any(filename.startswith(prefix) for prefix in TARGET_PREFIXES):
            continue

        print(f"{Colors.CYAN}⏳ กำลังคลีนไฟล์: {Colors.YELLOW}{filename}{Colors.RESET}")
        
        try:
            # 1. อ่านไฟล์ดิบ
            df = pd.read_csv(file, on_bad_lines='skip')
            raw_rows = len(df)

            if 'datetime' not in df.columns:
                print(f"   {Colors.RED}-> ข้าม: ไม่พบคอลัมน์ 'datetime'{Colors.RESET}\n")
                continue

            # 2. ลบคอลัมน์ชื่อซ้ำกันทิ้ง (Remove duplicate columns)
            df = df.loc[:, ~df.columns.duplicated()]

            # 3. แปลงเวลาเพื่อใช้เรียงลำดับ (ยึดฟอร์แมตมาตรฐานโปรเจกต์ %d-%m-%Y-%H-%M-%S)
            df['dt_temp'] = pd.to_datetime(df['datetime'], format='%d-%m-%Y-%H-%M-%S', errors='coerce')
            
            # ตัดบรรทัดที่วันที่พังออก และเรียงจากอดีต -> ปัจจุบัน
            df = df.dropna(subset=['dt_temp']).sort_values('dt_temp')

            # 4. ลบแถวที่เวลา 'datetime' ซ้ำกันเป๊ะๆ (เก็บตัวแรกที่เซนเซอร์อ่านเจอไว้)
            dups_count = df.duplicated(subset=['datetime']).sum()
            df_cleaned = df.drop_duplicates(subset=['datetime'], keep='first').copy()

            # 5. ลบคอลัมน์ชั่วคราวทิ้งก่อนบันทึกกลับ
            df_cleaned.drop(columns=['dt_temp'], inplace=True)
            clean_rows = len(df_cleaned)

            # บันทึกทับไฟล์เดิมด้วยข้อมูลที่เรียงเวลาและคลีนซ้ำแล้ว
            df_cleaned.to_csv(file, index=False)

            total_files_processed += 1
            total_dups_removed += dups_count

            if dups_count > 0:
                print(f"   {Colors.GREEN}-> ✅ คลีนสำเร็จ: ลบแถวซ้ำไป {dups_count:,} แถว (เหลือ {clean_rows:,} แถว เรียงเวลาถูกต้อง){Colors.RESET}\n")
            else:
                print(f"   {Colors.GREEN}-> 🟢 สะอาดอยู่แล้ว (เรียงเวลา {clean_rows:,} แถว สมบูรณ์){Colors.RESET}\n")

        except Exception as e:
            print(f"   {Colors.RED}-> ❌ พัง: เกิดข้อผิดพลาด ({e}){Colors.RESET}\n")

    print(f"{Colors.BOLD}{Colors.CYAN}================================================================={Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.GREEN} 🎉 สรุปผลการคลีนข้อมูลเสร็จสิ้น!{Colors.RESET}")
    print(f"    • จำนวนไฟล์ที่คลีน: {total_files_processed:,} ไฟล์")
    print(f"    • สังหารแถวซ้ำรวม:   {total_dups_removed:,} แถว")
    print(f"{Colors.CYAN}=================================================================\n{Colors.RESET}")

if __name__ == "__main__":
    DeduplicateAndSortData()