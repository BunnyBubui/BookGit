import os, threading, io, json, time, re, tempfile
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("TkAgg")
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import matplotlib.ticker as mticker
import matplotlib.colors as mcolors
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
from datetime import datetime, time as dtime

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

import tkinter as tk
from tkinter import filedialog, messagebox, ttk

try:
    import customtkinter as ctk
except ImportError:
    print("pip install customtkinter"); exit(1)

try:
    import firebase_admin
    from firebase_admin import credentials as fb_creds, db as fb_db
    HAS_FIREBASE = True
except ImportError:
    HAS_FIREBASE = False

try:
    from google.oauth2.credentials import Credentials
    from google.auth.transport.requests import Request
    from google_auth_oauthlib.flow import InstalledAppFlow
    from googleapiclient.discovery import build as gdrive_build
    HAS_GDRIVE = True
except ImportError:
    HAS_GDRIVE = False

# ══════════════════════════════════════════════════════════════════════
#  FONTS & SIZES
# ══════════════════════════════════════════════════════════════════════
FONT      = "Tahoma"
FONT_MONO = "Consolas"
REF_DATE  = pd.Timestamp("2000-01-01")

FS_TITLE  = 16
FS_LABEL  = 14
FS_BODY   = 13
FS_SMALL  = 12
FS_TINY   = 11
FS_MONO   = 11

STANDARD_COLORS = [
    "#2196F3","#F44336","#FF9800",
    "#E91E63","#4CAF50","#9C27B0","#795548",
]

# ══════════════════════════════════════════════════════════════════════
#  THEMES
# ══════════════════════════════════════════════════════════════════════
THEMES = {
    "light": {
        "sidebar_bg": "#FFFFFF", "main_bg":   "#F7F7F7",
        "accent":     "#1565C0", "accent2":   "#0D47A1", "accent3": "#082d6e",
        "text":       "#0D1B3E", "text_soft": "#37474F", "text_dim": "#78909C",
        "card_bg":    "#EEF2FA", "input_bg":  "#F5F8FF", "border":  "#C5D3F0",
        "green":      "#2E7D32", "red":       "#C62828", "amber":   "#E65100",
        "orange":     "#BF360C", "purple":    "#6A1B9A", "teal":    "#006064",
        "plot_bg":    "#FFFFFF", "plot_grid": "#E0E7F5", "plot_txt": "#263238",
        "dlg_bg":     "#F5F8FF",
        "exp_bg":     "#FFFFFF", "exp_card":  "#E4EAF6", "exp_log":  "#F5F8FF",
        "white":  "#F5F8FF",
    },
    "dark": {
        "sidebar_bg": "#0F1729", "main_bg":   "#0D1830",
        "accent":     "#4F9CF9", "accent2":   "#2D6FD6", "accent3": "#1A4A8A",
        "text":       "#E2E8F7", "text_soft": "#8B9CC8", "text_dim": "#4A567A",
        "card_bg":    "#162040", "input_bg":  "#1A2545", "border":  "#243058",
        "green":      "#34D399", "red":       "#F87171", "amber":   "#FBBF24",
        "orange":     "#FB923C", "purple":    "#A78BFA", "teal":    "#38BDF8",
        "plot_bg":    "#0D1830", "plot_grid": "#1A2D52", "plot_txt": "#8B9CC8",
        "dlg_bg":     "#0F1729",
        "exp_bg":     "#0A0F1E", "exp_card":  "#111827", "exp_log":  "#0D1525",
    },
}
C = dict(THEMES["light"])

# ══════════════════════════════════════════════════════════════════════
#  PLOT CONFIG
# ══════════════════════════════════════════════════════════════════════
PLOT_OPTIONS = {
    "PM2.5 + PC0.1 + Temp&Hum":                 {"r1":["pm25"],        "r2":["pc01"],        "temp":True},
    "PM0.1 + PC0.1 + Temp&Hum":                 {"r1":["pm01"],        "r2":["pc01"],        "temp":True},
    "PM2.5 + PC2.5 + Temp&Hum":                 {"r1":["pm25"],        "r2":["pc25"],        "temp":True},
    "PM0.1 + PC2.5 + Temp&Hum":                 {"r1":["pm01"],        "r2":["pc25"],        "temp":True},
    "PM0.1 + PM2.5 + Temp&Hum":                 {"r1":["pm01","pm25"], "r2":[],              "temp":True},
    "PC0.1 + PC2.5 + Temp&Hum":                 {"r1":[],              "r2":["pc01","pc25"], "temp":True},
    "PM2.5 + PC0.1 (ไม่มี Temp)":               {"r1":["pm25"],        "r2":["pc01"],        "temp":False},
    "PM0.1 + PC0.1 (ไม่มี Temp)":               {"r1":["pm01"],        "r2":["pc01"],        "temp":False},
    "PM2.5 + PC2.5 (ไม่มี Temp)":               {"r1":["pm25"],        "r2":["pc25"],        "temp":False},
    "PM0.1 + PC2.5 (ไม่มี Temp)":               {"r1":["pm01"],        "r2":["pc25"],        "temp":False},
    "PM0.1 + PM2.5 (ไม่มี Temp)":               {"r1":["pm01","pm25"], "r2":[],              "temp":False},
    "PC0.1 + PC2.5 (ไม่มี Temp)":               {"r1":[],              "r2":["pc01","pc25"], "temp":False},
    "PM2.5 + Temp&Hum":                          {"r1":["pm25"],        "r2":[],              "temp":True},
    "PM0.1 + Temp&Hum":                          {"r1":["pm01"],        "r2":[],              "temp":True},
    "PC0.1 + Temp&Hum":                          {"r1":[],              "r2":["pc01"],        "temp":True},
    "PC2.5 + Temp&Hum":                          {"r1":[],              "r2":["pc25"],        "temp":True},
    "PM2.5 เท่านั้น":                            {"r1":["pm25"],        "r2":[],              "temp":False},
    "PM0.1 เท่านั้น":                            {"r1":["pm01"],        "r2":[],              "temp":False},
    "PC0.1 เท่านั้น":                            {"r1":[],              "r2":["pc01"],        "temp":False},
    "PC2.5 เท่านั้น":                            {"r1":[],              "r2":["pc25"],        "temp":False},
    "Temp & Humidity เท่านั้น":                  {"r1":[],              "r2":[],              "temp":True},
    "ทุกอย่าง (PM0.1+PM2.5+PC0.1+PC2.5+Temp)": {"r1":["pm01","pm25"], "r2":["pc01","pc25"], "temp":True},
}

TIME_RANGE_OPTIONS = {
    "ทั้งวัน (00:00–24:00)":      (0,24),
    "ครึ่งวันแรก (00:00–12:00)":  (0,12),
    "ครึ่งวันหลัง (12:00–24:00)": (12,24),
    "ช่วงเช้า (06:00–12:00)":     (6,12),
    "ช่วงบ่าย (12:00–18:00)":     (12,18),
    "ช่วงเย็น-ค่ำ (18:00–24:00)": (18,24),
    "กลางคืน (00:00–06:00)":      (0,6),
    "กำหนดเอง...":                 None,
}

RESAMPLE_OPTIONS = ["1min","5min","10min","30min","1h"]

COL_KEYS = {
    "pm25":["pm2.5","pm25","pm2_5"],
    "pm01":["pm0.1","pm01","pm0_1","pm1"],
    "pc01":["pc01","pc0.1","pc0_1","particlecount01","count01","pc1"],
    "pc25":["pc25","pc2.5","pc2_5","particlecount25","count25"],
    "temp":["temp","temperature","t(°c)","t(c)"],
    "hum": ["hum","humidity","moisture","moi","rh"],
}

AXIS_LABELS = {"pm25":"PM2.5 (μg/m³)","pm01":"PM0.1 (μg/m³)",
               "pc01":"PC0.1 (pcs/L)","pc25":"PC2.5 (pcs/L)"}
AXIS_TITLES = {"pm25":"PM 2.5 Concentration (μg/m³)",
               "pm01":"PM 0.1 Concentration (μg/m³)",
               "pc01":"Particle Count 0.1 μm (pcs/L)",
               "pc25":"Particle Count 2.5 μm (pcs/L)"}

# ══════════════════════════════════════════════════════════════════════
#  HELPERS (Analytics & UI)
# ══════════════════════════════════════════════════════════════════════
def find_col(columns, *keywords):
    for kw in keywords:
        kw_c = kw.lower().replace(".","").replace("_","").replace(" ","")
        for c in columns:
            if kw_c in c.lower().replace(".","").replace("_","").replace(" ",""):
                return c
    return None

def find_key_col(columns, key):
    return find_col(columns, *COL_KEYS.get(key,[key]))

_THAI_MONTHS = ["", "ม.ค.", "ก.พ.", "มี.ค.", "เม.ย.", "พ.ค.", "มิ.ย.",
                "ก.ค.", "ส.ค.", "ก.ย.", "ต.ค.", "พ.ย.", "ธ.ค."]

def _thai_date_str(d):
    try:
        import datetime as _dt
        if isinstance(d, str):
            d = _dt.date.fromisoformat(d)
        return f"{d.day:02d} {_THAI_MONTHS[d.month]} {d.year + 543}"
    except Exception:
        return str(d)

def detect_outliers(series):
    q1, q3 = series.quantile(0.25), series.quantile(0.75)
    iqr = q3 - q1
    return int(((series < q1-1.5*iqr)|(series > q3+1.5*iqr)).sum())

def calc_completeness(df_indexed, h0, h1):
    total_secs = (h1 - h0) * 3600
    if total_secs <= 0: return 0.0, 0
    unique_secs = int(df_indexed.index.floor("s").nunique())
    return min(unique_secs / total_secs * 100.0, 100.0), unique_secs

def fb_rows_to_df(data):
    if not data: return pd.DataFrame()
    rows = [{"datetime": ts, **vals} for ts,vals in data.items()
            if isinstance(vals, dict)]
    return pd.DataFrame(rows)

def _apply_xaxis(ax, total_span_days: float):
    span_h = total_span_days * 24

    if total_span_days > 7:
        ax.xaxis.set_major_locator(mdates.DayLocator(interval=1))
        ax.xaxis.set_major_formatter(mdates.DateFormatter("%d/%m"))
        ax.xaxis.set_minor_locator(mdates.HourLocator(interval=12))
        rot = 30
    elif total_span_days > 2:
        ax.xaxis.set_major_locator(mdates.HourLocator(interval=12))
        ax.xaxis.set_major_formatter(mdates.DateFormatter("%d/%m\n%H:%M"))
        ax.xaxis.set_minor_locator(mdates.HourLocator(interval=6))
        rot = 0
    elif total_span_days > 1:
        ax.xaxis.set_major_locator(mdates.HourLocator(interval=6))
        ax.xaxis.set_major_formatter(mdates.DateFormatter("%d/%m\n%H:%M"))
        ax.xaxis.set_minor_locator(mdates.HourLocator(interval=3))
        rot = 0
    elif span_h > 12:
        ax.xaxis.set_major_locator(mdates.HourLocator(interval=2))
        ax.xaxis.set_major_formatter(mdates.DateFormatter("%H:%M"))
        ax.xaxis.set_minor_locator(mdates.MinuteLocator(byminute=[30]))
        rot = 0
    elif span_h > 6:
        ax.xaxis.set_major_locator(mdates.HourLocator(interval=1))
        ax.xaxis.set_major_formatter(mdates.DateFormatter("%H:%M"))
        ax.xaxis.set_minor_locator(mdates.MinuteLocator(byminute=[30]))
        rot = 0
    elif span_h > 2:
        ax.xaxis.set_major_locator(mdates.MinuteLocator(byminute=[0, 30]))
        ax.xaxis.set_major_formatter(mdates.DateFormatter("%H:%M"))
        ax.xaxis.set_minor_locator(mdates.MinuteLocator(interval=10))
        rot = 0
    else:
        ax.xaxis.set_major_locator(mdates.MinuteLocator(interval=10))
        ax.xaxis.set_major_formatter(mdates.DateFormatter("%H:%M"))
        ax.xaxis.set_minor_locator(mdates.MinuteLocator(interval=5))
        rot = 0

    ax.tick_params(axis="x", which="major", colors=C["plot_txt"],
                   labelsize=10, rotation=rot)
    ax.tick_params(axis="x", which="minor",
                   length=3, width=0.6, color=C["plot_grid"])

# ══════════════════════════════════════════════════════════════════════
#  ROBUST HTTP REQUESTS (STABILITY FIX + OFFLINE QUEUE)
# ══════════════════════════════════════════════════════════════════════
def get_stable_session():
    """สร้าง requests.Session พร้อมระบบ Retry อัตโนมัติป้องกันเน็ตหลุด/Server ชะงัก"""
    session = requests.Session()
    retry = Retry(total=4, backoff_factor=1, status_forcelist=[500, 502, 503, 504])
    adapter = HTTPAdapter(max_retries=retry)
    session.mount('http://', adapter)
    session.mount('https://', adapter)
    return session

_STABLE_SESSION = get_stable_session()

def upload_with_pending(df, filename, web_app_url, pending_dir):
    """ส่งข้อมูลขึ้น Drive ถ้าเน็ตหลุด/ไม่สำเร็จ ให้นำเข้า Queue เพื่อรอรอบถัดไป"""
    if not web_app_url:
        return False, "ยังไม่ได้ตั้งค่า Web App URL"
    try:
        csv_data = df.to_csv(index=False, encoding="utf-8-sig")
        resp = _STABLE_SESSION.post(web_app_url, params={"filename": filename}, data=json.dumps(csv_data), timeout=15)
        if "Success" not in resp.text:
            raise RuntimeError(f"App Script Error: {resp.text[:100]}")
        return True, "อัปโหลดสำเร็จ"
    except requests.exceptions.RequestException as e:
        os.makedirs(pending_dir, exist_ok=True)
        pfile = os.path.join(pending_dir, f"{int(time.time()*1000)}_{filename}")
        df.to_csv(pfile, index=False, encoding="utf-8-sig")
        return False, "รออินเทอร์เน็ต (นำเข้าคิวแล้ว)"
    except Exception as e:
        os.makedirs(pending_dir, exist_ok=True)
        pfile = os.path.join(pending_dir, f"{int(time.time()*1000)}_{filename}")
        df.to_csv(pfile, index=False, encoding="utf-8-sig")
        return False, f"ผิดพลาด {str(e)[:30]} (นำเข้าคิวแล้ว)"

def flush_pending_uploads(app_url, pending_dir, log_fn):
    """ตรวจสอบไฟล์ค้างและพยายามอัปโหลดซ้ำ (Resume Offline Queue)"""
    if not os.path.isdir(pending_dir): return
    pendings = [f for f in os.listdir(pending_dir) if f.endswith(".csv")]
    if pendings:
        log_fn(f"🔄 พบไฟล์ค้างอัปโหลดรอบก่อน {len(pendings)} รายการ กำลังพยายามส่งใหม่...")
        success_count = 0
        for pf in pendings:
            try:
                p_path = os.path.join(pending_dir, pf)
                p_df = pd.read_csv(p_path)
                fname = pf.split("_", 1)[1] if "_" in pf else pf
                
                csv_data = p_df.to_csv(index=False, encoding="utf-8-sig")
                resp = _STABLE_SESSION.post(app_url, params={"filename": fname}, data=json.dumps(csv_data), timeout=10)
                if "Success" in resp.text:
                    os.remove(p_path)
                    log_fn(f"  ☁ ดันข้อมูลค้างสำเร็จ: {fname}")
                    success_count += 1
                else:
                    log_fn(f"  ❌ ดันข้อมูลค้างพลาด (AppScript Error): {fname}")
            except Exception as pe:
                log_fn(f"  ⚠️ อินเทอร์เน็ตยังไม่เสถียร หยุดดันคิวชั่วคราว...")
                break # หากเชื่อมไม่ได้เลย ให้หยุดทำทันทีเพื่อไม่ให้ระบบค้าง
        if success_count > 0:
            log_fn(f"✅ ดันคิวสำเร็จ {success_count} รายการ")

# ══════════════════════════════════════════════════════════════════════
#  GOOGLE DRIVE
# ══════════════════════════════════════════════════════════════════════
DRIVE_SCOPES = ["https://www.googleapis.com/auth/drive.readonly"]

class DriveManager:
    def __init__(self, client_file, token_file, pm_folder, dht_folder, extra_folders=None):
        self.client_file=client_file; self.token_file=token_file
        self.pm_folder=pm_folder;     self.dht_folder=dht_folder
        self.extra_folders = extra_folders or []
        self._creds=None; self._svc=None

    def _auth(self):
        if self._creds and self._creds.valid: return
        if os.path.exists(self.token_file):
            self._creds = Credentials.from_authorized_user_file(self.token_file, DRIVE_SCOPES)
        if not self._creds or not self._creds.valid:
            if self._creds and self._creds.expired and self._creds.refresh_token:
                self._creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(self.client_file, DRIVE_SCOPES)
                self._creds = flow.run_local_server(port=0)
            with open(self.token_file,"w") as f: f.write(self._creds.to_json())
        self._svc = gdrive_build("drive","v3",credentials=self._creds)

    def list_folder(self, folder_id, query=""):
        self._auth()
        q = f"'{folder_id}' in parents and trashed=false and (mimeType='text/csv' or mimeType='text/comma-separated-values')"
        if query: q += f" and name contains '{query}'"
        res = self._svc.files().list(
            q=q, orderBy="modifiedTime desc",
            fields="files(id,name,modifiedTime,size)", pageSize=200,
            supportsAllDrives=True, includeItemsFromAllDrives=True).execute()
        return res.get("files",[])

    def list_all(self, query=""):
        results = []
        if self.pm_folder:
            for f in self.list_folder(self.pm_folder, query):
                results.append(dict(f, _folder="PM"))
        if self.dht_folder:
            for f in self.list_folder(self.dht_folder, query):
                results.append(dict(f, _folder="DHT"))
        for ef in self.extra_folders:
            fid  = ef.get("id","").strip()
            name = ef.get("name","") or fid[:10]
            if not fid: continue
            for f in self.list_folder(fid, query):
                results.append(dict(f, _folder=name))
        seen = set(); deduped = []
        for f in results:
            if f["id"] not in seen:
                seen.add(f["id"]); deduped.append(f)
        return {"pm": [], "dht": [], "_all": deduped}

    def download(self, file_id):
        self._auth()
        data = self._svc.files().get_media(fileId=file_id, supportsAllDrives=True).execute()
        return io.BytesIO(data)

# ══════════════════════════════════════════════════════════════════════
#  FIREBASE
# ══════════════════════════════════════════════════════════════════════
class FirebaseManager:
    def __init__(self, key_file, db_url):
        self.key_file=key_file; self.db_url=db_url; self._init=False

    def _ensure(self):
        if not HAS_FIREBASE: raise RuntimeError("pip install firebase-admin")
        if not self._init:
            if not firebase_admin._apps:
                firebase_admin.initialize_app(
                    fb_creds.Certificate(self.key_file), {"databaseURL": self.db_url})
            self._init = True

    def load(self, path):
        self._ensure(); return fb_db.reference(path).get() or {}

    def load_shallow(self, path):
        self._ensure()
        data = fb_db.reference(path).get(shallow=True)
        return list(data.keys()) if data else []

    def delete(self, path, on_progress=None):
        self._ensure()
        ref  = fb_db.reference(path)
        data = ref.get(shallow=True)
        if not data: return 0
        keys = list(data.keys())
        for i in range(0, len(keys), 500):
            ref.update({k: None for k in keys[i:i+500]})
            if on_progress:
                on_progress(min(100, int((i+500)/len(keys)*100)))
        return len(keys)

    def load_as_df(self, path):
        data = self.load(path)
        if not data: return pd.DataFrame()
        rows = [{"datetime":ts,**vals} for ts,vals in data.items() if isinstance(vals,dict)]
        df = pd.DataFrame(rows)
        if not df.empty and "datetime" in df.columns:
            df["Datetime"] = pd.to_datetime(df["datetime"],
                format="%d-%m-%Y-%H-%M-%S", errors="coerce")
        return df

    def list_all_paths(self, base):
        self._ensure()
        paths = []
        for sensor in ["DustSensor", "DHT22"]:
            try:
                rooms = fb_db.reference(f"{base}/{sensor}").get(shallow=True) or {}
                for room in rooms:
                    pts = fb_db.reference(f"{base}/{sensor}/{room}").get(shallow=True) or {}
                    for pt in pts:
                        paths.append(f"{base}/{sensor}/{room}/{pt}")
            except: pass
        return sorted(paths)

# ══════════════════════════════════════════════════════════════════════
#  EXPORT via App Script
# ══════════════════════════════════════════════════════════════════════
def export_room_point(room, point, cfg, do_drive, do_delete, log_fn):
    fb_mgr   = cfg["_fb_mgr"]
    base     = cfg.get("fb_base_path", "SAC")
    data_dir = cfg.get("export_dir", "")
    os.makedirs(data_dir, exist_ok=True)
    
    pending_dir = os.path.join(data_dir, ".pending_drive")
    if do_drive: os.makedirs(pending_dir, exist_ok=True)

    dht_path  = f"{base}/DHT22/{room}/{point}"
    dust_path = f"{base}/DustSensor/{room}/{point}"

    log_fn(f"  ▸ DHT22  : {dht_path}")
    dht_raw  = fb_mgr.load(dht_path)
    log_fn(f"  ▸ Dust   : {dust_path}")
    dust_raw = fb_mgr.load(dust_path)

    df_dht  = fb_rows_to_df(dht_raw)
    df_dust = fb_rows_to_df(dust_raw)

    if df_dht.empty and df_dust.empty:
        log_fn(f"  💤 ไม่มีข้อมูลใน {room}/{point}")
        return []

    for df in (df_dht, df_dust):
        if not df.empty:
            df["dt"]   = pd.to_datetime(df["datetime"],
                format="%d-%m-%Y-%H-%M-%S", errors="coerce")
            df["date"] = df["dt"].dt.strftime("%d-%m-%Y")

    if not df_dht.empty and not df_dust.empty:
        df_merge = pd.merge(df_dht, df_dust, on=["datetime","dt","date"], how="outer")
    else:
        df_merge = df_dht if not df_dht.empty else df_dust

    df_merge = df_merge.sort_values("dt")

    results = []; all_ok = True
    for date_str, df_day in df_merge.groupby("date"):
        df_export = df_day.drop(columns=["dt","date"], errors="ignore")
        filename  = f"{room}_{point}_{date_str}.csv"
        fpath     = os.path.join(data_dir, filename)
        result    = {"filename":filename,"rows":len(df_export),
                     "drive":False,"status":"ok","msg":""}
        try:
            if os.path.isfile(fpath):
                df_exist = pd.read_csv(fpath, dtype=str)
                new_data = df_export[~df_export["datetime"].isin(df_exist["datetime"])]
                if new_data.empty:
                    result["msg"] = "ข้อมูลซ้ำ ข้าม"; result["rows"] = 0
                else:
                    new_cols = [c for c in new_data.columns if c not in df_exist.columns]
                    if new_cols:
                        combined = pd.concat([df_exist, new_data], ignore_index=True, sort=False)
                        combined['_dt'] = pd.to_datetime(combined['datetime'], format="%d-%m-%Y-%H-%M-%S", errors='coerce')
                        combined = combined.sort_values('_dt').drop(columns=['_dt'])
                        combined.to_csv(fpath, mode="w", index=False, header=True, encoding="utf-8-sig")
                        result["msg"] = f"Local อัปเดต +{len(new_data)} แถว"
                    else:
                        combined = pd.concat([df_exist, new_data], ignore_index=True, sort=False)
                        combined['_dt'] = pd.to_datetime(combined['datetime'], format="%d-%m-%Y-%H-%M-%S", errors='coerce')
                        combined = combined.sort_values('_dt').drop(columns=['_dt'])
                        combined.to_csv(fpath, mode="w", index=False, header=True, encoding="utf-8-sig")
                        result["msg"] = f"Local ต่อท้าย +{len(new_data)} แถว"
                    
                    if do_drive:
                        succ, msg = upload_with_pending(new_data, filename, cfg.get("web_app_url",""), pending_dir)
                        if succ:
                            result["drive"] = True
                            result["msg"] += " (Drive สำเร็จ ☁)"
                        else:
                            result["msg"] += f" [{msg}]"
            else:
                df_export.to_csv(fpath, mode="w", index=False, header=True, encoding="utf-8-sig")
                result["msg"] = f"Local สร้างใหม่ {len(df_export)} แถว"
                if do_drive:
                    succ, msg = upload_with_pending(df_export, filename, cfg.get("web_app_url",""), pending_dir)
                    if succ:
                        result["drive"] = True
                        result["msg"] += " (Drive สำเร็จ ☁)"
                    else:
                        result["msg"] += f" [{msg}]"
            
            log_fn(f"  💾 {filename}  —  {result['msg']}")
        except Exception as e:
            result["status"] = "error"; result["msg"] = str(e)
            all_ok = False
            log_fn(f"  ❌ {filename}: {e}")
        results.append(result)

    if all_ok and do_delete:
        if not df_dht.empty:
            n = fb_mgr.delete(dht_path)
            log_fn(f"  🗑  ลบ DHT22 {n} รายการ")
        if not df_dust.empty:
            n = fb_mgr.delete(dust_path)
            log_fn(f"  🗑  ลบ Dust {n} รายการ")
    elif not all_ok and do_delete:
        log_fn(f"  ⚠️  มีข้อผิดพลาด — ระงับการลบ Firebase")

    return results

# ══════════════════════════════════════════════════════════════════════
#  CONFIG
# ══════════════════════════════════════════════════════════════════════
def load_cfg():
    d = dict(CFG_DEFAULTS)
    if os.path.exists(CFG_FILE):
        try:
            with open(CFG_FILE) as f: d.update(json.load(f))
        except: pass
    return d

def save_cfg(cfg):
    to_save = {k:v for k,v in cfg.items() if not k.startswith("_")}
    with open(CFG_FILE,"w") as f: json.dump(to_save,f,indent=2,ensure_ascii=False)

CFG_FILE = os.path.join(os.path.expanduser("~"), ".dust_monitor_pro.json")

CFG_DEFAULTS = {
    "local_dir":"", "dt_col":"", "dt_fmt":"",
    "station_name":"", "kw1":"","nm1":"","kw2":"","nm2":"",
    "kw3":"","nm3":"","kw4":"","nm4":"","kw5":"","nm5":"",
    "pm_folder_id":"", "dht_folder_id":"", "oauth_client":"", "oauth_token":"",
    "fb_key":"", "fb_url":"",
    "drive_folders": "[]",
    "fb_base_path":"SAC",
    "fb_rooms":"c3_supat,c3_knbd",
    "fb_points":"Point01",
    "web_app_url":"",
    "export_dir":os.path.join(os.path.expanduser("~"), "C3_Export"),
    "auto_drive":True,
    "auto_delete":False,
}

# ══════════════════════════════════════════════════════════════════════
#  SETTINGS DIALOG
# ══════════════════════════════════════════════════════════════════════
class SettingsDialog(ctk.CTkToplevel):
    def __init__(self, parent, on_save_cb=None):
        super().__init__(parent)
        self.title("⚙  Settings — Dust Monitor Pro v4")
        self.geometry("780x860"); self.resizable(True,True)
        self._vars={}; self._cfg=load_cfg(); self._on_save_cb=on_save_cb
        self._build()

    def _build(self):
        hdr = ctk.CTkFrame(self, fg_color=C["accent"], height=52, corner_radius=0)
        hdr.pack(fill="x"); hdr.pack_propagate(False)
        ctk.CTkLabel(hdr, text="⚙  Dust Monitor Pro v4 — Configuration",
                     font=ctk.CTkFont(family=FONT, size=FS_LABEL, weight="bold"),
                     text_color="white").pack(side="left", padx=18, pady=12)

        row = ctk.CTkFrame(self, fg_color=C["card_bg"], corner_radius=0)
        row.pack(fill="x")
        ctk.CTkLabel(row, text="  Import / Export JSON",
                     font=ctk.CTkFont(family=FONT, size=FS_SMALL, weight="bold"),
                     text_color=C["teal"]).pack(side="left", padx=12, pady=10)
        ctk.CTkButton(row, text="💾 Export", width=120, height=38,
                      fg_color=C["accent"], hover_color=C["accent2"],
                      font=ctk.CTkFont(family=FONT, size=FS_SMALL),
                      command=self._export).pack(side="right", padx=6, pady=8)
        ctk.CTkButton(row, text="📂 Import", width=120, height=38,
                      fg_color=C["teal"], hover_color="#006064", text_color="white",
                      font=ctk.CTkFont(family=FONT, size=FS_SMALL),
                      command=self._import).pack(side="right", padx=4, pady=8)

        tab = ctk.CTkTabview(self, fg_color=C["dlg_bg"],
                             segmented_button_fg_color=C["card_bg"],
                             segmented_button_selected_color=C["accent"],
                             segmented_button_selected_hover_color=C["accent2"],
                             segmented_button_unselected_color=C["card_bg"],
                             text_color=C["text"])
        tab.pack(fill="both", expand=True, padx=14, pady=6)
        for nm in ["☁ Drive","🔥 Firebase","📤 Export","📁 Local","🖥 Display"]:
            tab.add(nm)
        self._tab_drive(tab.tab("☁ Drive"))
        self._tab_firebase(tab.tab("🔥 Firebase"))
        self._tab_export(tab.tab("📤 Export"))
        self._tab_local(tab.tab("📁 Local"))
        self._tab_display(tab.tab("🖥 Display"))

        bf = ctk.CTkFrame(self, fg_color=C["card_bg"], corner_radius=0, height=62)
        bf.pack(fill="x", side="bottom"); bf.pack_propagate(False)
        ctk.CTkButton(bf, text="💾  บันทึก", height=42, width=150,
                      fg_color=C["accent"], hover_color=C["accent2"],
                      font=ctk.CTkFont(family=FONT, size=FS_LABEL, weight="bold"),
                      command=self._save).pack(side="left", padx=14, pady=10)
        ctk.CTkButton(bf, text="✕  ปิด", height=42, width=120,
                      fg_color=C["text_soft"], hover_color="#37474F", text_color="white",
                      font=ctk.CTkFont(family=FONT, size=FS_LABEL),
                      command=self.destroy).pack(side="left", padx=6, pady=10)

    def _field(self, parent, label, key, desc="", browse=None):
        f = ctk.CTkFrame(parent, fg_color=C["input_bg"], corner_radius=6)
        f.pack(fill="x", pady=4, padx=4)
        ctk.CTkLabel(f, text=label,
                     font=ctk.CTkFont(family=FONT, size=FS_BODY, weight="bold"),
                     text_color=C["text"]).pack(anchor="w", padx=12, pady=(8,0))
        if desc:
            ctk.CTkLabel(f, text=desc,
                         font=ctk.CTkFont(family=FONT, size=FS_SMALL),
                         text_color=C["text_dim"], wraplength=600, justify="left"
                         ).pack(anchor="w", padx=12, pady=(0,4))
        row = ctk.CTkFrame(f, fg_color="transparent")
        row.pack(fill="x", padx=12, pady=(0,10))
        var = ctk.StringVar(value=self._cfg.get(key,""))
        self._vars[key] = var
        ctk.CTkEntry(row, textvariable=var, height=40,
                     font=ctk.CTkFont(family=FONT_MONO, size=FS_BODY),
                     fg_color=C["main_bg"], text_color=C["text"],
                     border_color=C["border"]).pack(side="left", fill="x", expand=True)
        if browse=="json":
            ctk.CTkButton(row, text="📂", width=44, height=40,
                          fg_color=C["accent2"],
                          command=lambda v=var: v.set(
                              filedialog.askopenfilename(
                                  filetypes=[("JSON","*.json")]) or v.get())
                          ).pack(side="left", padx=(4,0))
        elif browse=="dir":
            ctk.CTkButton(row, text="📁", width=44, height=40,
                          fg_color=C["accent2"],
                          command=lambda v=var: v.set(
                              filedialog.askdirectory() or v.get())
                          ).pack(side="left", padx=(4,0))

    def _tab_drive(self, p):
        p.configure(fg_color=C["dlg_bg"])
        sc = ctk.CTkScrollableFrame(p, fg_color=C["dlg_bg"]); sc.pack(fill="both",expand=True)
        self._field(sc,"OAuth Client JSON","oauth_client",
                    "ไฟล์ credentials.json จาก Google Cloud Console","json")
        self._field(sc,"Token JSON","oauth_token",
                    "ไฟล์ token.json (สร้างอัตโนมัติ)","json")
        ctk.CTkFrame(sc, fg_color=C["border"], height=1, corner_radius=0
                     ).pack(fill="x", padx=8, pady=12)
        hdr_f = ctk.CTkFrame(sc, fg_color="transparent")
        hdr_f.pack(fill="x", padx=8, pady=(0,6))
        ctk.CTkLabel(hdr_f,
            text="📁  Google Drive Folders  (เพิ่มได้ไม่จำกัด)",
            font=ctk.CTkFont(family=FONT, size=FS_SMALL, weight="bold"),
            text_color=C["teal"]).pack(side="left", padx=4)
        ctk.CTkButton(hdr_f, text="＋ เพิ่ม", width=90, height=28,
                      fg_color=C["teal"], hover_color="#005050",
                      font=ctk.CTkFont(family=FONT, size=FS_SMALL),
                      command=lambda: self._drive_add_row(folder_rows_f)
                      ).pack(side="right", padx=4)
        ctk.CTkLabel(sc,
            text="  กำหนดชื่อ + Folder ID เพื่อให้แสดงในหัวตาราง Drive Browser",
            font=ctk.CTkFont(family=FONT, size=FS_SMALL),
            text_color=C["text_dim"], justify="left"
        ).pack(anchor="w", padx=12, pady=(0,8))
        ch = ctk.CTkFrame(sc, fg_color=C["card_bg"], corner_radius=6)
        ch.pack(fill="x", padx=8, pady=(0,2))
        ctk.CTkLabel(ch, text="  ชื่อที่แสดง (เช่น c3_knbd)", width=200,
                     font=ctk.CTkFont(family=FONT, size=FS_SMALL, weight="bold"),
                     text_color=C["text_soft"], anchor="w").pack(side="left", padx=8, pady=4)
        ctk.CTkLabel(ch, text="Folder ID (จาก Google Drive URL)",
                     font=ctk.CTkFont(family=FONT, size=FS_SMALL, weight="bold"),
                     text_color=C["text_soft"], anchor="w").pack(side="left", padx=4, pady=4)
        folder_rows_f = ctk.CTkFrame(sc, fg_color="transparent")
        folder_rows_f.pack(fill="x", padx=8, pady=2)
        self._drive_folder_rows = []
        try:
            existing = json.loads(self._cfg.get("drive_folders","[]") or "[]")
            if not isinstance(existing, list): existing = []
        except: existing = []
        if not existing:
            if self._cfg.get("pm_folder_id"):
                existing.append({"name":"PM Sensor","id":self._cfg["pm_folder_id"]})
            if self._cfg.get("dht_folder_id"):
                existing.append({"name":"DHT22","id":self._cfg["dht_folder_id"]})
        for entry in existing:
            self._drive_add_row(folder_rows_f,
                                entry.get("name",""), entry.get("id",""))
        if not existing:
            self._drive_add_row(folder_rows_f)
        self._vars["drive_folders"] = "_DYNAMIC_"

    def _drive_add_row(self, parent, name="", fid=""):
        row = ctk.CTkFrame(parent, fg_color=C["input_bg"], corner_radius=6)
        row.pack(fill="x", pady=2)
        nv = ctk.StringVar(value=name)
        iv = ctk.StringVar(value=fid)
        ctk.CTkEntry(row, textvariable=nv, width=180, height=34,
                     placeholder_text="ชื่อโฟลเดอร์",
                     font=ctk.CTkFont(family=FONT_MONO, size=FS_SMALL),
                     fg_color=C["main_bg"], text_color=C["text"],
                     border_color=C["border"]
                     ).pack(side="left", padx=(8,4), pady=6)
        ctk.CTkEntry(row, textvariable=iv, height=34,
                     placeholder_text="Folder ID (1BxW...)",
                     font=ctk.CTkFont(family=FONT_MONO, size=FS_SMALL),
                     fg_color=C["main_bg"], text_color=C["text"],
                     border_color=C["border"]
                     ).pack(side="left", fill="x", expand=True, padx=4, pady=6)
        def _rm(r=row, entry=(nv,iv)):
            self._drive_folder_rows = [x for x in self._drive_folder_rows if x[2] is not r]
            r.destroy()
        ctk.CTkButton(row, text="✕", width=32, height=28,
                      fg_color=C["border"], hover_color=C["red"],
                      text_color=C["text_soft"],
                      font=ctk.CTkFont(family=FONT, size=FS_SMALL),
                      command=_rm
                      ).pack(side="right", padx=6, pady=6)
        self._drive_folder_rows.append((nv, iv, row))

    def _tab_firebase(self, p):
        p.configure(fg_color=C["dlg_bg"])
        sc = ctk.CTkScrollableFrame(p, fg_color=C["dlg_bg"]); sc.pack(fill="both",expand=True)
        for lb,k,d,bt in [
            ("Service Account Key","fb_key","serviceAccountKey.json จาก Firebase Console","json"),
            ("Database URL","fb_url","https://your-project-default-rtdb.firebaseio.com",""),
            ("Base Path","fb_base_path","path หลักใน Realtime DB เช่น SAC",""),
            ("Rooms (คั่นด้วย ,)","fb_rooms","เช่น c3_supat,c3_knbd",""),
            ("Points (คั่นด้วย ,)","fb_points","เช่น Point01,Point02",""),
        ]: self._field(sc,lb,k,d,bt)

    def _tab_export(self, p):
        p.configure(fg_color=C["dlg_bg"])
        sc = ctk.CTkScrollableFrame(p, fg_color=C["dlg_bg"]); sc.pack(fill="both",expand=True)
        ctk.CTkLabel(sc,
            text="  📤  Export Manager — Google Drive via App Script",
            font=ctk.CTkFont(family=FONT, size=FS_SMALL, weight="bold"),
            text_color=C["teal"]).pack(anchor="w", padx=8, pady=(10,4))
        for lb,k,d,bt in [
            ("App Script URL","web_app_url",
             "URL ของ Google Apps Script Web App ที่ใช้รับ CSV แล้วบันทึกลง Drive",""),
            ("โฟลเดอร์บันทึกในเครื่อง","export_dir",
             "โฟลเดอร์สำหรับบันทึกไฟล์ CSVในเครื่อง","dir"),
        ]: self._field(sc,lb,k,d,bt)
        ctk.CTkLabel(sc, text="  ตัวเลือก Default:",
                     font=ctk.CTkFont(family=FONT, size=FS_SMALL, weight="bold"),
                     text_color=C["text_soft"]).pack(anchor="w", padx=8, pady=(10,4))
        for txt,key,col in [
            ("☁  อัปโหลด Google Drive เป็น Default","auto_drive",C["teal"]),
            ("🗑  ลบ Firebase หลังดึง เป็น Default","auto_delete",C["red"]),
        ]:
            bvar = ctk.BooleanVar(value=bool(self._cfg.get(key,False)))
            self._vars[key] = bvar
            ctk.CTkCheckBox(sc, text=txt, variable=bvar,
                            fg_color=col, hover_color=col,
                            text_color=C["text"],
                            font=ctk.CTkFont(family=FONT, size=FS_BODY)
                            ).pack(anchor="w", padx=16, pady=4)

    def _tab_local(self, p):
        p.configure(fg_color=C["dlg_bg"])
        sc = ctk.CTkScrollableFrame(p, fg_color=C["dlg_bg"]); sc.pack(fill="both",expand=True)
        for lb,k,d,bt in [
            ("โฟลเดอร์หลัก","local_dir","โฟลเดอร์เริ่มต้นเมื่อเปิด file dialog","dir"),
            ("DateTime Column","dt_col","ชื่อคอลัมน์ datetime เช่น Time, Datetime",""),
            ("DateTime Format","dt_fmt","เช่น %d-%m-%Y-%H-%M-%S  หรือ %Y-%m-%d %H:%M:%S",""),
        ]: self._field(sc,lb,k,d,bt)

    def _tab_display(self, p):
        p.configure(fg_color=C["dlg_bg"])
        sc = ctk.CTkScrollableFrame(p, fg_color=C["dlg_bg"]); sc.pack(fill="both",expand=True)
        self._field(sc,"ชื่อสถานี","station_name",
                    "ชื่อสถานีที่แสดงในกราฟ (ใช้เมื่อไม่มี keyword ตรง)")
        ctk.CTkLabel(sc,
            text="  🏷  Keyword → ชื่อที่แสดงในกราฟ  (สูงสุด 5 คู่)",
            font=ctk.CTkFont(family=FONT, size=FS_SMALL, weight="bold"),
            text_color=C["teal"]).pack(anchor="w", padx=8, pady=(14,4))
        ctk.CTkLabel(sc,
            text="  ตรวจสอบ Keyword ทุกคู่ตามลำดับ ถ้าชื่อไฟล์มี keyword → ใช้ชื่อที่กำหนด",
            font=ctk.CTkFont(family=FONT, size=FS_SMALL),
            text_color=C["text_dim"], wraplength=620, justify="left"
        ).pack(anchor="w", padx=12, pady=(0,6))
        for i in range(1,6):
            rf = ctk.CTkFrame(sc, fg_color=C["input_bg"], corner_radius=6)
            rf.pack(fill="x", padx=4, pady=3)
            ctk.CTkLabel(rf, text=f"  #{i}",
                         font=ctk.CTkFont(family=FONT, size=FS_SMALL, weight="bold"),
                         text_color=C["accent"], width=28
                         ).pack(side="left", padx=(8,0), pady=10)
            ctk.CTkLabel(rf, text="Keyword:",
                         font=ctk.CTkFont(family=FONT, size=FS_SMALL),
                         text_color=C["text_soft"]
                         ).pack(side="left", padx=(6,2), pady=10)
            kv = ctk.StringVar(value=self._cfg.get(f"kw{i}",""))
            self._vars[f"kw{i}"] = kv
            ctk.CTkEntry(rf, textvariable=kv, width=120, height=36,
                         placeholder_text=f"sensor{i}",
                         font=ctk.CTkFont(family=FONT_MONO, size=FS_SMALL),
                         fg_color=C["main_bg"], text_color=C["text"],
                         border_color=C["border"]
                         ).pack(side="left", padx=(0,8), pady=10)
            ctk.CTkLabel(rf, text="→  ชื่อที่แสดง:",
                         font=ctk.CTkFont(family=FONT, size=FS_SMALL),
                         text_color=C["text_soft"]
                         ).pack(side="left", padx=(0,2), pady=10)
            nv = ctk.StringVar(value=self._cfg.get(f"nm{i}",""))
            self._vars[f"nm{i}"] = nv
            ctk.CTkEntry(rf, textvariable=nv, height=36,
                         placeholder_text=f"Station {i}",
                         font=ctk.CTkFont(family=FONT_MONO, size=FS_SMALL),
                         fg_color=C["main_bg"], text_color=C["text"],
                         border_color=C["border"]
                         ).pack(side="left", fill="x", expand=True, padx=(0,12), pady=10)

    def _import(self):
        p = filedialog.askopenfilename(parent=self, filetypes=[("JSON","*.json")])
        if not p: return
        try:
            with open(p) as f: data = json.load(f)
            for k,v in self._vars.items():
                if k in data: v.set(data[k])
            messagebox.showinfo("Import","นำเข้าสำเร็จ", parent=self)
        except Exception as e: messagebox.showerror("Error",str(e),parent=self)

    def _export(self):
        p = filedialog.asksaveasfilename(parent=self, defaultextension=".json",
                                         filetypes=[("JSON","*.json")])
        if not p: return
        try:
            with open(p,"w") as f:
                json.dump({k: (v.get() if hasattr(v,"get") else v.get())
                           for k,v in self._vars.items()}, f, indent=2)
            messagebox.showinfo("Export","ส่งออกสำเร็จ", parent=self)
        except Exception as e: messagebox.showerror("Error",str(e),parent=self)

    def _save(self):
        d = {}
        for k,v in self._vars.items():
            if k == "drive_folders": continue
            raw = v.get()
            d[k] = bool(raw) if isinstance(v, ctk.BooleanVar) else str(raw).strip()
        if hasattr(self, "_drive_folder_rows"):
            folders = []
            for nv, iv, _row in self._drive_folder_rows:
                name = nv.get().strip(); fid = iv.get().strip()
                if fid:
                    folders.append({"name": name, "id": fid})
            d["drive_folders"] = json.dumps(folders, ensure_ascii=False)
        save_cfg(d)
        if self._on_save_cb: self._on_save_cb()
        messagebox.showinfo("บันทึก","บันทึกการตั้งค่าเรียบร้อย", parent=self)


# ══════════════════════════════════════════════════════════════════════
#  FIREBASE BROWSER DIALOG
# ══════════════════════════════════════════════════════════════════════
class FirebaseBrowserDialog(ctk.CTkToplevel):
    def __init__(self, parent, fb_mgr, base_path="SAC"):
        super().__init__(parent)
        self.title("🔥 Firebase Browser — ดู / ลบ Path")
        self.geometry("680x600"); self.configure(fg_color=C["main_bg"])
        self._fb   = fb_mgr
        self._base = base_path
        self._all  = []
        self._build()
        threading.Thread(target=self._load_paths, daemon=True).start()

    def _build(self):
        hdr = ctk.CTkFrame(self, fg_color="#7C2D12", height=50, corner_radius=0)
        hdr.pack(fill="x"); hdr.pack_propagate(False)
        ctk.CTkLabel(hdr, text="🔥  Firebase Browser",
                     font=ctk.CTkFont(family=FONT, size=FS_LABEL, weight="bold"),
                     text_color="white").pack(side="left", padx=16)
        sf = ctk.CTkFrame(self, fg_color=C["card_bg"], corner_radius=0)
        sf.pack(fill="x")
        ctk.CTkLabel(sf, text="🔍",
                     font=ctk.CTkFont(size=14), text_color=C["text_soft"]
                     ).pack(side="left", padx=8)
        self._sq = ctk.StringVar()
        self._sq.trace_add("write", self._filter)
        ctk.CTkEntry(sf, textvariable=self._sq, height=36,
                     placeholder_text="ค้นหา path...",
                     font=ctk.CTkFont(family=FONT_MONO, size=FS_SMALL),
                     fg_color=C["input_bg"], text_color=C["text"],
                     border_color=C["border"]
                     ).pack(side="left", fill="x", expand=True, padx=(0,8), pady=8)
        lf = ctk.CTkFrame(self, fg_color=C["card_bg"], corner_radius=8)
        lf.pack(fill="both", expand=True, padx=10, pady=4)
        sb = ttk.Scrollbar(lf); sb.pack(side="right", fill="y")
        self._lb = tk.Listbox(lf, bg=C["input_bg"], fg=C["text"],
                               font=(FONT_MONO, FS_SMALL), relief="flat", bd=0,
                               selectbackground=C["accent"], selectforeground="white",
                               yscrollcommand=sb.set, selectmode=tk.EXTENDED,
                               activestyle="none", highlightthickness=0)
        self._lb.pack(fill="both", expand=True, padx=4, pady=4)
        sb.config(command=self._lb.yview)
        self._status = ctk.CTkLabel(self, text="กำลังโหลด...",
                                     font=ctk.CTkFont(family=FONT, size=FS_SMALL),
                                     text_color=C["amber"])
        self._status.pack(pady=(0,2))
        self._prog = ctk.CTkProgressBar(self, mode="determinate", height=6)
        self._prog.pack(fill="x", padx=10, pady=2); self._prog.set(0)
        bf = ctk.CTkFrame(self, fg_color=C["card_bg"], corner_radius=0, height=62)
        bf.pack(fill="x", side="bottom"); bf.pack_propagate(False)
        for txt,cmd,col,hov in [
            ("🔄 รีเฟรช",            self._refresh,         C["accent2"],   C["accent"]),
            ("☑ เลือกทั้งหมด",       lambda: self._lb.select_set(0,tk.END),
                                                              C["card_bg"],   C["border"]),
            ("🗑 ลบ Path ที่เลือก",   self._delete_selected, C["red"],       "#B71C1C"),
        ]:
            ctk.CTkButton(bf, text=txt, height=40, fg_color=col,
                          hover_color=hov,
                          text_color="white" if col!=C["card_bg"] else C["accent"],
                          font=ctk.CTkFont(family=FONT, size=FS_SMALL),
                          command=cmd).pack(side="left", padx=6, pady=10)
        ctk.CTkButton(bf, text="✕ ปิด", height=40, fg_color=C["text_soft"],
                      hover_color="#37474F", text_color="white",
                      font=ctk.CTkFont(family=FONT, size=FS_SMALL),
                      command=self.destroy).pack(side="right", padx=10, pady=10)

    def _load_paths(self):
        try:
            paths = self._fb.list_all_paths(self._base)
            self._all = paths
            self.after(0, self._populate, paths)
            self.after(0, lambda: self._status.configure(text=f"พบ {len(paths)} path", text_color=C["green"]))
        except Exception as e:
            self.after(0, lambda: self._status.configure(text=str(e)[:80], text_color=C["red"]))

    def _populate(self, paths):
        self._lb.delete(0, tk.END)
        for p in paths: self._lb.insert(tk.END, f"  {p}")

    def _filter(self, *_):
        q = self._sq.get().lower()
        self._populate([p for p in self._all if q in p.lower()])

    def _refresh(self):
        self._status.configure(text="กำลังโหลดใหม่...", text_color=C["amber"])
        self._prog.set(0)
        threading.Thread(target=self._load_paths, daemon=True).start()

    def _delete_selected(self):
        sel = self._lb.curselection()
        if not sel:
            messagebox.showwarning("เลือก Path","กรุณาเลือก path ก่อน",parent=self); return
        paths = [self._lb.get(i).strip() for i in sel]
        if not messagebox.askyesno("ยืนยันการลบ",
            f"ลบ {len(paths)} path ?\n\n" +
            "\n".join(f"  • {p}" for p in paths[:6]) +
            (f"\n  ... และอีก {len(paths)-6}" if len(paths)>6 else ""),
            parent=self): return
        self._status.configure(text="กำลังลบ...", text_color=C["amber"])
        threading.Thread(target=self._bg_delete, args=(paths,), daemon=True).start()

    def _bg_delete(self, paths):
        for i,path in enumerate(paths):
            try: self._fb.delete(path)
            except: pass
            self.after(0, self._prog.set, (i+1)/len(paths))
        
        def _done():
            self._status.configure(text=f"✅ ลบเสร็จ {len(paths)} path", text_color=C["green"])
            self._refresh()
            
        self.after(0, _done)


# ══════════════════════════════════════════════════════════════════════
#  MAIN APPLICATION
# ══════════════════════════════════════════════════════════════════════
class DustMonitorApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.bind("<F5>", self._dev_reload)
        ctk.set_appearance_mode("Light")
        ctk.set_default_color_theme("blue")
        self.title("Dust Monitor Pro — v4  |  Plot + Export + Summary")
        self.geometry("1700x980"); self.minsize(960,540)

        self._theme_name   = "light"
        self._cfg          = load_cfg()
        self._drive_mgr    = None
        self._fb_mgr       = None
        self.files_data    = []
        self._sheet_files  = []  
        self._current_fig  = None
        self._settings_win = None
        self._browser_win  = None
        self._is_plotting  = False
        self._is_exporting = False

        self._color_map = {}
        self._color_idx = 0

        self._plot_type  = ctk.StringVar(value=list(PLOT_OPTIONS.keys())[0])
        self._time_range = ctk.StringVar(value=list(TIME_RANGE_OPTIONS.keys())[0])
        self._resample   = ctk.StringVar(value="1min")
        self._show_hist  = ctk.BooleanVar(value=False)
        self._show_heat  = ctk.BooleanVar(value=False)
        self._show_gap   = ctk.BooleanVar(value=False)
        self._smooth     = ctk.BooleanVar(value=True)
        self._fill_area  = ctk.BooleanVar(value=True)

        self._exp_room_vars  = {}
        self._exp_point_vars = {}
        self._exp_do_drive   = ctk.BooleanVar(value=self._cfg.get("auto_drive", True))
        self._exp_do_delete  = ctk.BooleanVar(value=self._cfg.get("auto_delete", False))
        self._exp_ok = 0; self._exp_err = 0; self._exp_drive = 0

        self._scroll_velocity  = 0.0
        self._scroll_animating = False

        self._init_integrations()
        self._build_ui()

    def _get_color_for_label(self, raw_name):
        base_name = re.sub(r'_[0-9]{2}-[0-9]{2}-[0-9]{4}.*', '', raw_name)
        base_name = re.sub(r'_[0-9]{10,}.*', '', base_name)
        display_label = self._resolve_label(base_name)

        if display_label not in self._color_map:
            self._color_map[display_label] = STANDARD_COLORS[self._color_idx % len(STANDARD_COLORS)]
            self._color_idx += 1
            
        return display_label, self._color_map[display_label]

    def _dev_reload(self, event=None):
        print("🔄 Reloading UI...")
        current_tab = self._tabs.get()
        for widget in self.winfo_children():
            if isinstance(widget, ctk.CTkToplevel): continue
            widget.destroy()
        self._build_ui()
        try: self._tabs.set(current_tab)
        except: pass
        print("✅ UI Reloaded!")

    def _init_integrations(self):
        cfg = self._cfg
        if HAS_GDRIVE and cfg.get("oauth_client"):
            try:
                extra = json.loads(cfg.get("drive_folders","[]") or "[]")
                if not isinstance(extra, list): extra = []
            except: extra = []
            if cfg.get("pm_folder_id") or cfg.get("dht_folder_id") or extra:
                try:
                    self._drive_mgr = DriveManager(
                        cfg.get("oauth_client",""),
                        cfg.get("oauth_token", os.path.join(
                            os.path.dirname(cfg.get("oauth_client","")), "token.json")),
                        cfg.get("pm_folder_id",""), cfg.get("dht_folder_id",""),
                        extra_folders=extra)
                except: pass
        if HAS_FIREBASE and cfg.get("fb_key") and cfg.get("fb_url"):
            try:
                self._fb_mgr = FirebaseManager(cfg.get("fb_key",""), cfg.get("fb_url",""))
            except: pass

    def _build_ui(self):
        self.configure(fg_color=C["main_bg"])
        top = ctk.CTkFrame(self, height=52, corner_radius=0, fg_color=C["sidebar_bg"])
        top.pack(fill="x"); top.pack_propagate(False)
        ctk.CTkLabel(top, text="◉  Dust Monitor Pro",
                     font=ctk.CTkFont(family=FONT, size=FS_TITLE, weight="bold"),
                     text_color=C["accent"]).pack(side="left", padx=18)
        ctk.CTkLabel(top, text="v4  ·  Plot + Export",
                     font=ctk.CTkFont(family=FONT, size=FS_SMALL),
                     text_color=C["text_dim"]).pack(side="left")
        for txt,cmd,col in [
            ("⚙ Settings",     self._open_settings,  C["text_soft"]),
            ("☁ Drive",        lambda: self._open_drive(mode="plot"), C["teal"]),
            ("🔥 FB Browser",  self._open_browser,    C["orange"]),
            ("◑ Theme",        self._switch_theme,    C["purple"]),
        ]:
            ctk.CTkButton(top, text=txt, width=120, height=34,
                          fg_color="transparent", hover_color=C["card_bg"],
                          text_color=col,
                          font=ctk.CTkFont(family=FONT, size=FS_SMALL, weight="bold"),
                          command=cmd).pack(side="right", padx=3, pady=9)
        self._status_lbl = ctk.CTkLabel(top, text="● IDLE",
                                         font=ctk.CTkFont(family=FONT, size=FS_SMALL),
                                         text_color=C["text_dim"])
        self._status_lbl.pack(side="right", padx=8)

        self._tabs = ctk.CTkTabview(
            self, fg_color=C["main_bg"],
            segmented_button_fg_color=C["sidebar_bg"],
            segmented_button_selected_color=C["accent"],
            segmented_button_selected_hover_color=C["accent2"],
            segmented_button_unselected_color=C["sidebar_bg"],
            segmented_button_unselected_hover_color=C["card_bg"],
            corner_radius=12)
        self._tabs.pack(fill="both", expand=True)
        self._tabs.add("วิเคราะห์ & กราฟ")
        self._tabs.add("Export Manager")
        self._tabs.add("สรุปสถิติรายวัน (Sheets)")
        self._tabs.add("รวมไฟล์ CSV (Merge)")
        
        self._build_plot_tab(self._tabs.tab("วิเคราะห์ & กราฟ"))
        self._build_export_tab(self._tabs.tab("Export Manager"))
        self._build_sheets_tab(self._tabs.tab("สรุปสถิติรายวัน (Sheets)"))
        self._build_merge_tab(self._tabs.tab("รวมไฟล์ CSV (Merge)"))

    def _build_plot_tab(self, tab):
        tab.configure(fg_color=C["main_bg"])
        body = ctk.CTkFrame(tab, corner_radius=12, fg_color=C["main_bg"])
        body.pack(fill="both", expand=True)
        self._sidebar = ctk.CTkScrollableFrame(body, width=310, corner_radius=12,
                                                fg_color=C["sidebar_bg"])
        self._sidebar.pack(side="left", fill="y")
        self._build_sidebar()
        main = ctk.CTkFrame(body, corner_radius=0, fg_color=C["main_bg"])
        main.pack(side="left", fill="both", expand=True, padx=8, pady=8)
        scroll_outer = ctk.CTkFrame(main, fg_color=C["main_bg"], corner_radius=8)
        scroll_outer.pack(fill="both", expand=True)
        self._chart_vscroll = ttk.Scrollbar(scroll_outer, orient="vertical")
        self._chart_vscroll.pack(side="right", fill="y")
        self._scroll_canvas = tk.Canvas(scroll_outer, bg=C["main_bg"],
                                         highlightthickness=0,
                                         yscrollcommand=self._chart_vscroll.set)
        self._scroll_canvas.pack(side="left", fill="both", expand=True)
        self._chart_vscroll.config(command=self._scroll_canvas.yview)
        self._chart_frame  = tk.Frame(self._scroll_canvas, bg=C["main_bg"])
        self._chart_window = self._scroll_canvas.create_window(
            (0,0), window=self._chart_frame, anchor="nw")

        def _on_canvas_configure(ev):
            self._scroll_canvas.itemconfig(self._chart_window, width=ev.width)
        def _on_frame_configure(ev):
            self._scroll_canvas.configure(
                scrollregion=self._scroll_canvas.bbox("all"))
        self._scroll_canvas.bind("<Configure>", _on_canvas_configure)
        self._chart_frame.bind("<Configure>",   _on_frame_configure)

        def _on_mousewheel(event):
            if event.num == 4:   delta = -3
            elif event.num == 5: delta =  3
            else:
                raw = event.delta
                if abs(raw) > 500:       delta = raw / -60.0
                elif abs(raw) >= 120:    delta = int(-1*(raw/120))*4
                else:                    delta = -raw / 10.0
            self._scroll_velocity = max(-25, min(25, self._scroll_velocity + delta))
            if not self._scroll_animating:
                self._scroll_animating = True
                _do_scroll()

        def _do_scroll():
            if abs(self._scroll_velocity) < 0.2:
                self._scroll_velocity  = 0.0
                self._scroll_animating = False
                return
            self._scroll_canvas.yview_scroll(int(round(self._scroll_velocity)), "units")
            self._scroll_velocity *= 0.82
            self.after(14, _do_scroll)

        self._scroll_canvas.bind_all("<MouseWheel>", _on_mousewheel)
        self._scroll_canvas.bind_all("<Button-4>",   _on_mousewheel)
        self._scroll_canvas.bind_all("<Button-5>",   _on_mousewheel)
        self._show_placeholder()

    def _build_sidebar(self):
        sb = self._sidebar

        def sec(t, col=None):
            col = col or C["accent"]
            f = ctk.CTkFrame(sb, fg_color="transparent"); f.pack(fill="x",padx=6,pady=(14,3))
            ctk.CTkFrame(f, fg_color=col, width=4, height=16, corner_radius=2).pack(side="left")
            ctk.CTkLabel(f, text=f"  {t}",
                         font=ctk.CTkFont(family=FONT, size=FS_SMALL, weight="bold"),
                         text_color=col).pack(side="left")

        def sep():
            ctk.CTkFrame(sb, fg_color=C["border"], height=1, corner_radius=0
                         ).pack(fill="x", padx=10, pady=6)

        def lbl(t, col=None):
            ctk.CTkLabel(sb, text=t,
                         font=ctk.CTkFont(family=FONT, size=FS_SMALL),
                         text_color=col or C["text_soft"]
                         ).pack(anchor="w", padx=14, pady=(4,2))

        hdr = ctk.CTkFrame(sb, fg_color=C["card_bg"], corner_radius=8)
        hdr.pack(fill="x", padx=8, pady=(10,4))
        ctk.CTkLabel(hdr, text="PM · PC · Temp · Humidity",
                     font=ctk.CTkFont(family=FONT, size=FS_LABEL, weight="bold"),
                     text_color=C["accent"]).pack(pady=(10,2))
        ctk.CTkLabel(hdr, text="Air Quality Dashboard  v4",
                     font=ctk.CTkFont(family=FONT, size=FS_SMALL),
                     text_color=C["text_dim"]).pack(pady=(0,8))
        sep()

        sec("📂 DATA SOURCE")
        for txt,cmd,col,hov,h in [
            ("➕  เพิ่มไฟล์ CSV (เลือกหลายไฟล์ได้)",
             self._add_files, C["accent"],   C["accent2"],  48),
            ("📁  เลือกโฟลเดอร์ (โหลดทุก CSV)",
             self._load_folder,"#546E7A",   "#37474F",      42),
            ("☁  Google Drive (เลือกหลายไฟล์ได้)",
             lambda: self._open_drive(mode="plot"), "#0369A1",   "#01579B",      42),
            ("🔥  Firebase (โหลดเพื่อ Plot)",
             self._open_firebase,"#C2410C", "#9A3412",      42),
        ]:
            ctk.CTkButton(sb, text=txt, command=cmd, fg_color=col,
                          hover_color=hov, text_color="white", height=h,
                          font=ctk.CTkFont(family=FONT,
                                           size=FS_LABEL if h==48 else FS_BODY,
                                           weight="bold" if h==48 else "normal")
                          ).pack(fill="x", padx=12, pady=2)

        lbl("รายการไฟล์ที่โหลด (Ctrl/Shift เลือกหลายรายการ):")
        lf = ctk.CTkFrame(sb, fg_color=C["card_bg"], corner_radius=6)
        lf.pack(fill="x", padx=12, pady=2)
        sc2 = ttk.Scrollbar(lf); sc2.pack(side="right", fill="y")
        self.listbox = tk.Listbox(lf, height=8, bg=C["input_bg"], fg=C["accent"],
                                   borderwidth=0, relief="flat",
                                   font=(FONT, FS_BODY),
                                   selectbackground=C["border"],
                                   activestyle="none", selectmode=tk.EXTENDED,
                                   yscrollcommand=sc2.set)
        self.listbox.pack(fill="x", padx=4, pady=4)
        sc2.config(command=self.listbox.yview)
        bf = ctk.CTkFrame(sb, fg_color="transparent"); bf.pack(fill="x", padx=12, pady=(2,4))
        ctk.CTkButton(bf, text="❌  ลบที่เลือก", fg_color=C["red"], hover_color="#B71C1C",
                      height=36, font=ctk.CTkFont(family=FONT, size=FS_SMALL),
                      command=self._remove_selected
                      ).pack(side="left", fill="x", expand=True, padx=(0,2))
        ctk.CTkButton(bf, text="🗑️  ล้างทั้งหมด", fg_color="#546E7A", hover_color="#37474F",
                      height=36, font=ctk.CTkFont(family=FONT, size=FS_SMALL),
                      command=self._clear_all
                      ).pack(side="left", fill="x", expand=True, padx=(2,0))
        sep()

        sec("📈 PLOT TYPE")
        ctk.CTkOptionMenu(sb, variable=self._plot_type, values=list(PLOT_OPTIONS.keys()),
                          fg_color=C["accent"], button_color=C["accent2"], text_color="white",
                          font=ctk.CTkFont(family=FONT, size=FS_BODY),
                          dynamic_resizing=False, width=285
                          ).pack(pady=4, padx=12, fill="x")
        sep()

        sec("➕ ADDITIONAL PLOTS", col=C["purple"])
        for txt,var,col in [
            ("Histogram (distribution)", self._show_hist, C["purple"]),
            ("Heatmap (hour × 10min)",   self._show_heat, C["teal"]),
            ("Gap / Completeness",       self._show_gap,  C["green"]),
        ]:
            ctk.CTkCheckBox(sb, text=txt, variable=var,
                            checkbox_width=20, checkbox_height=20,
                            fg_color=col, hover_color=col, text_color=C["text"],
                            font=ctk.CTkFont(family=FONT, size=FS_BODY)
                            ).pack(anchor="w", padx=16, pady=3)
        sep()

        sec("⏰ TIME RANGE", col=C["teal"])
        ctk.CTkOptionMenu(sb, variable=self._time_range,
                          values=list(TIME_RANGE_OPTIONS.keys()),
                          fg_color=C["accent"], button_color=C["accent2"],
                          text_color="white",
                          font=ctk.CTkFont(family=FONT, size=FS_BODY),
                          command=self._on_time_change, dynamic_resizing=False
                          ).pack(pady=4, padx=12, fill="x")
        qf = ctk.CTkFrame(sb, fg_color="transparent"); qf.pack(fill="x", padx=12, pady=(0,4))
        for qt,qs in [("ทั้งวัน","ทั้งวัน (00:00–24:00)"),
                       ("เช้า","ช่วงเช้า (06:00–12:00)"),
                       ("บ่าย","ช่วงบ่าย (12:00–18:00)"),
                       ("เย็น","ช่วงเย็น-ค่ำ (18:00–24:00)")]:
            ctk.CTkButton(qf, text=qt, width=68, height=30,
                          fg_color=C["card_bg"], hover_color=C["border"],
                          text_color=C["text_soft"],
                          font=ctk.CTkFont(family=FONT, size=FS_TINY),
                          command=lambda s=qs: (self._time_range.set(s),
                                                self._on_time_change(s))
                          ).pack(side="left", padx=2)
        self._custom_frame = ctk.CTkFrame(sb, fg_color=C["card_bg"], corner_radius=6)
        cf = ctk.CTkFrame(self._custom_frame, fg_color="transparent")
        cf.pack(fill="x", padx=8, pady=6)
        ctk.CTkLabel(cf, text="เริ่ม (ชม):",
                     font=ctk.CTkFont(family=FONT, size=FS_SMALL),
                     text_color=C["text_soft"]).pack(side="left")
        self._custom_start = ctk.CTkEntry(cf, width=64, height=36, placeholder_text="0",
                                           font=ctk.CTkFont(family=FONT, size=FS_BODY))
        self._custom_start.pack(side="left", padx=4)
        ctk.CTkLabel(cf, text="สิ้นสุด:",
                     font=ctk.CTkFont(family=FONT, size=FS_SMALL),
                     text_color=C["text_soft"]).pack(side="left")
        self._custom_end = ctk.CTkEntry(cf, width=64, height=36, placeholder_text="24",
                                         font=ctk.CTkFont(family=FONT, size=FS_BODY))
        self._custom_end.pack(side="left", padx=4)
        sep()

        sec("✨ DISPLAY OPTIONS", col=C["green"])
        for txt,var in [("Smooth / Resample data", self._smooth),
                         ("Fill area under curves",  self._fill_area)]:
            ctk.CTkCheckBox(sb, text=txt, variable=var,
                            checkbox_width=20, checkbox_height=20,
                            fg_color=C["green"], hover_color=C["green"],
                            text_color=C["text"],
                            font=ctk.CTkFont(family=FONT, size=FS_BODY)
                            ).pack(anchor="w", padx=16, pady=3)
        lbl("Resample Interval:")
        ctk.CTkOptionMenu(sb, variable=self._resample, values=RESAMPLE_OPTIONS,
                          fg_color=C["accent"], button_color=C["accent2"],
                          text_color="white",
                          font=ctk.CTkFont(family=FONT, size=FS_BODY)
                          ).pack(fill="x", padx=12, pady=(0,4))
        sep()

        sec("📋 LAST ANALYSIS")
        self._info_box = ctk.CTkTextbox(sb, height=180,
                                         font=ctk.CTkFont(family=FONT_MONO, size=FS_MONO),
                                         fg_color=C["input_bg"], text_color=C["text_soft"])
        self._info_box.pack(fill="x", padx=12, pady=4)
        self._info_box.insert("end", "ยังไม่มีข้อมูล\nกรุณาเพิ่มไฟล์ CSV")
        self._info_box.configure(state="disabled")
        sep()

        self._progress = ctk.CTkProgressBar(sb, mode="determinate", height=10)
        self._progress.pack(fill="x", padx=12, pady=(0,4)); self._progress.set(0)
        self._status_sb = ctk.CTkLabel(sb, text="",
                                        font=ctk.CTkFont(family=FONT, size=FS_SMALL),
                                        text_color=C["text_dim"], wraplength=280)
        self._status_sb.pack(pady=2, padx=10)
        ctk.CTkButton(sb, text="▶  ANALYZE & PLOT",
                      fg_color=C["accent"], hover_color=C["accent2"],
                      font=ctk.CTkFont(family=FONT, size=FS_TITLE, weight="bold"),
                      height=58, command=self._plot_threaded
                      ).pack(fill="x", padx=12, pady=(4,16))

    # ══════════════════════════════════════════════════════════════
    #  TAB 2: EXPORT MANAGER
    # ══════════════════════════════════════════════════════════════
    def _build_export_tab(self, tab):
        tab.configure(fg_color=C["exp_bg"])
        body = ctk.CTkFrame(tab, corner_radius=0, fg_color=C["exp_bg"])
        body.pack(fill="both", expand=True)
        left = ctk.CTkScrollableFrame(body, width=280, corner_radius=0,
                                       fg_color=C["sidebar_bg"])
        left.pack(side="left", fill="y")
        self._build_export_left(left)
        right = ctk.CTkFrame(body, corner_radius=0, fg_color=C["exp_bg"])
        right.pack(side="left", fill="both", expand=True, padx=10, pady=10)
        stats_f = ctk.CTkFrame(right, fg_color="transparent", height=100)
        stats_f.pack(fill="x"); stats_f.pack_propagate(False)
        self._exp_stats_frame = stats_f
        self._build_exp_stats()
        log_card = ctk.CTkFrame(right, fg_color=C["exp_card"], corner_radius=12)
        log_card.pack(fill="both", expand=True, pady=(10,0))
        log_hdr = ctk.CTkFrame(log_card, fg_color="transparent", height=38)
        log_hdr.pack(fill="x", padx=10, pady=(8,0)); log_hdr.pack_propagate(False)
        ctk.CTkLabel(log_hdr, text="📋  Activity Log",
                     font=ctk.CTkFont(family=FONT, size=FS_SMALL, weight="bold"),
                     text_color=C["text_soft"]).pack(side="left")
        ctk.CTkButton(log_hdr, text="🗑  ล้าง Log", width=100, height=28,
                      fg_color=C["border"], hover_color=C["text_dim"],
                      text_color=C["text_soft"],
                      font=ctk.CTkFont(family=FONT, size=FS_TINY),
                      command=self._exp_clear_log
                      ).pack(side="right")
        ctk.CTkFrame(log_card, fg_color=C["border"], height=1, corner_radius=0
                     ).pack(fill="x", padx=10, pady=(6,0))
        self._exp_log = ctk.CTkTextbox(log_card, fg_color=C["exp_log"],
                                        text_color=C["text_soft"],
                                        font=ctk.CTkFont(family=FONT_MONO, size=FS_MONO),
                                        state="disabled", corner_radius=0)
        self._exp_log.pack(fill="both", expand=True, padx=2, pady=2)
        bot = ctk.CTkFrame(right, fg_color="transparent", height=90)
        bot.pack(fill="x", pady=(10,0)); bot.pack_propagate(False)
        self._exp_progress = ctk.CTkProgressBar(bot, mode="determinate", height=6,
                                                 progress_color=C["teal"],
                                                 fg_color=C["border"])
        self._exp_progress.pack(fill="x", pady=(0,8)); self._exp_progress.set(0)
        self._exp_run_btn = ctk.CTkButton(
            bot, text="▶  เริ่มดึงและส่งออกข้อมูล",
            fg_color=C["orange"], hover_color="#bf4800", text_color="white",
            height=52, corner_radius=10,
            font=ctk.CTkFont(family=FONT, size=FS_LABEL, weight="bold"),
            command=self._exp_run)
        self._exp_run_btn.pack(fill="x")

    def _build_export_left(self, panel):
        def sep():
            ctk.CTkFrame(panel, fg_color=C["border"], height=1, corner_radius=0
                         ).pack(fill="x", padx=8, pady=8)
        def sec(t, col=None):
            col = col or C["orange"]
            f = ctk.CTkFrame(panel, fg_color="transparent")
            f.pack(fill="x", padx=6, pady=(10,3))
            ctk.CTkFrame(f, fg_color=col, width=4, height=14, corner_radius=2).pack(side="left")
            ctk.CTkLabel(f, text=f"  {t}",
                         font=ctk.CTkFont(family=FONT, size=FS_SMALL, weight="bold"),
                         text_color=col).pack(side="left")

        hdr = ctk.CTkFrame(panel, fg_color=C["card_bg"], corner_radius=10)
        hdr.pack(fill="x", padx=8, pady=(12,4))
        ctk.CTkFrame(hdr, fg_color=C["orange"], height=3, corner_radius=2
                     ).pack(fill="x", padx=10, pady=(8,0))
        ctk.CTkLabel(hdr, text="Firebase Export Manager",
                     font=ctk.CTkFont(family=FONT, size=13, weight="bold"),
                     text_color=C["orange"]).pack(pady=(6,2))
        ctk.CTkLabel(hdr, text="ดึง · บันทึก · อัปโหลด Drive · ลบ",
                     font=ctk.CTkFont(family=FONT, size=FS_TINY),
                     text_color=C["text_dim"]).pack(pady=(0,10))
        sep()

        sec("📡 ROOMS")
        self._exp_rooms_frame = ctk.CTkFrame(panel, fg_color="transparent")
        self._exp_rooms_frame.pack(fill="x", padx=10)
        self._rebuild_exp_rooms()
        ctk.CTkButton(panel, text="☑  เลือก / ยกเลิกทั้งหมด",
                      height=28, fg_color=C["border"],
                      hover_color=C["text_dim"], text_color=C["text_soft"],
                      font=ctk.CTkFont(family=FONT, size=FS_TINY),
                      command=self._toggle_exp_rooms
                      ).pack(fill="x", padx=10, pady=(2,4))
        sep()

        sec("📌 POINTS")
        self._exp_points_frame = ctk.CTkFrame(panel, fg_color="transparent")
        self._exp_points_frame.pack(fill="x", padx=10)
        self._rebuild_exp_points()
        ctk.CTkButton(panel, text="☑  เลือก / ยกเลิกทั้งหมด",
                      height=28, fg_color=C["border"],
                      hover_color=C["text_dim"], text_color=C["text_soft"],
                      font=ctk.CTkFont(family=FONT, size=FS_TINY),
                      command=self._toggle_exp_points
                      ).pack(fill="x", padx=10, pady=(2,4))
        sep()

        sec("⚙  OPTIONS", col=C["purple"])
        ctk.CTkCheckBox(panel, text="☁  อัปโหลดไป Google Drive",
                        variable=self._exp_do_drive,
                        fg_color=C["teal"], hover_color=C["teal"],
                        text_color=C["text"],
                        font=ctk.CTkFont(family=FONT, size=FS_BODY)
                        ).pack(anchor="w", padx=14, pady=6)
        del_card = ctk.CTkFrame(panel, fg_color=C["card_bg"], corner_radius=8)
        del_card.pack(fill="x", padx=10, pady=(2,4))
        ctk.CTkCheckBox(del_card, text="🗑  ลบ Firebase หลังดึง",
                        variable=self._exp_do_delete,
                        fg_color=C["red"], hover_color=C["red"],
                        text_color=C["text"],
                        font=ctk.CTkFont(family=FONT, size=FS_BODY)
                        ).pack(anchor="w", padx=10, pady=(10,2))
        ctk.CTkLabel(del_card,
            text="⚠  จะลบเฉพาะเมื่อบันทึกสำเร็จ 100%",
            font=ctk.CTkFont(family=FONT, size=9),
            text_color=C["amber"], wraplength=230, justify="left"
        ).pack(anchor="w", padx=14, pady=(0,8))
        sep()

        sec("🔄 SYNC & REPAIR", col=C["teal"])
        ctk.CTkButton(panel, text="☁  Sync & Repair",
                      height=36, fg_color=C["teal"], hover_color="#00695C",
                      font=ctk.CTkFont(family=FONT, size=FS_SMALL, weight="bold"),
                      command=self._open_sync_dialog
                      ).pack(fill="x", padx=10, pady=(2,4))
        ctk.CTkLabel(panel, text="เช็คข้อมูลในเครื่องเทียบกับ Drive\nโหลดเร็ว เลือกซ่อมแซมได้ทันที",
                     font=ctk.CTkFont(family=FONT, size=FS_TINY),
                     text_color=C["text_dim"], justify="left"
                     ).pack(anchor="w", padx=14, pady=(0,6))
        sep()

        sec("📁 บันทึกไฟล์ในเครื่อง", col=C["green"])
        path_card = ctk.CTkFrame(panel, fg_color=C["card_bg"], corner_radius=8)
        path_card.pack(fill="x", padx=10, pady=4)
        self._exp_path_lbl = ctk.CTkLabel(
            path_card,
            text=self._short_path(self._cfg.get("export_dir","")),
            font=ctk.CTkFont(family=FONT_MONO, size=9),
            text_color=C["green"], wraplength=230, justify="left")
        self._exp_path_lbl.pack(anchor="w", padx=10, pady=(8,4))
        ctk.CTkButton(path_card, text="📁  เปลี่ยนโฟลเดอร์",
                      height=32, fg_color=C["green"], hover_color="#1B5E20",
                      font=ctk.CTkFont(family=FONT, size=FS_SMALL),
                      command=self._pick_export_dir
                      ).pack(fill="x", padx=8, pady=(0,8))
        ctk.CTkButton(panel, text="📂  เปิดโฟลเดอร์",
                      height=32, fg_color=C["border"],
                      hover_color=C["text_dim"], text_color=C["text_soft"],
                      font=ctk.CTkFont(family=FONT, size=FS_SMALL),
                      command=self._open_export_dir
                      ).pack(fill="x", padx=10, pady=(0,4))

    def _build_exp_stats(self):
        for w in self._exp_stats_frame.winfo_children(): w.destroy()
        stat_data = [
            ("📦", "ไฟล์ในเครื่อง",   self._count_export_files(), C["accent"],  C["accent3"]),
            ("✅", "สำเร็จ (session)", str(getattr(self,"_exp_ok",0)),   C["green"],  "#1B5E20"),
            ("❌", "ผิดพลาด",          str(getattr(self,"_exp_err",0)),  C["red"],    "#7F1D1D"),
            ("☁",  "อัปโหลด Drive",   str(getattr(self,"_exp_drive",0)),C["teal"],   "#004D40"),
        ]
        self._exp_stat_lbls = {}
        for icon, name, val, col, dark in stat_data:
            card = ctk.CTkFrame(self._exp_stats_frame, fg_color=C["exp_card"],
                                corner_radius=12)
            card.pack(side="left", fill="both", expand=True, padx=5, pady=4)
            ctk.CTkFrame(card, fg_color=col, height=4, corner_radius=2
                         ).pack(fill="x", padx=8, pady=(8,0))
            ctk.CTkLabel(card, text=icon,
                         font=ctk.CTkFont(size=18), text_color=col).pack(pady=(4,0))
            lbl = ctk.CTkLabel(card, text=val,
                               font=ctk.CTkFont(family=FONT, size=22, weight="bold"),
                               text_color=col)
            lbl.pack()
            ctk.CTkLabel(card, text=name,
                         font=ctk.CTkFont(family=FONT, size=9),
                         text_color=C["text_dim"]).pack(pady=(0,8))
            self._exp_stat_lbls[name] = lbl

    def _rebuild_exp_rooms(self):
        for w in self._exp_rooms_frame.winfo_children(): w.destroy()
        self._exp_room_vars.clear()
        rooms = [r.strip() for r in
                 self._cfg.get("fb_rooms","").split(",") if r.strip()]
        for r in rooms:
            var = ctk.BooleanVar(value=True)
            self._exp_room_vars[r] = var
            ctk.CTkCheckBox(self._exp_rooms_frame, text=r, variable=var,
                            fg_color=C["orange"], hover_color=C["amber"],
                            text_color=C["text"],
                            font=ctk.CTkFont(family=FONT, size=FS_BODY)
                            ).pack(anchor="w", pady=2)

    def _rebuild_exp_points(self):
        for w in self._exp_points_frame.winfo_children(): w.destroy()
        self._exp_point_vars.clear()
        pts = [p.strip() for p in
               self._cfg.get("fb_points","").split(",") if p.strip()]
        for p in pts:
            var = ctk.BooleanVar(value=True)
            self._exp_point_vars[p] = var
            ctk.CTkCheckBox(self._exp_points_frame, text=p, variable=var,
                            fg_color=C["orange"], hover_color=C["amber"],
                            text_color=C["text"],
                            font=ctk.CTkFont(family=FONT, size=FS_BODY)
                            ).pack(anchor="w", pady=2)

    def _toggle_exp_rooms(self):
        new = not all(v.get() for v in self._exp_room_vars.values())
        for v in self._exp_room_vars.values(): v.set(new)

    def _toggle_exp_points(self):
        new = not all(v.get() for v in self._exp_point_vars.values())
        for v in self._exp_point_vars.values(): v.set(new)

    @staticmethod
    def _short_path(p, n=32):
        return p if len(p)<=n else "..."+p[-(n-3):]

    def _pick_export_dir(self):
        d = filedialog.askdirectory(
            initialdir=self._cfg.get("export_dir", os.path.expanduser("~")))
        if d:
            self._cfg["export_dir"] = d; save_cfg(self._cfg)
            self._exp_path_lbl.configure(text=self._short_path(d))

    def _open_export_dir(self):
        d = self._cfg.get("export_dir","")
        if d and os.path.isdir(d):
            try: os.startfile(d)
            except: os.system(f'xdg-open "{d}"')
        else:
            messagebox.showinfo("โฟลเดอร์",f"ไม่พบ: {d}")

    def _count_export_files(self):
        d = self._cfg.get("export_dir","")
        if not d or not os.path.isdir(d): return "0"
        return str(len([f for f in os.listdir(d) if f.endswith(".csv")]))

    def _exp_log_write(self, msg):
        self._exp_log.configure(state="normal")
        ts = datetime.now().strftime("%H:%M:%S")
        self._exp_log.insert("end", f"[{ts}]  {msg}\n")
        self._exp_log.see("end")
        self._exp_log.configure(state="disabled")

    def _exp_clear_log(self):
        self._exp_log.configure(state="normal")
        self._exp_log.delete("1.0","end")
        self._exp_log.configure(state="disabled")
        self._exp_ok = self._exp_err = self._exp_drive = 0
        self._exp_update_stats()

    def _exp_update_stats(self):
        m = {"สำเร็จ (session)": str(self._exp_ok),
             "ผิดพลาด":          str(self._exp_err),
             "อัปโหลด Drive":   str(self._exp_drive)}
        for k,v in m.items():
            if k in self._exp_stat_lbls:
                self._exp_stat_lbls[k].configure(text=v)

    def _exp_run(self):
        if self._is_exporting:
            messagebox.showinfo("กำลังทำงาน","กรุณารอให้เสร็จก่อน"); return
        if not self._fb_mgr:
            messagebox.showwarning("Firebase",
                "ยังไม่ได้ตั้งค่า Firebase Key / URL\nไปที่ ⚙ Settings → 🔥 Firebase"); return
        rooms  = [r for r,v in self._exp_room_vars.items()  if v.get()]
        points = [p for p,v in self._exp_point_vars.items() if v.get()]
        if not rooms:
            messagebox.showwarning("Room","กรุณาเลือก Room อย่างน้อย 1 ห้อง"); return
        if not points:
            messagebox.showwarning("Point","กรุณาเลือก Point อย่างน้อย 1 จุด"); return
        if not self._cfg.get("export_dir",""):
            messagebox.showwarning("Export Dir","กรุณาตั้งค่าโฟลเดอร์บันทึกก่อน"); return
        do_del   = self._exp_do_delete.get()
        do_drive = self._exp_do_drive.get()
        if do_del and not messagebox.askyesno(
            "ยืนยัน — ลบ Firebase",
            f"⚠  คุณเปิดใช้ 'ลบ Firebase หลังดึง'\n\n"
            f"ระบบจะลบข้อมูลของ {len(rooms)} Room × {len(points)} Point\n"
            f"ออกจาก Firebase Realtime DB หลังบันทึกสำเร็จ\n\nยืนยันหรือไม่?"):
            return
        self._is_exporting = True
        self._exp_run_btn.configure(text="⏳  กำลังทำงาน...",
                                    state="disabled", fg_color=C["border"])
        self._set_status("🔥 Export กำลังทำงาน...", C["orange"])
        self._exp_progress.set(0)
        self._exp_ok = self._exp_err = self._exp_drive = 0
        threading.Thread(
            target=self._exp_bg,
            args=(rooms, points, do_drive, do_del),
            daemon=True).start()

    def _exp_bg(self, rooms, points, do_drive, do_delete):
        try:
            self.after(0, self._exp_log_write,
                       f"🚀 เริ่ม  Rooms={rooms}  Points={points}"
                       f"  Drive={do_drive}  Delete={do_delete}")
            
            if do_drive:
                pending_dir = os.path.join(self._cfg.get("export_dir",""), ".pending_drive")
                flush_pending_uploads(self._cfg.get("web_app_url",""), pending_dir, lambda m: self.after(0, self._exp_log_write, m))

            cfg_pass = dict(self._cfg)
            cfg_pass["_fb_mgr"] = self._fb_mgr
            total = len(rooms)*len(points); done = 0
            for room in rooms:
                for point in points:
                    self.after(0, self._exp_log_write,
                               f"\n{'─'*44}\n📂 [{room}]  [{point}]")
                    results = export_room_point(
                        room, point, cfg_pass,
                        do_drive=do_drive, do_delete=do_delete,
                        log_fn=lambda m: self.after(0, self._exp_log_write, m))
                    for r in results:
                        if r["status"]=="ok": self._exp_ok += 1
                        else:                 self._exp_err += 1
                        if r.get("drive"):    self._exp_drive += 1
                    done += 1
                    self.after(0, self._exp_progress.set, done/total)
                    self.after(0, self._exp_update_stats)
            self.after(0, self._exp_log_write,
                       f"\n✅ เสร็จทั้งหมด  "
                       f"สำเร็จ={self._exp_ok}  "
                       f"ผิดพลาด={self._exp_err}  "
                       f"Drive={self._exp_drive}")
            self.after(0, self._set_status, "✅ Export เสร็จ", C["green"])
        except Exception as e:
            import traceback; traceback.print_exc()
            self.after(0, self._exp_log_write, f"❌ ERROR: {e}")
            self.after(0, self._set_status, f"❌ Export ผิดพลาด", C["red"])
        finally:
            def _reset_btn():
                self._exp_run_btn.configure(
                    text="▶  เริ่มดึงและส่งออกข้อมูล",
                    state="normal", fg_color=C["orange"])
                self._is_exporting = False
                self._build_exp_stats()
            self.after(0, _reset_btn)

    # ══════════════════════════════════════════════════════════════
    #  ADVANCED SYNC & REPAIR (Google Drive ↔ Local)
    # ══════════════════════════════════════════════════════════════
    def _open_sync_dialog(self):
        if self._is_exporting:
            messagebox.showinfo("กำลังทำงาน", "กรุณารอให้งานปัจจุบันเสร็จก่อน")
            return
        if not self._drive_mgr:
            messagebox.showwarning("Drive", "กรุณาตั้งค่า Google Drive ใน Settings (ต้องมี OAuth Client และ Token)")
            return
        app_url = self._cfg.get("web_app_url", "")
        if not app_url:
            messagebox.showwarning("App Script", "กรุณาตั้งค่า App Script URL ในหน้า ⚙ Settings ก่อนครับ")
            return
        local_dir = self._cfg.get("export_dir", "")
        if not local_dir or not os.path.isdir(local_dir):
            messagebox.showwarning("Local Dir", "ไม่พบโฟลเดอร์ Local ในเครื่อง กรุณาตั้งค่าและสร้างโฟลเดอร์ก่อน")
            return

        self._sync_dialog_open = True
        
        dlg = ctk.CTkToplevel(self)
        dlg.title("🔄 Advanced Sync & Repair Manager")
        dlg.geometry("900x650")
        dlg.resizable(True, True)
        
        def _on_close():
            self._sync_dialog_open = False
            dlg.destroy()
        dlg.protocol("WM_DELETE_WINDOW", _on_close)

        hdr = ctk.CTkFrame(dlg, fg_color=C["teal"], height=52, corner_radius=0)
        hdr.pack(fill="x")
        hdr.pack_propagate(False)
        ctk.CTkLabel(hdr, text="🔄 Sync & Repair — เปรียบเทียบข้อมูลแบบรวดเร็ว",
                     font=ctk.CTkFont(family=FONT, size=FS_LABEL, weight="bold"),
                     text_color="white").pack(side="left", padx=16)

        # Filter bar
        filt_f = ctk.CTkFrame(dlg, fg_color=C["card_bg"], corner_radius=0)
        filt_f.pack(fill="x")
        
        ctk.CTkLabel(filt_f, text="📅 กรองวันที่:", font=ctk.CTkFont(family=FONT, size=FS_BODY), text_color=C["text_soft"]).pack(side="left", padx=(16, 8), pady=10)
        self._sync_date_var = ctk.StringVar(value="ทั้งหมด (All)")
        self._sync_date_menu = ctk.CTkOptionMenu(filt_f, variable=self._sync_date_var, values=["ทั้งหมด (All)"],
                                                 font=ctk.CTkFont(family=FONT, size=FS_BODY), 
                                                 command=self._on_sync_filter_change, width=150)
        self._sync_date_menu.pack(side="left", pady=10)
        
        ctk.CTkFrame(filt_f, width=2, height=20, fg_color=C["border"]).pack(side="left", padx=15)
        
        self._show_miss_local = ctk.BooleanVar(value=True)
        self._show_miss_drive = ctk.BooleanVar(value=True)
        
        ctk.CTkCheckBox(filt_f, text="📥 ขาดบนเครื่อง", variable=self._show_miss_local, 
                        fg_color=C["teal"], font=ctk.CTkFont(family=FONT, size=FS_BODY), command=self._on_sync_filter_change).pack(side="left", padx=8)
        ctk.CTkCheckBox(filt_f, text="☁️ ขาดบน Drive", variable=self._show_miss_drive, 
                        fg_color=C["orange"], font=ctk.CTkFont(family=FONT, size=FS_BODY), command=self._on_sync_filter_change).pack(side="left", padx=8)

        # List Headers
        ch = ctk.CTkFrame(dlg, fg_color=C["input_bg"], height=34, corner_radius=0)
        ch.pack(fill="x", padx=6)
        ch.pack_propagate(False)
        for txt,w in [("แหล่งข้อมูล",130), ("ชื่อไฟล์ (File Name)", 380), ("วันที่", 120), ("สถานะ (Size Check)", 250)]:
            ctk.CTkLabel(ch, text=txt, width=w, font=ctk.CTkFont(family=FONT, size=FS_SMALL, weight="bold"), text_color=C["text_soft"], anchor="w").pack(side="left", padx=4, pady=6)

        # Listbox
        lf = ctk.CTkFrame(dlg, fg_color=C["card_bg"], corner_radius=6)
        lf.pack(fill="both", expand=True, padx=6, pady=4)
        sb2 = ttk.Scrollbar(lf)
        sb2.pack(side="right", fill="y")
        self._sync_listbox = tk.Listbox(lf, bg=C["input_bg"], fg=C["text"], font=(FONT_MONO, FS_BODY), relief="flat",
                                        selectbackground=C["accent"], selectforeground="white", yscrollcommand=sb2.set,
                                        bd=0, selectmode=tk.EXTENDED, activestyle="dotbox", highlightthickness=0)
        self._sync_listbox.pack(fill="both", expand=True, padx=4, pady=4)
        sb2.config(command=self._sync_listbox.yview)

        # Status row
        st_row = ctk.CTkFrame(dlg, fg_color="transparent")
        st_row.pack(fill="x", padx=8, pady=(0, 2))
        self._sync_status_lbl = ctk.CTkLabel(st_row, text="⏳ กำลังเตรียมการโหลด...", 
                                             text_color=C["amber"], font=ctk.CTkFont(family=FONT, size=FS_BODY))
        self._sync_status_lbl.pack(side="left", padx=4)
        self._sync_sel_lbl = ctk.CTkLabel(st_row, text="", text_color=C["accent"], font=ctk.CTkFont(family=FONT, size=FS_BODY, weight="bold"))
        self._sync_sel_lbl.pack(side="right", padx=8)

        def update_sel(event=None):
            n = len(self._sync_listbox.curselection())
            self._sync_sel_lbl.configure(text=f"เลือกแล้ว {n} ไฟล์" if n else "")
            
        self._sync_listbox.bind("<<ListboxSelect>>", update_sel)
        self._sync_listbox.bind("<Control-a>", lambda _: (self._sync_listbox.select_set(0, tk.END), update_sel()))
        self._sync_listbox.bind("<Control-A>", lambda _: (self._sync_listbox.select_set(0, tk.END), update_sel()))

        # Bottom Buttons
        bf = ctk.CTkFrame(dlg, fg_color=C["card_bg"], corner_radius=0, height=62)
        bf.pack(fill="x", side="bottom")
        bf.pack_propagate(False)
        
        def do_sync():
            idxs = self._sync_listbox.curselection()
            if not idxs:
                messagebox.showwarning("เลือกไฟล์", "กรุณาเลือกไฟล์อย่างน้อย 1 ไฟล์เพื่อ Sync", parent=dlg)
                return
            selected_items = [self._sync_visible_items[i] for i in idxs]
            _on_close()
            
            self._is_exporting = True
            self._exp_run_btn.configure(state="disabled")
            self._set_status("🔄 กำลังเตรียมข้อมูล Sync...", C["teal"])
            self._exp_progress.set(0)
            self._exp_clear_log()
            
            threading.Thread(target=self._bg_process_selected_sync, args=(selected_items, local_dir, app_url), daemon=True).start()

        ctk.CTkButton(bf, text="✅  เริ่ม Sync ไฟล์ที่เลือก", fg_color=C["teal"], hover_color="#004D40", height=42, width=220,
                      font=ctk.CTkFont(family=FONT, size=FS_LABEL, weight="bold"), command=do_sync).pack(side="left", padx=12, pady=10)
        ctk.CTkButton(bf, text="☑  เลือกทั้งหมด", fg_color=C["card_bg"], hover_color=C["border"], text_color=C["accent"], height=42, width=150,
                      font=ctk.CTkFont(family=FONT, size=FS_BODY), command=lambda: (self._sync_listbox.select_set(0, tk.END), update_sel())).pack(side="left", padx=4, pady=10)
        ctk.CTkButton(bf, text="✕  ยกเลิก", fg_color=C["text_soft"], hover_color="#37474F", text_color="white", height=42, width=110,
                      font=ctk.CTkFont(family=FONT, size=FS_BODY), command=_on_close).pack(side="right", padx=12, pady=10)

        self._sync_all_items = []
        self._sync_visible_items = []

        threading.Thread(target=self._load_sync_data, args=(local_dir,), daemon=True).start()

    def _load_sync_data(self, local_dir):
        try:
            self.after(0, lambda: self._sync_status_lbl.configure(text="กำลังสแกนไฟล์ในเครื่อง... 0%", text_color=C["amber"]))
            local_files = [f for f in os.listdir(local_dir) if f.endswith(".csv")]
            
            file_map = {}
            total_local = len(local_files) if local_files else 1
            for i, f in enumerate(local_files):
                m = re.search(r'(\d{2}-\d{2}-\d{4})', f)
                date_str = m.group(1) if m else "Unknown"
                sz = os.path.getsize(os.path.join(local_dir, f))
                file_map[f] = {"name": f, "local": True, "drive": False, "id": None, "date": date_str, "l_size": sz, "d_size": 0}
                
                if i % max(1, total_local // 10) == 0:
                    pct = int((i/total_local)*50)
                    self.after(0, lambda p=pct: self._sync_status_lbl.configure(text=f"กำลังสแกนไฟล์ในเครื่อง... {p}%"))

            self.after(0, lambda: self._sync_status_lbl.configure(text="กำลังดึงข้อมูลจาก Google Drive... (อาจใช้เวลาครู่หนึ่ง)"))
            drive_res = self._drive_mgr.list_all()
            drive_files = drive_res.get("_all", [])
            if not drive_files:
                drive_files = drive_res.get("pm", []) + drive_res.get("dht", [])
                
            total_drive = len(drive_files) if drive_files else 1
            for i, df in enumerate(drive_files):
                fname = df["name"]
                dsz = int(df.get("size", 0))
                if fname not in file_map:
                    m = re.search(r'(\d{2}-\d{2}-\d{4})', fname)
                    date_str = m.group(1) if m else df.get("modifiedTime","Unknown")[:10]
                    file_map[fname] = {"name": fname, "local": False, "drive": True, "id": df["id"], "date": date_str, "l_size": 0, "d_size": dsz}
                else:
                    file_map[fname]["drive"] = True
                    file_map[fname]["id"] = df["id"]
                    file_map[fname]["d_size"] = dsz
                    
                if i % max(1, total_drive // 10) == 0:
                    pct = 50 + int((i/total_drive)*49)
                    self.after(0, lambda p=pct: self._sync_status_lbl.configure(text=f"กำลังจับคู่ข้อมูล... {p}%"))

            for item in file_map.values():
                ls = item["l_size"]; ds = item["d_size"]
                if ls == 0 and ds > 0: item["status"] = "missing_local"
                elif ds == 0 and ls > 0: item["status"] = "missing_drive"
                else:
                    diff = ls - ds
                    if diff > 2048: item["status"] = "missing_drive"
                    elif diff < -2048: item["status"] = "missing_local"
                    else: item["status"] = "synced"

            self._sync_all_items = list(file_map.values())
            self._sync_all_items.sort(key=lambda x: (x["date"], x["name"]), reverse=True)
            
            dates = sorted(list(set(v["date"] for v in self._sync_all_items if v["date"] != "Unknown")), reverse=True)
            dates.insert(0, "ทั้งหมด (All)")
            
            def _update_ui():
                if not getattr(self, "_sync_dialog_open", False): return
                try:
                    self._sync_date_menu.configure(values=dates)
                    self._sync_date_var.set("ทั้งหมด (All)")
                    self._on_sync_filter_change()
                    self._sync_status_lbl.configure(text=f"✅ พร้อมใช้งาน พบไฟล์ทั้งหมด {len(self._sync_all_items)} รายการ (กด Click ลากเพื่อเลือก หรือ Ctrl+A)", text_color=C["green"])
                except: pass
            
            self.after(0, _update_ui)
        except Exception as e:
            self.after(0, lambda: self._sync_status_lbl.configure(text=f"❌ โหลดข้อมูลผิดพลาด: {e}", text_color=C["red"]))

    def _on_sync_filter_change(self, val=None):
        if not getattr(self, "_sync_dialog_open", False): return
        filt = self._sync_date_var.get()
        show_m_local = self._show_miss_local.get()
        show_m_drive = self._show_miss_drive.get()
        
        self._sync_listbox.delete(0, tk.END)
        self._sync_visible_items = []
        
        for item in self._sync_all_items:
            if filt != "ทั้งหมด (All)" and item["date"] != filt: continue
            
            st = item["status"]
            if st == "missing_local" and not show_m_local: continue
            if st == "missing_drive" and not show_m_drive: continue
            
            self._sync_visible_items.append(item)
            
            l_mark = "💻 Local" if item["local"] else "          "
            d_mark = "☁ Drive" if item["drive"] else "       "
            
            if st == "missing_local": st_mark = "📥 ขาดบนเครื่อง"
            elif st == "missing_drive": st_mark = "☁️ ขาดบน Drive"
            else: st_mark = "✅ ตรงกันสมบูรณ์"
            
            row_txt = f" [{l_mark}] [{d_mark}]   {item['name']:<42}   {item['date']:<12}   {st_mark}"
            self._sync_listbox.insert(tk.END, row_txt)
            
        self._sync_sel_lbl.configure(text="")

    def _bg_process_selected_sync(self, items, local_dir, app_url):
        try:
            total = len(items)
            fixed = 0
            self.after(0, self._exp_log_write, f"🚀 เริ่ม 2-Way Sync และจัดเรียงเวลา จำนวน {total} ไฟล์")
            
            pending_dir = os.path.join(local_dir, ".pending_drive")
            flush_pending_uploads(app_url, pending_dir, lambda m: self.after(0, self._exp_log_write, m))
            
            for i, item in enumerate(items):
                fname = item["name"]
                fpath = os.path.join(local_dir, fname)
                in_local = item["local"]
                in_drive = item["drive"]
                drive_id = item["id"]
                
                self.after(0, self._exp_log_write, f"\n🔍 ไฟล์: {fname}")
                
                df_local = pd.DataFrame()
                if in_local and os.path.exists(fpath):
                    df_local = pd.read_csv(fpath, dtype=str)
                
                df_drive = pd.DataFrame()
                if in_drive and drive_id:
                    try:
                        buf = self._drive_mgr.download(drive_id)
                        df_drive = pd.read_csv(buf, dtype=str)
                    except Exception as e:
                        self.after(0, self._exp_log_write, f"  ❌ โหลดจาก Drive ล้มเหลว: {e}")
                
                df_final = None
                
                # Case 1: มีใน Local อย่างเดียว -> ดันขึ้น Drive เต็มๆ
                if in_local and not in_drive:
                    if not df_local.empty and "datetime" in df_local.columns:
                        self.after(0, self._exp_log_write, f"  ▸ ไม่มีบน Drive -> กำลังสร้างใหม่บน Drive ({len(df_local)} แถว)")
                        success, msg = upload_with_pending(df_local, fname, app_url, pending_dir)
                        if success:
                            self.after(0, self._exp_log_write, f"  ✅ อัปโหลดขึ้น Drive สำเร็จ")
                            fixed += 1
                            self._exp_drive += 1
                        else:
                            self.after(0, self._exp_log_write, f"  ⚠️ {msg}")
                        df_final = df_local
                        
                # Case 2: มีใน Drive อย่างเดียว -> โหลดลงเครื่องเต็มๆ
                elif in_drive and not in_local:
                    if not df_drive.empty and "datetime" in df_drive.columns:
                        self.after(0, self._exp_log_write, f"  ▸ ไม่มีในเครื่อง -> ดาวน์โหลดจาก Drive ลง Local ({len(df_drive)} แถว)")
                        try:
                            # 🟢 เรียงข้อมูลก่อนเซฟ
                            df_drive['_dt'] = pd.to_datetime(df_drive['datetime'], format="%d-%m-%Y-%H-%M-%S", errors='coerce')
                            df_drive = df_drive.sort_values('_dt').drop(columns=['_dt'])
                            df_drive.to_csv(fpath, index=False, encoding='utf-8-sig')
                            self.after(0, self._exp_log_write, f"  ✅ ดาวน์โหลดและเรียงข้อมูลลงเครื่องสำเร็จ")
                            fixed += 1
                        except Exception as e:
                            self.after(0, self._exp_log_write, f"  ❌ เซฟไฟล์ลงเครื่องล้มเหลว: {e}")
                        df_final = df_drive
                            
                # Case 3: มีทั้ง Local และ Drive -> 2-Way Sync ตรวจหาส่วนต่าง
                elif in_local and in_drive:
                    if not df_local.empty and not df_drive.empty and "datetime" in df_local.columns and "datetime" in df_drive.columns:
                        missing_in_drive = df_local[~df_local["datetime"].isin(df_drive["datetime"])]
                        missing_in_local = df_drive[~df_drive["datetime"].isin(df_local["datetime"])]
                        
                        updated_local = False
                        
                        if not missing_in_drive.empty:
                            self.after(0, self._exp_log_write, f"  ▸ พบส่วนต่างที่ Drive ขาด {len(missing_in_drive)} แถว -> กำลังดันขึ้น Drive")
                            success, msg = upload_with_pending(missing_in_drive, fname, app_url, pending_dir)
                            if success:
                                self.after(0, self._exp_log_write, f"  ✅ อัปโหลดส่วนที่ขาดขึ้น Drive สำเร็จ")
                                fixed += 1
                                self._exp_drive += 1
                            else:
                                self.after(0, self._exp_log_write, f"  ⚠️ {msg}")
                                
                        if not missing_in_local.empty:
                            self.after(0, self._exp_log_write, f"  ▸ พบส่วนต่างที่ Local ขาด {len(missing_in_local)} แถว -> นำมาต่อและเรียงข้อมูลใหม่")
                            try:
                                df_local_updated = pd.concat([df_local, missing_in_local], ignore_index=True)
                                # 🟢 เรียงข้อมูลเวลาจากน้อยไปมาก
                                df_local_updated['_dt'] = pd.to_datetime(df_local_updated['datetime'], format="%d-%m-%Y-%H-%M-%S", errors='coerce')
                                df_local_updated = df_local_updated.sort_values('_dt').drop(columns=['_dt'])
                                df_local_updated.to_csv(fpath, index=False, encoding='utf-8-sig')
                                self.after(0, self._exp_log_write, f"  ✅ อัปเดต Local สำเร็จ")
                                df_final = df_local_updated
                                updated_local = True
                                fixed += 1
                            except Exception as e:
                                self.after(0, self._exp_log_write, f"  ❌ อัปเดต Local ล้มเหลว: {e}")
                                
                        if missing_in_drive.empty and missing_in_local.empty:
                            self.after(0, self._exp_log_write, f"  ✓ ข้อมูลตรงกัน ไม่ต้องดำเนินการเพิ่ม")
                            
                        if not updated_local:
                            df_final = df_local
                            
                # 🟢 รายงาน % และช่วงที่ขาด หลังจากอัปเดตไฟล์เสร็จสิ้น (แบบเร็ว)
                if df_final is not None and "datetime" in df_final.columns:
                    # เช็คเพิ่มเติมว่าขาดหน้าเที่ยงหรือหลังเที่ยง
                    dt_col = pd.to_datetime(df_final['datetime'], format="%d-%m-%Y-%H-%M-%S", errors='coerce').dropna()
                    if not dt_col.empty:
                        total_u = dt_col.nunique()
                        pct = min((total_u / 86400) * 100, 100.0)
                        
                        m_cnt = dt_col[dt_col.dt.hour < 12].nunique()
                        a_cnt = dt_col[dt_col.dt.hour >= 12].nunique()
                        m_pct = min((m_cnt / 43200) * 100, 100.0)
                        a_pct = min((a_cnt / 43200) * 100, 100.0)
                        
                        miss_str = ""
                        if pct >= 98: miss_str = "(ข้อมูลครบถ้วน)"
                        elif m_pct < 95 and a_pct < 95: miss_str = "(ขาดแหว่งหนักทั้งวัน)"
                        elif m_pct < 95: miss_str = "(ส่วนใหญ่ขาดช่วงหน้าเที่ยง)"
                        elif a_pct < 95: miss_str = "(ส่วนใหญ่ขาดช่วงหลังเที่ยง)"
                        else: miss_str = "(แหว่งย่อยๆ)"
                        
                        self.after(0, self._exp_log_write, f"  📊 ความสมบูรณ์: {pct:.1f}% {miss_str}")
                            
                self.after(0, self._exp_progress.set, (i+1)/total)
                self.after(0, self._exp_update_stats)

            self.after(0, self._exp_log_write, f"\n🎉 Sync เสร็จสิ้น! ดำเนินการอัปเดตไฟล์/Drive สำเร็จไป {fixed} รายการ")
            self.after(0, self._set_status, "✅ ซ่อมแซม/Sync ข้อมูลเสร็จสิ้น", C["green"])
            
        except Exception as e:
            import traceback; traceback.print_exc()
            self.after(0, self._exp_log_write, f"❌ ERROR: {e}")
            self.after(0, self._set_status, f"❌ Sync ผิดพลาด", C["red"])
        finally:
            self.after(0, setattr, self, "_is_exporting", False)
            self.after(0, self._exp_progress.set, 0)
            self.after(0, lambda: self._exp_run_btn.configure(state="normal"))

    def _on_time_change(self, choice=None):
        if choice is None: choice = self._time_range.get()
        if choice == "กำหนดเอง...":
            self._custom_frame.pack(fill="x", padx=12, pady=(0,4))
        else:
            self._custom_frame.pack_forget()

    def _get_time_range(self):
        choice = self._time_range.get()
        if choice == "กำหนดเอง...":
            try:
                h0 = int(self._custom_start.get() or 0)
                h1 = int(self._custom_end.get() or 24)
                assert 0<=h0<h1<=24
                return h0, h1
            except:
                messagebox.showerror("ช่วงเวลาผิด","กรอกชั่วโมงให้ถูกต้อง (0–24)")
                return None
        return TIME_RANGE_OPTIONS[choice]

    def _resolve_label(self, raw_name: str) -> str:
        cfg = self._cfg
        for i in range(1, 6):
            kw = cfg.get(f"kw{i}", "").strip()
            nm = cfg.get(f"nm{i}", "").strip()
            if kw and kw.lower() in raw_name.lower():
                return nm if nm else raw_name
        if cfg.get("station_name", "").strip():
            return cfg["station_name"].strip()
        return raw_name

    def _add_files(self):
        init_dir = self._cfg.get("local_dir","") or os.path.expanduser("~")
        paths = filedialog.askopenfilenames(
            initialdir=init_dir,
            title="เลือกไฟล์ CSV  —  Ctrl / Shift เลือกหลายไฟล์",
            filetypes=[("CSV Files","*.csv"),("All Files","*.*")])
        if not paths: return
        self._set_status(f"⏳ กำลังโหลด {len(paths)} ไฟล์...", C["amber"])
        threading.Thread(target=self._bg_load_files, args=(paths,), daemon=True).start()

    def _bg_load_files(self, paths):
        errors=[]; loaded=0
        for path in paths:
            try:
                df = pd.read_csv(path, low_memory=False)
                df, date_str = self._parse_df(df, path)
                if df is None:
                    errors.append(f"❌ {os.path.basename(path)}: ไม่พบ datetime column"); continue
                
                label = os.path.splitext(os.path.basename(path))[0]
                display, color = self._get_color_for_label(label)

                self.files_data.append({"label":display,"df_raw":df,
                                         "color":color,"date_str":date_str,"path":path})
                loaded += 1
                self.after(0, self._refresh_listbox)
            except Exception as e:
                errors.append(f"❌ {os.path.basename(path)}: {e}")
        msg = f"✅ โหลดแล้ว {loaded} ไฟล์"
        if errors: msg += f"  ⚠ {len(errors)} ผิดพลาด"
        self.after(0, self._set_status, msg, C["green"] if not errors else C["amber"])
        if errors: self.after(0, messagebox.showwarning, "บางไฟล์มีปัญหา", "\n".join(errors))

    def _parse_df(self, df, path=""):
        cfg=self._cfg; dt_col=cfg.get("dt_col","").strip(); dt_fmt=cfg.get("dt_fmt","").strip()
        if dt_col and dt_col in df.columns:
            df["Datetime"] = pd.to_datetime(df[dt_col],
                format=dt_fmt if dt_fmt else None, errors="coerce")
        else:
            date_col      = find_col(df.columns, "date")
            time_col_only = find_col(df.columns, "time")
            datetime_col  = find_col(df.columns, "datetime", "timestamp")
            if date_col and time_col_only and date_col != time_col_only:
                combined = df[date_col].astype(str) + " " + df[time_col_only].astype(str)
                df["Datetime"] = pd.to_datetime(combined, dayfirst=True, errors="coerce")
            elif datetime_col:
                df["Datetime"] = pd.to_datetime(df[datetime_col],
                    format="%d-%m-%Y-%H-%M-%S", errors="coerce")
                if df["Datetime"].isnull().mean() > 0.5:
                    df["Datetime"] = pd.to_datetime(df[datetime_col], errors="coerce")
            else:
                return None, ""
        df = df.dropna(subset=["Datetime"]).copy()
        if df.empty: return None,""
        non_dt = [c for c in df.columns if c!="Datetime"]
        df[non_dt] = df[non_dt].apply(pd.to_numeric, errors="coerce")
        date_str = _thai_date_str(df["Datetime"].dt.date.mode()[0]) if len(df)>0 else "Unknown"
        return df, date_str

    def _load_folder(self):
        init_dir = self._cfg.get("local_dir","") or os.path.expanduser("~")
        path = filedialog.askdirectory(initialdir=init_dir)
        if not path: return
        files = sorted([os.path.join(path,f) for f in os.listdir(path) if f.endswith(".csv")])
        if not files: messagebox.showwarning("ว่าง","ไม่พบไฟล์ CSV ในโฟลเดอร์นี้"); return
        self._set_status(f"⏳ กำลังโหลด {len(files)} ไฟล์...", C["amber"])
        threading.Thread(target=self._bg_load_files, args=(files,), daemon=True).start()

    def _remove_selected(self):
        sel = list(self.listbox.curselection())
        if not sel: return
        for idx in sorted(sel, reverse=True): self.files_data.pop(idx)
        self._refresh_listbox()

    def _clear_all(self):
        self.files_data.clear(); self.listbox.delete(0, tk.END)
        self._color_map.clear()
        self._color_idx = 0
        self._set_status("ล้างข้อมูลแล้ว", C["text_dim"])
        self._show_placeholder()

    def _refresh_listbox(self):
        self.listbox.delete(0, tk.END)
        for i,item in enumerate(self.files_data):
            self.listbox.insert(tk.END, f"● {item['label']}  [{item['date_str']}]")
            self.listbox.itemconfig(i, fg=item["color"])

    def _set_info(self, txt):
        self._info_box.configure(state="normal")
        self._info_box.delete("1.0","end")
        self._info_box.insert("end", txt)
        self._info_box.configure(state="disabled")

    def _set_status(self, txt, col=None):
        col = col or C["text_dim"]
        self._status_lbl.configure(text="● "+txt, text_color=col)
        try: self._status_sb.configure(text=txt, text_color=col)
        except: pass

    def _show_placeholder(self):
        if self._current_fig:
            try:
                self._current_fig.clf() # ล้างหน่วยความจำกราฟเก่า
                plt.close(self._current_fig)
            except: pass
            self._current_fig = None
        for w in self._chart_frame.winfo_children(): w.destroy()
        try: self._scroll_canvas.yview_moveto(0)
        except: pass
        fig, ax = plt.subplots(figsize=(15,6), facecolor=C["plot_bg"])
        ax.set_facecolor(C["plot_bg"]); ax.set_xticks([]); ax.set_yticks([])
        for sp in ax.spines.values(): sp.set_visible(False)
        ax.text(.5,.60,"◉",color=C["accent"],fontsize=100,alpha=0.06,
                ha="center",va="center",transform=ax.transAxes)
        ax.text(.5,.44,"📁  เพิ่มไฟล์ CSV  →  เลือกประเภทกราฟ  →  กด  ▶ ANALYZE & PLOT",
                color=C["text_soft"],fontsize=14,ha="center",va="center",
                transform=ax.transAxes,fontfamily=FONT)
        ax.text(.5,.34,"ไฟล์แต่ละไฟล์ = 1 วัน  ·  กราฟจะพลอตต่อเนื่องตามลำดับวันที่จริง",
                color=C["text_dim"],fontsize=11,ha="center",va="center",
                transform=ax.transAxes,fontfamily=FONT)
        cv = FigureCanvasTkAgg(fig, master=self._chart_frame)
        cv.draw(); cv.get_tk_widget().pack(fill="both", expand=True)
        self._current_fig = fig

    def _open_settings(self):
        if self._settings_win and self._settings_win.winfo_exists():
            self._settings_win.lift(); self._settings_win.focus(); return
        def on_save():
            self._cfg = load_cfg(); self._init_integrations()
            self._rebuild_exp_rooms(); self._rebuild_exp_points()
            self._exp_path_lbl.configure(
                text=self._short_path(self._cfg.get("export_dir","")))
            self._build_exp_stats()
        self._settings_win = SettingsDialog(self, on_save_cb=on_save)
        self._settings_win.lift()

    def _open_browser(self):
        if not self._fb_mgr:
            messagebox.showwarning("Firebase",
                "ตั้งค่า Firebase Key / URL ใน ⚙ Settings → 🔥 Firebase ก่อน"); return
        if self._browser_win and self._browser_win.winfo_exists():
            self._browser_win.lift(); return
        self._browser_win = FirebaseBrowserDialog(
            self, self._fb_mgr, self._cfg.get("fb_base_path","SAC"))
        self._browser_win.lift()

    def _open_drive(self, mode="plot"):
        """ mode: 'plot', 'sheet', หรือ 'merge' """
        if not HAS_GDRIVE:
            messagebox.showwarning("Drive",
                "ติดตั้ง: pip install google-auth-oauthlib google-api-python-client"); return
        if not self._drive_mgr:
            messagebox.showwarning("Drive","ตั้งค่า Folder ID + OAuth ใน Settings ก่อน"); return
        self._show_drive_dialog(mode)

    def _show_drive_dialog(self, mode="plot"):
        dlg = ctk.CTkToplevel(self)
        dlg.title(f"☁  Google Drive — เลือกไฟล์ CSV ({mode.upper()})")
        dlg.geometry("860x640"); dlg.resizable(True,True)
        hdr = ctk.CTkFrame(dlg, fg_color=C["accent"], height=52, corner_radius=0)
        hdr.pack(fill="x"); hdr.pack_propagate(False)
        ctk.CTkLabel(hdr, text="☁  Google Drive",
                     font=ctk.CTkFont(family=FONT, size=FS_LABEL, weight="bold"),
                     text_color="white").pack(side="left", padx=16, pady=13)
        ctk.CTkLabel(hdr, text="Ctrl / Shift / Ctrl+A  เพื่อเลือกหลายไฟล์",
                     font=ctk.CTkFont(family=FONT, size=FS_SMALL),
                     text_color="#BBDEFB").pack(side="right", padx=16)
        sf = ctk.CTkFrame(dlg, fg_color=C["card_bg"], corner_radius=0); sf.pack(fill="x")
        ctk.CTkLabel(sf, text="  🔍", font=ctk.CTkFont(family=FONT, size=FS_BODY),
                     text_color=C["text_soft"]).pack(side="left", padx=6, pady=8)
        sq = ctk.StringVar()
        search_e = ctk.CTkEntry(sf, textvariable=sq, height=40,
                                placeholder_text="ค้นหาชื่อไฟล์...",
                                font=ctk.CTkFont(family=FONT, size=FS_BODY))
        search_e.pack(side="left", fill="x", expand=True, pady=8)
        ctk.CTkButton(sf, text="ค้นหา", width=100, height=40,
                      fg_color=C["teal"], hover_color="#006064",
                      font=ctk.CTkFont(family=FONT, size=FS_BODY),
                      command=lambda: threading.Thread(
                          target=bg_load, args=(sq.get(),), daemon=True).start()
                      ).pack(side="left", padx=6, pady=8)
        ch = ctk.CTkFrame(dlg, fg_color=C["input_bg"], height=34, corner_radius=0)
        ch.pack(fill="x", padx=6); ch.pack_propagate(False)
        for txt,w in [("  ชื่อไฟล์",400),("โฟลเดอร์",75),("ขนาด",95),("วันที่แก้ไข",120)]:
            ctk.CTkLabel(ch, text=txt, width=w,
                         font=ctk.CTkFont(family=FONT, size=FS_SMALL, weight="bold"),
                         text_color=C["text_soft"], anchor="w"
                         ).pack(side="left", padx=4, pady=6)
        lf = ctk.CTkFrame(dlg, fg_color=C["card_bg"], corner_radius=6)
        lf.pack(fill="both", expand=True, padx=6, pady=4)
        sb2 = ttk.Scrollbar(lf); sb2.pack(side="right", fill="y")
        lb = tk.Listbox(lf, bg=C["input_bg"], fg=C["text"],
                        font=(FONT, FS_BODY), relief="flat",
                        selectbackground=C["accent"], selectforeground="white",
                        yscrollcommand=sb2.set, bd=0,
                        selectmode=tk.EXTENDED, activestyle="dotbox",
                        highlightthickness=0)
        lb.pack(fill="both", expand=True, padx=4, pady=4)
        sb2.config(command=lb.yview)
        st_row = ctk.CTkFrame(dlg, fg_color="transparent"); st_row.pack(fill="x", padx=8, pady=(0,2))
        st = ctk.CTkLabel(st_row, text="กำลังโหลด...", text_color=C["amber"],
                           font=ctk.CTkFont(family=FONT, size=FS_BODY)); st.pack(side="left", padx=4)
        sel_lbl = ctk.CTkLabel(st_row, text="", text_color=C["accent"],
                                font=ctk.CTkFont(family=FONT, size=FS_BODY, weight="bold"))
        sel_lbl.pack(side="right", padx=8)
        _files = []
        def update_sel(event=None):
            n = len(lb.curselection())
            sel_lbl.configure(text=f"เลือกแล้ว {n} ไฟล์" if n else "")
        lb.bind("<<ListboxSelect>>", update_sel)
        lb.bind("<Control-a>", lambda _: (lb.select_set(0,tk.END), update_sel()))
        lb.bind("<Control-A>", lambda _: (lb.select_set(0,tk.END), update_sel()))
        search_e.bind("<Return>",
            lambda _: threading.Thread(target=bg_load, args=(sq.get(),), daemon=True).start())
        
        def bg_load(query=""):
            dlg.after(0, lambda: st.configure(text="กำลังโหลด...", text_color=C["amber"]))
            try:
                res = self._drive_mgr.list_all(query)
                if res.get("_all") is not None:
                    files = res["_all"]
                else:
                    files = ([dict(f,_folder="PM")  for f in res.get("pm",[])] +
                             [dict(f,_folder="DHT") for f in res.get("dht",[])])
                _files.clear(); _files.extend(files)
                def _u():
                    lb.delete(0,"end")
                    for f in files:
                        sz = f.get("size","?")
                        try:    sz = f"{int(sz)//1024:,} KB"
                        except: sz = "—"
                        lb.insert("end",
                            f"  {f['name']:<44}  {f['_folder']:<12}  {sz:>9}    {f.get('modifiedTime','')[:10]}")
                    st.configure(text=f"พบ {len(files)} ไฟล์   (Ctrl+A เลือกทั้งหมด)",
                                 text_color=C["green"]); update_sel()
                dlg.after(0, _u)
            except Exception as e:
                dlg.after(0, lambda: st.configure(text=str(e), text_color=C["red"]))
        
        def do_download():
            idxs = lb.curselection()
            if not idxs:
                messagebox.showwarning("เลือกไฟล์","กรุณาเลือกไฟล์อย่างน้อย 1 ไฟล์",parent=dlg); return
            chosen = [_files[i] for i in idxs]; dlg.destroy()
            
            if mode == "plot":
                self._set_status(f"⏳ กำลังดาวน์โหลด {len(chosen)} ไฟล์...", C["amber"])
                threading.Thread(target=self._bg_drive_dl_multi, args=(chosen,), daemon=True).start()
            elif mode == "sheet":
                self._sheet_status.configure(text=f"⏳ กำลังดาวน์โหลด {len(chosen)} ไฟล์จาก Drive...", text_color=C["amber"])
                threading.Thread(target=self._bg_drive_dl_sheet, args=(chosen,), daemon=True).start()
            elif mode == "merge":
                self._merge_status.configure(text=f"⏳ กำลังดาวน์โหลด {len(chosen)} ไฟล์จาก Drive...", text_color=C["amber"])
                threading.Thread(target=self._bg_drive_dl_merge, args=(chosen,), daemon=True).start()

        bf = ctk.CTkFrame(dlg, fg_color=C["card_bg"], corner_radius=0, height=62)
        bf.pack(fill="x", side="bottom"); bf.pack_propagate(False)
        ctk.CTkButton(bf, text="✅  โหลดไฟล์ที่เลือก",
                      fg_color=C["accent"], hover_color=C["accent2"],
                      height=42, width=210,
                      font=ctk.CTkFont(family=FONT, size=FS_LABEL, weight="bold"),
                      command=do_download).pack(side="left", padx=12, pady=10)
        ctk.CTkButton(bf, text="☑  เลือกทั้งหมด",
                      fg_color=C["card_bg"], hover_color=C["border"],
                      text_color=C["accent"], height=42, width=150,
                      font=ctk.CTkFont(family=FONT, size=FS_BODY),
                      command=lambda: (lb.select_set(0,tk.END), update_sel())
                      ).pack(side="left", padx=4, pady=10)
        ctk.CTkButton(bf, text="✕  ยกเลิก",
                      fg_color=C["text_soft"], hover_color="#37474F",
                      text_color="white", height=42, width=110,
                      font=ctk.CTkFont(family=FONT, size=FS_BODY),
                      command=dlg.destroy).pack(side="right", padx=12, pady=10)
        threading.Thread(target=bg_load, daemon=True).start()

    def _save_drive_to_temp(self, fi):
        base_dir = self._cfg.get("export_dir", os.path.expanduser("~"))
        tmp_dir = os.path.join(base_dir, ".temp_drive")
        os.makedirs(tmp_dir, exist_ok=True)
        fname = re.sub(r'[\\/*?:"<>|]', "", fi["name"])
        fpath = os.path.join(tmp_dir, fname)
        buf = self._drive_mgr.download(fi["id"])
        with open(fpath, "wb") as f:
            f.write(buf.getbuffer())
        return fpath

    def _bg_drive_dl_multi(self, file_list):
        errors=[]; loaded=0
        for fi in file_list:
            try:
                buf = self._drive_mgr.download(fi["id"])
                df_raw = pd.read_csv(buf)
                df, date_str = self._parse_df(df_raw)
                if df is not None:
                    display, color = self._get_color_for_label(fi["name"])
                    self.files_data.append({
                        "label": display,
                        "df_raw":df, "color":color,"date_str":date_str,"path":""})
                    loaded += 1
                else:
                    errors.append(f"❌ {fi['name']}: parse datetime ไม่ได้")
            except Exception as e:
                errors.append(f"❌ {fi['name']}: {e}")
                
        def _update_ui():
            msg = f"✅ โหลดจาก Drive {loaded} ไฟล์"
            if errors: msg += f"  ⚠ {len(errors)} ผิดพลาด"
            self._set_status(msg, C["green"] if not errors else C["amber"])
            if errors: messagebox.showwarning("บางไฟล์มีปัญหา", "\n".join(errors))
            self._refresh_listbox()
            
        self.after(0, _update_ui)

    def _bg_drive_dl_sheet(self, file_list):
        errors = []; loaded = 0
        for fi in file_list:
            try:
                path = self._save_drive_to_temp(fi)
                self._sheet_files.append(path)
                loaded += 1
            except Exception as e:
                errors.append(f"❌ {fi['name']}: {e}")
                
        def _update_ui():
            msg = f"📁 เลือกแล้ว {len(self._sheet_files)} ไฟล์ (จาก Drive สำเร็จ {loaded} ไฟล์)"
            if errors: msg += f"  ⚠ {len(errors)} ผิดพลาด"
            self._sheet_status.configure(text=msg, text_color=C["green"] if not errors else C["amber"])
            if errors:
                messagebox.showwarning("บางไฟล์มีปัญหา", "\n".join(errors))
                
        self.after(0, _update_ui)

    def _bg_drive_dl_merge(self, file_list):
        errors = []; dht_c = 0; pm_c = 0
        for fi in file_list:
            try:
                path = self._save_drive_to_temp(fi)
                fname = fi["name"].lower()
                if 'dht' in fname:
                    self._merge_dht_paths.append(path)
                    dht_c += 1
                else:
                    self._merge_pm_paths.append(path)
                    pm_c += 1
            except Exception as e:
                errors.append(f"❌ {fi['name']}: {e}")
        
        def _update_ui():
            self._merge_dht_label.configure(text=f"📁 เลือกรวมแล้ว {len(self._merge_dht_paths)} ไฟล์", text_color=C["green"])
            self._merge_pm_label.configure(text=f"📁 เลือกรวมแล้ว {len(self._merge_pm_paths)} ไฟล์", text_color=C["green"])
            msg = f"✅ โหลดจาก Drive สำเร็จ: DHT22 = {dht_c}, PM = {pm_c}"
            if errors: msg += f"  ⚠ {len(errors)} ผิดพลาด"
            self._merge_status.configure(text=msg, text_color=C["green"] if not errors else C["amber"])
            if errors: messagebox.showwarning("บางไฟล์มีปัญหา", "\n".join(errors))
            
        self.after(0, _update_ui)

    def _open_firebase(self):
        if not self._fb_mgr:
            messagebox.showwarning("Firebase","ตั้งค่า Firebase ใน Settings ก่อน"); return
        cfg   = self._cfg
        rooms = [r.strip() for r in cfg.get("fb_rooms","").split(",") if r.strip()] or ["Room1"]
        pts   = [p.strip() for p in cfg.get("fb_points","").split(",") if p.strip()] or ["P1"]
        dlg = ctk.CTkToplevel(self); dlg.title("🔥 Firebase → Plot"); dlg.geometry("420x320")
        ctk.CTkLabel(dlg, text="🔥  โหลดจาก Firebase (เพื่อ Plot)",
                     font=ctk.CTkFont(family=FONT, size=FS_LABEL, weight="bold"),
                     text_color=C["orange"]).pack(pady=(14,8))
        rv=ctk.StringVar(value=rooms[0]); pv=ctk.StringVar(value=pts[0])
        sv=ctk.StringVar(value="dust")
        for label,var,vals in [("Room:",rv,rooms),("Point:",pv,pts)]:
            f=ctk.CTkFrame(dlg,fg_color="transparent"); f.pack(pady=4,fill="x",padx=18)
            ctk.CTkLabel(f,text=label,font=ctk.CTkFont(family=FONT,size=FS_BODY),
                         text_color=C["text_soft"]).pack(side="left",padx=6)
            ctk.CTkOptionMenu(f,variable=var,values=vals,
                              fg_color=C["accent"],button_color=C["accent2"],
                              text_color="white",font=ctk.CTkFont(family=FONT,size=FS_BODY)
                              ).pack(side="left",fill="x",expand=True)
        rf=ctk.CTkFrame(dlg,fg_color="transparent"); rf.pack(pady=6)
        ctk.CTkRadioButton(rf,text="Dust Sensor",variable=sv,value="dust",
                            fg_color=C["orange"],font=ctk.CTkFont(family=FONT,size=FS_BODY)
                            ).pack(side="left",padx=12)
        ctk.CTkRadioButton(rf,text="DHT22",variable=sv,value="dht",
                            fg_color=C["teal"],font=ctk.CTkFont(family=FONT,size=FS_BODY)
                            ).pack(side="left",padx=12)
        def do_load():
            base = cfg.get("fb_base_path","SAC")
            path = (f"{base}/DustSensor/{rv.get()}/{pv.get()}" if sv.get()=="dust"
                    else f"{base}/DHT22/{rv.get()}/{pv.get()}")
            dlg.destroy()
            threading.Thread(target=self._bg_fb_load,
                             args=(path,rv.get(),pv.get(),sv.get()),daemon=True).start()
        ctk.CTkButton(dlg,text="🔥  โหลดข้อมูล",fg_color=C["orange"],hover_color="#E65100",
                      text_color="#FFF7ED",height=44,
                      font=ctk.CTkFont(family=FONT,size=FS_LABEL,weight="bold"),
                      command=do_load).pack(pady=14,ipadx=24)

    def _bg_fb_load(self, path, room, point, sensor):
        try:
            df = self._fb_mgr.load_as_df(path)
            if df.empty:
                self.after(0,self._set_status,"ไม่พบข้อมูล Firebase",C["red"]); return
            df2,date_str = self._parse_df(df)
            if df2 is not None:
                raw_name = f"{room}_{point}"
                display, color = self._get_color_for_label(raw_name)
                self.files_data.append({
                    "label": display,
                    "df_raw":df2, "color":color,"date_str":date_str,"path":""})
                self.after(0, self._refresh_listbox)
                self.after(0, self._set_status, f"✅ โหลดจาก Firebase: {path}", C["green"])
        except Exception as e:
            self.after(0, messagebox.showerror, "Firebase Error", str(e))

    def _switch_theme(self):
        self._theme_name = "dark" if self._theme_name=="light" else "light"
        C.update(THEMES[self._theme_name])
        ctk.set_appearance_mode("Dark" if self._theme_name=="dark" else "Light")
        self._set_status(f"Theme: {self._theme_name.capitalize()}", C["green"])

    # ══════════════════════════════════════════════════════════════
    #  PLOT PIPELINE
    # ══════════════════════════════════════════════════════════════
    def _plot_threaded(self):
        if not self.files_data:
            messagebox.showinfo("ยังไม่มีข้อมูล","กรุณาเพิ่มไฟล์ CSV ก่อน"); return
        if self._is_plotting:
            self._set_status("⏳ กำลังวาดอยู่ กรุณารอ...", C["amber"]); return
        tr = self._get_time_range()
        if tr is None: return
        self._is_plotting = True
        self._set_status("⏳ กำลังวาดกราฟ...", C["amber"])
        self._progress.set(0.1)
        threading.Thread(target=self._do_plot, args=(tr,), daemon=True).start()

    def _do_plot(self, time_range):
        try:
            h0, h1     = time_range
            res        = self._resample.get() if self._smooth.get() else None
            opt        = PLOT_OPTIONS[self._plot_type.get()]
            r1_keys    = opt["r1"]; r2_keys = opt["r2"]; show_temp = opt["temp"]
            show_hist  = self._show_hist.get()
            show_heat  = self._show_heat.get()
            show_gap   = self._show_gap.get()
            all_keys   = r1_keys + r2_keys
            total_secs = (h1 - h0) * 3600

            prepared = []
            for item in self.files_data:
                df = item["df_raw"].copy()
                mode_dates = df["Datetime"].dt.date.mode()
                if mode_dates.empty: continue
                day_date = mode_dates[0]
                t0 = datetime.combine(day_date, dtime(h0, 0))
                t1 = (datetime.combine(day_date, dtime(min(h1,23), 59, 59))
                      if h1 < 24 else datetime.combine(day_date, dtime(23, 59, 59)))
                df_s = df[(df["Datetime"] >= t0) & (df["Datetime"] <= t1)].copy()
                if df_s.empty: continue
                df_s = df_s.sort_values("Datetime").set_index("Datetime")
                comp_pct, unique_secs = calc_completeness(df_s, h0, h1)
                n_raw   = len(df_s)
                primary = next((find_key_col(df_s.columns, k) for k in all_keys
                                if find_key_col(df_s.columns, k)), None)
                n_out   = (detect_outliers(df_s[primary])
                           if primary and primary in df_s.columns else 0)
                df_plot = df_s.copy()
                if res:
                    df_plot = df_plot.resample(res).mean(numeric_only=True).interpolate(limit=10)
                prepared.append({
                    "label":       item["label"],
                    "df":          df_plot,
                    "df_raw_s":    df_s,
                    "color":       item["color"],
                    "date_str":    item["date_str"],
                    "day_date":    day_date,
                    "n_raw":       n_raw,
                    "comp_pct":    comp_pct,
                    "unique_secs": unique_secs,
                    "n_out":       n_out,
                })

            if not prepared:
                self.after(0, self._set_status, "ไม่มีข้อมูลในช่วงเวลาที่เลือก", C["red"])
                self.after(0, setattr, self, "_is_plotting", False); return

            self.after(0, self._progress.set, 0.35)

            all_indices = [d["df"].index for d in prepared if not d["df"].empty]
            global_xmin = min(idx.min() for idx in all_indices)

            first_day  = sorted({d["day_date"] for d in prepared})[0]
            last_day   = sorted({d["day_date"] for d in prepared})[-1]
            xlim_start = datetime.combine(first_day, dtime(h0, 0, 0))
            xlim_end   = (
                datetime.combine(last_day, dtime(min(h1, 23), 59, 59))
                if h1 < 24
                else datetime.combine(last_day, dtime(23, 59, 59))
            )
            x0n = mdates.date2num(xlim_start)
            x1n = mdates.date2num(xlim_end)
            total_span_days = (xlim_end - xlim_start).total_seconds() / 86400

            all_days = sorted({d["day_date"] for d in prepared})
            day_boundaries = []
            for dy in all_days:
                bnd = pd.Timestamp(datetime.combine(dy, dtime(h0, 0)))
                if bnd > global_xmin:
                    day_boundaries.append(mdates.date2num(bnd.to_pydatetime()))

            row_specs = []
            if r1_keys:   row_specs.append(("r1",   r1_keys, 5.0))
            if r2_keys:   row_specs.append(("r2",   r2_keys, 4.5))
            if show_temp: row_specs.append(("temp", [],       4.0))
            if show_hist: row_specs.append(("hist", [],       4.0))
            if show_heat: row_specs.append(("heat", [],       3.5))
            if show_gap:  row_specs.append(("gap",  [],       2.0))
            stats_h = max(3.2, 1.2 * len(prepared))
            row_specs.append(("stats", [], stats_h))

            if len(row_specs) <= 1:
                self.after(0, self._set_status, "ไม่มี plot ที่เลือก", C["red"])
                self.after(0, setattr, self, "_is_plotting", False); return

            plt.rcParams.update({"font.family": FONT, "font.size": 12})
            n_rows = len(row_specs); ratios = [s[2] for s in row_specs]
            fig_h  = max(sum(ratios) * 1.20, 10.0)
            try:
                canvas_px = self._scroll_canvas.winfo_width()
                fig_w = max(canvas_px / 96, 14.0)
            except:
                fig_w = 15.0

            fig, axes_list = plt.subplots(n_rows, 1, figsize=(fig_w, fig_h),
                                           gridspec_kw={"height_ratios": ratios},
                                           facecolor=C["plot_bg"])
            if n_rows == 1: axes_list = [axes_list]
            fig.subplots_adjust(left=0.11, right=0.93, top=0.96, bottom=0.03, hspace=0.28)

            date_titles = "  ·  ".join(
                f"{d['label']} [{d['date_str']}]" for d in prepared)
            fig.suptitle(date_titles, fontsize=11, fontweight="bold",
                         color=C["plot_txt"], y=0.99, ha="left", x=0.06)

            ax_map = {tag: ax for (tag, _, _), ax in zip(row_specs, axes_list)}

            def style_ax(ax, title, ylabel, col):
                ax.set_facecolor(C["plot_bg"])
                for side, sp in ax.spines.items():
                    sp.set_visible(side in ("bottom", "left"))
                    sp.set_color(C["border"]); sp.set_linewidth(0.8)
                ax.tick_params(colors=C["plot_txt"], labelsize=10, length=4, width=0.8)
                ax.set_ylabel(ylabel, color=C["plot_txt"], fontsize=11, labelpad=6)
                ax.yaxis.grid(True, color=C["plot_grid"], lw=0.7, alpha=0.9, ls="--")
                ax.xaxis.grid(True, color=C["plot_grid"], lw=0.4, alpha=0.4, ls=":")
                ax.set_axisbelow(True)
                ax.set_xlim(x0n, x1n)
                _apply_xaxis(ax, total_span_days)
                for xb in day_boundaries:
                    ax.axvline(xb, color=C["text_dim"], lw=0.8, alpha=0.5,
                               ls="--", zorder=0)
                ax.text(-0.005, 1.04, title, transform=ax.transAxes,
                        va="bottom", ha="left", color=col,
                        fontsize=12, fontfamily=FONT, fontweight="bold")

            ls_cycle = ["-", "--", "-.", ":"]
            LW = 1.0

            if "r1" in ax_map:
                ax = ax_map["r1"]
                ylbl  = " / ".join(AXIS_LABELS[k] for k in r1_keys if k in AXIS_LABELS)
                title = " + ".join(AXIS_TITLES.get(k, k) for k in r1_keys)
                style_ax(ax, title, ylbl, C["red"])
                for d in prepared:
                    slbl = d['label'][:20] + ("…" if len(d['label']) > 20 else "")
                    for ki, key in enumerate(r1_keys):
                        c = find_key_col(d["df"].columns, key)
                        if c is None: continue
                        s = d["df"][c]; lk = AXIS_LABELS.get(key, key)
                        ax.plot(s.index, s, color=d["color"], lw=LW, alpha=0.90,
                                linestyle=ls_cycle[ki % 4],
                                label=f"{lk} | {slbl} [{d['date_str']}]",
                                solid_capstyle="round")
                        if self._fill_area.get() and ki == 0:
                            ax.fill_between(s.index, s, alpha=0.08, color=d["color"])
                ax.legend(loc="upper left", fontsize=9, framealpha=0.95,
                           facecolor=C["plot_bg"], edgecolor=C["border"],
                           labelcolor=C["plot_txt"], ncol=min(3, max(1, len(prepared))),
                           borderpad=0.6, handlelength=1.8)
                ax.margins(y=0.15)

            if "r2" in ax_map:
                ax = ax_map["r2"]
                ylbl  = " / ".join(AXIS_LABELS[k] for k in r2_keys if k in AXIS_LABELS)
                title = " + ".join(AXIS_TITLES.get(k, k) for k in r2_keys)
                style_ax(ax, title, ylbl, C["accent"])
                ax.yaxis.set_major_formatter(mticker.StrMethodFormatter("{x:,.0f}"))
                for d in prepared:
                    slbl = d['label'][:20] + ("…" if len(d['label']) > 20 else "")
                    for ki, key in enumerate(r2_keys):
                        c = find_key_col(d["df"].columns, key)
                        if c is None: continue
                        s = d["df"][c]; lk = AXIS_LABELS.get(key, key)
                        ax.plot(s.index, s, color=d["color"], lw=LW, alpha=0.90,
                                linestyle=ls_cycle[ki % 4],
                                label=f"{lk} | {slbl} [{d['date_str']}]",
                                solid_capstyle="round")
                        if self._fill_area.get() and ki == 0:
                            ax.fill_between(s.index, s, alpha=0.08, color=d["color"])
                ax.legend(loc="upper left", fontsize=9, framealpha=0.95,
                           facecolor=C["plot_bg"], edgecolor=C["border"],
                           labelcolor=C["plot_txt"], ncol=min(3, max(1, len(prepared))),
                           borderpad=0.6, handlelength=1.8)
                ax.margins(y=0.15)

            if "temp" in ax_map:
                ax = ax_map["temp"]
                style_ax(ax, "Temperature (°C)  /  Humidity (%RH)", "°C", C["amber"])
                for d in prepared:
                    slbl = d['label'][:20] + ("…" if len(d['label']) > 20 else "")
                    tc = find_key_col(d["df"].columns, "temp")
                    hc = find_key_col(d["df"].columns, "hum")
                    if tc:
                        ax.plot(d["df"].index, d["df"][tc], color=d["color"], lw=LW,
                                label=f"Temp | {slbl} [{d['date_str']}]",
                                solid_capstyle="round")
                    if hc:
                        ax2 = ax.twinx()
                        ax2.plot(d["df"].index, d["df"][hc], color=d["color"],
                                  lw=LW, linestyle="--", alpha=0.70,
                                  label=f"Hum | {slbl}")
                        ax2.set_ylabel("%RH", color=C["purple"], fontsize=11)
                        ax2.tick_params(axis="y", colors=C["purple"], labelsize=10)
                        ax2.set_ylim(0, 105)
                        for sp in ax2.spines.values(): sp.set_visible(False)
                ax.legend(loc="upper left", fontsize=10, framealpha=0.95,
                           facecolor=C["plot_bg"], edgecolor=C["border"],
                           labelcolor=C["plot_txt"])
                ax.margins(y=0.15)

            if "hist" in ax_map and prepared:
                ax = ax_map["hist"]
                ax.set_facecolor(C["plot_bg"])
                for sp in ax.spines.values(): sp.set_visible(False)
                ax.tick_params(colors=C["plot_txt"], labelsize=9.5)
                ax.set_xlabel("Concentration", color=C["plot_txt"], fontsize=10)
                ax.set_ylabel("Count", color=C["plot_txt"], fontsize=10)
                ax.yaxis.grid(True, color=C["plot_grid"], lw=0.5, alpha=0.5, ls="--")
                ax.set_axisbelow(True)
                ax.text(-0.005, 1.04, "Distribution (Histogram)", transform=ax.transAxes,
                        va="bottom", ha="left", color=C["purple"], fontsize=10.5,
                        fontfamily=FONT, fontweight="bold")
                for d in prepared:
                    for key in all_keys:
                        c = find_key_col(d["df_raw_s"].columns, key)
                        if c is None: continue
                        vals = d["df_raw_s"][c].dropna()
                        ax.hist(vals, bins=40, color=d["color"], alpha=0.45,
                                label=f"{AXIS_LABELS.get(key,key)} | {d['label']}",
                                edgecolor="none", rwidth=0.9)
                        ax.axvline(vals.mean(), color=d["color"], lw=1.2, ls="--", alpha=0.8)
                ax.legend(loc="upper right", fontsize=9, framealpha=0.92,
                           facecolor=C["plot_bg"], edgecolor=C["plot_grid"],
                           labelcolor=C["plot_txt"])

            if "heat" in ax_map and prepared:
                ax = ax_map["heat"]
                ax.set_facecolor(C["plot_bg"])
                for sp in ax.spines.values():
                    sp.set_color(C["plot_grid"]); sp.set_linewidth(0.6)
                ax.text(-0.005, 1.04, "Heatmap (hour × 10-min) — File 1",
                        transform=ax.transAxes, va="bottom", ha="left",
                        color=C["teal"], fontsize=10.5, fontfamily=FONT, fontweight="bold")
                d0   = prepared[0]["df_raw_s"]
                pm_c = next((find_key_col(d0.columns, k) for k in all_keys
                             if find_key_col(d0.columns, k)), None)
                if pm_c and pm_c in d0.columns:
                    ts = d0.index; hrs = ts.hour; mins = ts.minute // 10
                    grid = np.full((24, 6), np.nan)
                    for h, m, v in zip(hrs, mins, d0[pm_c].values):
                        if 0 <= h < 24 and 0 <= m < 6: grid[h, m] = v
                    cmap_h = mcolors.LinearSegmentedColormap.from_list(
                        "aq", ["#F0FDF4","#86EFAC","#FDE68A","#FB923C","#EF4444","#7C3AED"])
                    im = ax.imshow(grid, aspect="auto", origin="upper", cmap=cmap_h,
                                    interpolation="nearest", extent=[-0.5, 5.5, 23.5, -0.5])
                    ax.set_yticks(range(0, 24, 2))
                    ax.set_yticklabels([f"{h:02d}:00" for h in range(0, 24, 2)],
                                        color=C["plot_txt"], fontsize=8.5)
                    ax.set_xticks(range(6))
                    ax.set_xticklabels([f":{m*10:02d}" for m in range(6)],
                                        color=C["plot_txt"], fontsize=9.5)
                    ax.set_xlabel("10-minute interval", color=C["plot_txt"], fontsize=10)
                    ax.set_ylabel("Hour", color=C["plot_txt"], fontsize=10)
                    ax.tick_params(colors=C["plot_txt"], length=2)
                    cb = fig.colorbar(im, ax=ax, pad=0.015, fraction=0.010, aspect=26)
                    cb.ax.tick_params(labelsize=8, colors=C["plot_txt"])
                    cb.outline.set_edgecolor(C["plot_grid"])

            if "gap" in ax_map:
                ax = ax_map["gap"]
                ax.set_facecolor(C["plot_bg"])
                for sp in ax.spines.values(): sp.set_visible(False)
                ax.text(-0.005, 1.14, "Data Completeness / Gap Analysis",
                        transform=ax.transAxes, va="bottom", ha="left",
                        color=C["green"], fontsize=10.5, fontfamily=FONT, fontweight="bold")
                ax.set_yticks([]); ax.xaxis.grid(False); ax.yaxis.grid(False)
                ax.set_xlim(x0n, x1n)
                _apply_xaxis(ax, total_span_days)
                ax.tick_params(axis="x", colors=C["plot_txt"], labelsize=10)
                for xb in day_boundaries:
                    ax.axvline(xb, color=C["text_dim"], lw=0.8, alpha=0.5, ls="--")
                n_p = max(len(prepared), 1)
                for idx, d in enumerate(prepared):
                    xn  = mdates.date2num(d["df"].index.to_pydatetime())
                    y_c = 0.12 + idx * 0.82 / n_p; y_h = 0.65 / n_p
                    if len(xn) > 1:
                        diffs = np.diff(xn) * 86400; seg_s = xn[0]
                        for i2 in range(1, len(xn)):
                            if diffs[i2-1] > 180:
                                ax.broken_barh([(seg_s, xn[i2-1] - seg_s)],
                                                (y_c, y_h), facecolors=d["color"],
                                                alpha=0.75, linewidth=0)
                                seg_s = xn[i2]
                        ax.broken_barh([(seg_s, xn[-1] - seg_s)],
                                        (y_c, y_h), facecolors=d["color"],
                                        alpha=0.75, linewidth=0)
                        ax.text(x1n + (x1n-x0n)*0.003, y_c + y_h/2, d["label"][:24],
                                color=d["color"], fontsize=9, va="center", clip_on=False)
                ax.set_ylim(0, 1)

            if "stats" in ax_map:
                ax = ax_map["stats"]
                ax.set_facecolor(C["card_bg"])
                for sp in ax.spines.values():
                    sp.set_visible(True); sp.set_color(C["plot_grid"]); sp.set_linewidth(0.5)
                ax.set_xticks([]); ax.set_yticks([])
                ax.text(-0.002, 1.10,
                    f"📊  Data Quality Statistics  |  {h0:02d}:00 – {h1:02d}:00"
                    f"  =  {total_secs:,} วินาที  (100%)",
                    transform=ax.transAxes, va="bottom", ha="left",
                    color=C["accent"], fontsize=11, fontfamily=FONT, fontweight="bold")

                col_x    = [0.005, 0.22, 0.35, 0.50, 0.645, 0.755, 0.865]
                col_hdrs = ["ไฟล์ / สถานี", "วันที่", "Records (raw)",
                            f"Unique-sec / {total_secs:,}", "Complete %",
                            "Missing %", "Outliers (IQR)"]
                for xi, h_txt in zip(col_x, col_hdrs):
                    ax.text(xi, 0.93, h_txt, transform=ax.transAxes,
                            color=C["accent"], fontsize=9, fontfamily=FONT,
                            fontweight="bold", va="top")
                ax.axhline(0.84, color=C["plot_grid"], lw=0.9)

                n_f   = len(prepared)
                row_h = min(0.78 / max(n_f, 1), 0.40)
                bar_w = 0.855

                for ri, d in enumerate(prepared):
                    y_top  = 0.83 - ri * row_h
                    comp   = d["comp_pct"]; miss = max(0.0, 100.0 - comp)
                    barcol = C["green"] if comp >= 95 else (C["amber"] if comp >= 75 else C["red"])
                    slbl   = d['label'][:26] + ("…" if len(d['label']) > 26 else "")

                    row_data = [
                        (col_x[0], f"● {slbl}",                           d["color"],    True),
                        (col_x[1], d["date_str"],                          C["text_soft"],False),
                        (col_x[2], f"{d['n_raw']:,}",                      C["text_soft"],False),
                        (col_x[3], f"{d['unique_secs']:,}/{total_secs:,}", C["text_soft"],False),
                        (col_x[4], f"{comp:.2f}%",                         barcol,        True),
                        (col_x[5], f"{miss:.2f}%",
                         C["red"] if miss > 5 else C["text_dim"],          False),
                        (col_x[6], str(d["n_out"]),
                         C["purple"] if d["n_out"] > 0 else C["text_dim"], False),
                    ]
                    for xi, txt, col, bold in row_data:
                        ax.text(xi, y_top, txt, transform=ax.transAxes,
                                color=col, fontsize=9.5, fontfamily=FONT,
                                fontweight="bold" if bold else "normal", va="top")

                    bar_y  = y_top - row_h * 0.60
                    bar_ht = row_h * 0.28
                    ax.barh(bar_y, bar_w, height=bar_ht, left=col_x[0],
                             color=C["plot_grid"], alpha=0.30,
                             transform=ax.transAxes, clip_on=False, zorder=0)
                    ax.barh(bar_y, bar_w * comp / 100, height=bar_ht, left=col_x[0],
                             color=barcol, alpha=0.38,
                             transform=ax.transAxes, clip_on=False, zorder=1)

                    if ri < n_f - 1:
                        ax.axhline(y_top - row_h + 0.01,
                                   color=C["plot_grid"], lw=0.5, alpha=0.5)

                ax.set_ylim(0, 1)

            self.after(0, self._progress.set, 0.85)
            self.after(0, self._render_canvas, fig)

            info = (f"🕒 ช่วงเวลา: {h0:02d}:00–{h1:02d}:00 ({total_secs:,} วินาที)\n"
                    f"📁 โหลดทั้งหมด: {len(prepared)} ไฟล์\n"
                    f"{'='*38}\n")
                    
            for d in prepared:
                comp = d['comp_pct']
                status_txt = "✅ ครบถ้วน" if comp >= 95 else ("⚠️ ขาดหายบางส่วน" if comp >= 75 else "❌ ข้อมูลแหว่งเยอะ")
                
                info += (f"📌 {d['label']} [{d['date_str']}]\n"
                         f"   ├ สถานะ: {status_txt} (Completeness {comp:.1f}%)\n"
                         f"   ├ ข้อมูล: {d['n_raw']:,} แถว | Unique: {d['unique_secs']:,} วิ\n"
                         f"   └ Outliers (ตรวจเจอ): {d['n_out']:,} จุด\n\n")

            self.after(0, self._set_info, info)
            self.after(0, self._set_status, f"✅ เสร็จ ({len(prepared)} ไฟล์)", C["green"])
            self.after(2500, self._progress.set, 0)

        except Exception as e:
            import traceback; traceback.print_exc()
            self.after(0, self._set_status, f"❌ {str(e)[:60]}", C["red"])
            self.after(0, messagebox.showerror, "Plot Error", str(e))
            self.after(0, self._progress.set, 0)
        finally:
            self.after(0, setattr, self, "_is_plotting", False)

    def _render_canvas(self, fig):
        if self._current_fig:
            try:
                self._current_fig.clf() # ล้างหน่วยความจำกราฟเก่า
                plt.close(self._current_fig)
            except: pass
        self._current_fig = fig

        for w in self._chart_frame.winfo_children(): w.destroy()
        toolbar_f = tk.Frame(self._chart_frame, bg=C["card_bg"], height=34)
        toolbar_f.pack(side="top", fill="x")

        cv = FigureCanvasTkAgg(fig, master=self._chart_frame)

        _artists     = [a for ax in fig.axes for a in list(ax.lines) + list(ax.collections)]
        _tgt_alphas  = []
        for a in _artists:
            _tgt_alphas.append(a.get_alpha() or 1.0)
            a.set_alpha(0.0)

        STEPS = 22; MS = 14
        def _fade(step):
            if step > STEPS:
                for a, ta in zip(_artists, _tgt_alphas): a.set_alpha(ta)
                cv.draw_idle(); return
            t = step / STEPS
            ease = 1.0 - (1.0 - t) ** 3
            for a, ta in zip(_artists, _tgt_alphas): a.set_alpha(ease * ta)
            cv.draw_idle()
            self.after(MS, _fade, step + 1)

        cv.draw()
        dpi = fig.get_dpi(); fw, fh = fig.get_size_inches()
        widget = cv.get_tk_widget()
        widget.config(width=int(fw * dpi), height=int(fh * dpi))
        widget.pack(side="top", fill="both", expand=True)

        tb = NavigationToolbar2Tk(cv, toolbar_f)
        try:
            tb.config(background=C["card_bg"])
            for ch in tb.winfo_children():
                try: ch.config(bg=C["card_bg"], fg=C["text_soft"],
                               activebackground=C["border"], relief="flat")
                except: pass
        except: pass
        tb.update()

        self.after(80,  lambda: self._scroll_canvas.yview_moveto(0))
        self.after(100, _fade, 0)
        self._progress.set(1.0)

# ══════════════════════════════════════════════════════════════════════
    #  TAB 3: SUMMARY SHEETS (ย้ายไป Background Thread เพื่อความเสถียร)
    # ══════════════════════════════════════════════════════════════════════
    def _build_sheets_tab(self, tab):
        tab.configure(fg_color=C["main_bg"])
        body = ctk.CTkFrame(tab, corner_radius=12, fg_color=C["card_bg"])
        body.pack(fill="both", expand=True, padx=20, pady=20)

        ctk.CTkLabel(body, text="📊 สรุปสถิติรายวัน (Daily Summary Sheets)",
                     font=ctk.CTkFont(family=FONT, size=FS_TITLE, weight="bold"),
                     text_color=C["accent"]).pack(pady=(20, 10))

        self._sheet_files = []

        def _select_local():
            files = filedialog.askopenfilenames(title="เลือกไฟล์ CSV (เลือกได้หลายไฟล์)", filetypes=[("CSV","*.csv")])
            if files:
                self._sheet_files.extend(files)
                self._sheet_status.configure(text=f"📁 เลือกแล้ว {len(self._sheet_files)} ไฟล์", text_color=C["green"])

        def _select_gdrive():
            self._open_drive(mode="sheet")

        row_btn = ctk.CTkFrame(body, fg_color="transparent")
        row_btn.pack(pady=10)
        ctk.CTkButton(row_btn, text="📂 เลือกไฟล์ (Local)", width=160, height=40,
                      font=ctk.CTkFont(family=FONT, size=FS_BODY, weight="bold"), fg_color=C["teal"],
                      command=_select_local).pack(side="left", padx=5)
        ctk.CTkButton(row_btn, text="☁️ นำเข้าจาก GDrive", width=160, height=40,
                      font=ctk.CTkFont(family=FONT, size=FS_BODY, weight="bold"), fg_color="#4285F4",
                      command=_select_gdrive).pack(side="left", padx=5)
        ctk.CTkButton(row_btn, text="🗑️ ล้างรายการ", width=100, height=40, fg_color=C["red"],
                      command=lambda: [self._sheet_files.clear(), self._sheet_status.configure(text="ยังไม่ได้เลือกไฟล์", text_color=C["text_soft"])]).pack(side="left", padx=5)

        self._sheet_status = ctk.CTkLabel(body, text="ยังไม่ได้เลือกไฟล์", text_color=C["text_soft"], font=ctk.CTkFont(family=FONT, size=FS_BODY))
        self._sheet_status.pack(pady=10)

        ctk.CTkButton(body, text="⚙️ ประมวลผลและสร้าง Summary", height=55,
                      font=ctk.CTkFont(family=FONT, size=FS_TITLE, weight="bold"),
                      fg_color=C["accent"], hover_color=C["accent2"], command=self._sheet_process_files).pack(pady=20)

    def _sheet_process_files(self):
        if not hasattr(self, '_sheet_files') or not self._sheet_files:
            messagebox.showwarning("คำเตือน", "กรุณากดเลือกไฟล์ CSV เข้ามาก่อนครับ!")
            return
            
        self._sheet_status.configure(text="⏳ กำลังประมวลผล กรุณารอซักครู่... (รันอยู่เบื้องหลัง)", text_color=C["amber"])
        threading.Thread(target=self._bg_sheet_process, daemon=True).start()

    def _bg_sheet_process(self):
        all_data_frames = []
        for path in self._sheet_files:
            try:
                try: df = pd.read_csv(path, encoding='utf-8-sig', low_memory=False)
                except UnicodeDecodeError: df = pd.read_csv(path, encoding='cp874', low_memory=False)
                
                df_parsed, _ = self._parse_df(df, path)
                
                if df_parsed is not None and not df_parsed.empty:
                    df_parsed['datetime_parsed'] = df_parsed['Datetime']
                    filename = os.path.basename(path)
                    name_no_ext = os.path.splitext(filename)[0]
                    room_name = re.sub(r'_?\d{2}-\d{2}-\d{4}.*', '', name_no_ext)
                    df_parsed['Room'] = room_name if room_name else name_no_ext
                    all_data_frames.append(df_parsed)
                else:
                    print(f"⚠️ ข้ามไฟล์ {os.path.basename(path)} แปลงเวลาไม่ได้ หรือข้อมูลว่างเปล่า")
            except Exception as e:
                print(f"❌ ไม่สามารถอ่านไฟล์ {os.path.basename(path)} ได้เนื่องจาก: {e}")

        if not all_data_frames:
            def _err():
                messagebox.showerror("ข้อผิดพลาด", "ไม่พบข้อมูลที่สามารถประมวลผลได้")
                self._sheet_status.configure(text="❌ ประมวลผลล้มเหลว: ไม่พบข้อมูล", text_color=C["red"])
            self.after(0, _err)
            return

        combined_df = pd.concat(all_data_frames, ignore_index=True)
        combined_df = combined_df.drop_duplicates()

        combined_df['date_obj'] = combined_df['datetime_parsed'].dt.date

        expected_rows_per_day = 86400
        row_counts = combined_df.groupby(['Room', 'date_obj']).size().reset_index(name='actual_rows')
        row_counts['Completeness (%)'] = ((row_counts['actual_rows'] / expected_rows_per_day) * 100).round(1).astype(str) + '%'

        pc01_c = find_key_col(combined_df.columns, "pc01")
        pm25_c = find_key_col(combined_df.columns, "pm25")
        temp_c = find_key_col(combined_df.columns, "temp")
        hum_c  = find_key_col(combined_df.columns, "hum")

        agg_dict = {}
        if pc01_c: agg_dict[pc01_c] = ['min', 'max', 'median', 'mean', 'std', 'skew', pd.Series.kurt]
        if pm25_c: agg_dict[pm25_c] = ['min', 'max', 'median', 'mean', 'std', 'skew', pd.Series.kurt]
        if temp_c: agg_dict[temp_c] = ['min', 'max', 'median', 'mean', 'std']
        if hum_c:  agg_dict[hum_c]  = ['min', 'max', 'median', 'mean', 'std']

        if not agg_dict:
            def _err2():
                messagebox.showerror("ข้อผิดพลาด", "ไม่พบคอลัมน์ข้อมูลสภาพอากาศ (PC0.1, PM2.5, Temp, Humid)")
                self._sheet_status.configure(text="❌ ประมวลผลล้มเหลว", text_color=C["red"])
            self.after(0, _err2)
            return

        stats = combined_df.groupby(['Room', 'date_obj']).agg(agg_dict).reset_index()

        flat_cols = ['Room', 'date_obj']
        if pc01_c: flat_cols.extend([f"PC01_{m}" for m in ['Min', 'Max', 'Median', 'Mean', 'SD', 'Skewness', 'Kurtosis']])
        if pm25_c: flat_cols.extend([f"Pm25_{m}" for m in ['Min', 'Max', 'Median', 'Mean', 'SD', 'Skewness', 'Kurtosis']])
        if temp_c: flat_cols.extend([f"temp_{m}" for m in ['Min', 'Max', 'Median', 'Mean', 'SD']])
        if hum_c:  flat_cols.extend([f"humid_{m}" for m in ['Min', 'Max', 'Median', 'Mean', 'SD']])

        stats.columns = flat_cols
        numeric_metrics = flat_cols[2:]
        stats[numeric_metrics] = stats[numeric_metrics].round(2)
        stats = pd.merge(stats, row_counts[['Room', 'date_obj', 'Completeness (%)']], on=['Room', 'date_obj'], how='left')
        stats.sort_values(by=['Room', 'date_obj'], ascending=[True, True], inplace=True)
        stats['Date'] = pd.to_datetime(stats['date_obj']).dt.strftime('%d-%m-%Y')

        stats['note'] = ""
        final_order = ['Room', 'Date', 'Completeness (%)'] + ['note'] + numeric_metrics
        stats = stats[final_order]

        def _prompt_save():
            first_room = stats['Room'].iloc[0] if not stats.empty else "data"
            default_save_name = f"summary_multiroom_{first_room}.csv"
            save_path = filedialog.asksaveasfilename(
                title="บันทึกไฟล์สรุปผลข้อมูล", defaultextension=".csv",
                filetypes=[("CSV Files", "*.csv")], initialfile=default_save_name
            )
            if save_path:
                try:
                    stats.to_csv(save_path, index=False, encoding='utf-8-sig')
                    messagebox.showinfo("สำเร็จ!", f"ประมวลผลสถิติแยกห้องเรียบร้อยแล้วที่:\n{save_path}")
                    self._sheet_status.configure(text="✨ ประมวลผลและบันทึกข้อมูลสำเร็จเรียบร้อย!", text_color=C["green"])
                except Exception as e:
                    messagebox.showerror("ข้อผิดพลาด", f"บันทึกไฟล์ล้มเหลว: {e}")
                    self._sheet_status.configure(text="❌ บันทึกไฟล์ล้มเหลว", text_color=C["red"])
            else:
                self._sheet_status.configure(text="⚠️ ยกเลิกการบันทึกไฟล์", text_color=C["amber"])

        self.after(0, _prompt_save)
            
# ══════════════════════════════════════════════════════════════════════
    #  TAB 4: MERGE CSV (ย้ายไป Background Thread และเพิ่ม dtype=str กันแรมกระชาก)
    # ══════════════════════════════════════════════════════════════════════
    def _build_merge_tab(self, tab):
        tab.configure(fg_color=C["main_bg"])
        body = ctk.CTkFrame(tab, corner_radius=12, fg_color=C["card_bg"])
        body.pack(fill="both", expand=True, padx=20, pady=20)

        ctk.CTkLabel(body, text="🔄 ระบบรวมไฟล์ DHT22 และ PM (Multi-File Merge)",
                     font=ctk.CTkFont(family=FONT, size=FS_TITLE, weight="bold"),
                     text_color=C["accent"]).pack(pady=(20, 10))

        self._merge_dht_paths = []
        self._merge_pm_paths = []

        def _select_gdrive_all():
            self._open_drive(mode="merge")
            
        def _select_dht_local():
            files = filedialog.askopenfilenames(title="เลือกไฟล์ DHT22", filetypes=[("CSV","*.csv")])
            if files:
                self._merge_dht_paths.extend(files)
                self._merge_dht_label.configure(text=f"📁 เลือกรวมแล้ว {len(self._merge_dht_paths)} ไฟล์", text_color=C["green"])

        def _select_pm_local():
            files = filedialog.askopenfilenames(title="เลือกไฟล์ PM", filetypes=[("CSV","*.csv")])
            if files:
                self._merge_pm_paths.extend(files)
                self._merge_pm_label.configure(text=f"📁 เลือกรวมแล้ว {len(self._merge_pm_paths)} ไฟล์", text_color=C["green"])

        ctk.CTkButton(body, text="☁️ นำเข้าจาก GDrive (ระบบจะค้นหาและแยกไฟล์ให้อัตโนมัติ)", height=45,
                      font=ctk.CTkFont(family=FONT, size=FS_BODY, weight="bold"), fg_color="#4285F4",
                      command=_select_gdrive_all).pack(fill="x", padx=40, pady=(0, 15))

        # Row DHT (Local)
        row_dht = ctk.CTkFrame(body, fg_color="transparent")
        row_dht.pack(fill="x", padx=40, pady=5)
        ctk.CTkButton(row_dht, text="📂 เลือก DHT22 เพิ่ม (Local)", width=180, height=35,
                      font=ctk.CTkFont(family=FONT, size=FS_BODY), fg_color=C["teal"],
                      command=_select_dht_local).pack(side="left", padx=(0, 15))
        self._merge_dht_label = ctk.CTkLabel(row_dht, text="ยังไม่ได้เลือกไฟล์ DHT22", text_color=C["text_soft"], font=ctk.CTkFont(family=FONT, size=FS_BODY))
        self._merge_dht_label.pack(side="left")

        # Row PM (Local)
        row_pm = ctk.CTkFrame(body, fg_color="transparent")
        row_pm.pack(fill="x", padx=40, pady=5)
        ctk.CTkButton(row_pm, text="📂 เลือก PM เพิ่ม (Local)", width=180, height=35,
                      font=ctk.CTkFont(family=FONT, size=FS_BODY), fg_color=C["orange"],
                      command=_select_pm_local).pack(side="left", padx=(0, 15))
        self._merge_pm_label = ctk.CTkLabel(row_pm, text="ยังไม่ได้เลือกไฟล์ PM", text_color=C["text_soft"], font=ctk.CTkFont(family=FONT, size=FS_BODY))
        self._merge_pm_label.pack(side="left")

        ctk.CTkButton(body, text="🗑️ ล้างรายการที่เลือก", width=120, height=30, fg_color=C["red"],
                      command=lambda: [self._merge_dht_paths.clear(), self._merge_pm_paths.clear(), 
                                       self._merge_dht_label.configure(text="ยังไม่ได้เลือกไฟล์ DHT22", text_color=C["text_soft"]),
                                       self._merge_pm_label.configure(text="ยังไม่ได้เลือกไฟล์ PM", text_color=C["text_soft"]),
                                       self._merge_status.configure(text="พร้อมทำงาน", text_color=C["text_soft"])]).pack(pady=15)

        ctk.CTkButton(body, text="⚙️ รวมไฟล์ (Merge)", height=55,
                      font=ctk.CTkFont(family=FONT, size=FS_TITLE, weight="bold"),
                      fg_color=C["accent"], hover_color=C["accent2"], command=self._process_merge).pack(pady=20)
        
        self._merge_status = ctk.CTkLabel(body, text="พร้อมทำงาน", text_color=C["text_soft"], font=ctk.CTkFont(family=FONT, size=FS_BODY))
        self._merge_status.pack(pady=5)

    def _process_merge(self):
        if not self._merge_dht_paths or not self._merge_pm_paths:
            messagebox.showwarning("คำเตือน", "กรุณาเลือกไฟล์ให้ครบทั้ง DHT22 และ PM อย่างน้อยฝั่งละ 1 ไฟล์ครับ")
            return

        import os
        first_pm_name = os.path.basename(self._merge_pm_paths[0])
        default_save_name = f"merge_{first_pm_name}"

        save_path = filedialog.asksaveasfilename(
            title="บันทึกไฟล์ที่รวมแล้ว", defaultextension=".csv",
            filetypes=[("CSV Files", "*.csv")], initialfile=default_save_name
        )
        if not save_path: return

        self._merge_status.configure(text="⏳ กำลังอ่านและรวมข้อมูลรันอยู่เบื้องหลัง...", text_color=C["amber"])
        threading.Thread(target=self._bg_process_merge, args=(save_path,), daemon=True).start()

    def _bg_process_merge(self, save_path):
        try:
            dht_frames = []
            for path in self._merge_dht_paths:
                try: df = pd.read_csv(path, encoding='utf-8-sig', dtype=str, on_bad_lines='skip')
                except UnicodeDecodeError: df = pd.read_csv(path, encoding='cp874', dtype=str, on_bad_lines='skip')
                df.rename(columns=lambda x: 'Date' if str(x).strip().lower() == 'date' else ('Time' if str(x).strip().lower() == 'time' else str(x).strip()), inplace=True)
                dht_frames.append(df)
            
            df_dht_all = pd.concat(dht_frames, ignore_index=True)
            df_dht_all.drop_duplicates(subset=['Date', 'Time'], inplace=True) 

            pm_frames = []
            for path in self._merge_pm_paths:
                try: df = pd.read_csv(path, encoding='utf-8-sig', dtype=str)
                except UnicodeDecodeError: df = pd.read_csv(path, encoding='cp874', dtype=str)
                df.rename(columns=lambda x: 'Date' if str(x).strip().lower() == 'date' else ('Time' if str(x).strip().lower() == 'time' else str(x).strip()), inplace=True)
                pm_frames.append(df)
                
            df_pm_all = pd.concat(pm_frames, ignore_index=True)
            df_pm_all.drop_duplicates(subset=['Date', 'Time'], inplace=True)

            df_merged = pd.merge(df_dht_all, df_pm_all, on=['Date', 'Time'], how='inner')
            df_merged['datetime'] = df_merged['Date'].str.replace('/', '-') + '-' + df_merged['Time'].str.replace(':', '-')

            rename_dict = {}
            for col in df_merged.columns:
                c_low = str(col).lower()
                if 'hum' in c_low: rename_dict[col] = 'humidity'
                elif 'temp' in c_low: rename_dict[col] = 'temperature'
                elif col == 'PC0.1': rename_dict[col] = 'PC0_1'
                elif col == 'PC0.3': rename_dict[col] = 'PC0_3'
                elif col == 'PC0.5': rename_dict[col] = 'PC0_5'
                elif col == 'PC1.0': rename_dict[col] = 'PC1_0'
                elif col == 'PC2.5': rename_dict[col] = 'PC2_5'
                elif col == 'PC5.0': rename_dict[col] = 'PC5_0'
                elif col == 'PM0.1': rename_dict[col] = 'PM0_1'
                elif col == 'PM0.3': rename_dict[col] = 'PM0_3'
                elif col == 'PM0.5': rename_dict[col] = 'PM0_5'
                elif col == 'PM1.0': rename_dict[col] = 'PM1_0'
                elif col == 'PM2.5': rename_dict[col] = 'PM2_5'
                elif col == 'PM5.0': rename_dict[col] = 'PM5_0'
                
            df_merged.rename(columns=rename_dict, inplace=True)

            target_cols = [
                'datetime', 'humidity', 'temperature', 
                'PC0_1', 'PC0_3', 'PC0_5', 'PC10', 'PC1_0', 'PC2_5', 'PC5_0', 
                'PM0_1', 'PM0_3', 'PM0_5', 'PM10', 'PM1_0', 'PM2_5', 'PM5_0'
            ]
            available_cols = [c for c in target_cols if c in df_merged.columns]
            df_final = df_merged[available_cols]
            
            # 🟢 เรียงข้อมูลเวลาจากน้อยไปมาก 100% ก่อนเขียนไฟล์
            if not df_final.empty and 'datetime' in df_final.columns:
                df_final['_dt'] = pd.to_datetime(df_final['datetime'], format="%d-%m-%Y-%H-%M-%S", errors='coerce')
                df_final = df_final.sort_values('_dt').drop(columns=['_dt'])
            
            df_final.to_csv(save_path, index=False, encoding='utf-8-sig')

            def _success():
                self._merge_status.configure(text=f"✅ รวมสำเร็จ: {os.path.basename(save_path)}", text_color=C["green"])
                messagebox.showinfo("สำเร็จ!", f"รวมไฟล์ทั้งหมดเรียบร้อยแล้วที่:\n{save_path}")
            self.after(0, _success)

        except Exception as e:
            error_message = str(e)  # Store the error message in a separate variable
            def _error(msg=error_message): # Bind it as a default argument
                self._merge_status.configure(text="❌ เกิดข้อผิดพลาด!", text_color=C["red"])
                messagebox.showerror("Error", f"ไม่สามารถรวมไฟล์ได้:\n{msg}")
            self.after(0, _error)
            
# ══════════════════════════════════════════════════════════════════════
if __name__ == "__main__":
    app = DustMonitorApp()
    app.mainloop()