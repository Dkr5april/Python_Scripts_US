# ======================================================
#            KP MASTER ENGINE (UNIFIED V86)
# ======================================================

import swisseph as swe
import os, time
from datetime import datetime, timedelta
from collections import Counter
from pynput import keyboard
from rich.live import Live
from rich.table import Table
from rich.console import Console
from rich.layout import Layout
from rich.panel import Panel
from rich.text import Text
import pandas as pd

# ================= USER CONTROL PANEL =================
MODE = "EXCEL"        # "DASHBOARD" or "EXCEL"
DOB  = "05/04/1979"   
TOB  = "16:55:00"     
PLACE = "Guntur, India" 
LAT, LON = 16.12, 80.93 # Manual Override for reliability

START_DT = datetime(2026, 1, 8, 0, 0)
END_DT   = datetime(2026, 1, 9, 0, 0)
FREQ = "1h" # Adjust based on need

EXPORT_ONLY_DASHA_CHANGES = False
OUT_FILE = "KP_MASTER_OUTPUT.xlsx"

# ==================== CONSTANTS =======================
YEAR_LEN = 365.2425
swe.set_ephe_path("./ephe")
swe.set_sid_mode(swe.SIDM_KRISHNAMURTI)
console = Console()

PLANET_LIT = ["Ke","Ve","Su","Mo","Ma","Ra","Ju","Sa","Me"]
DASHA_YEARS = [7,20,6,10,7,18,16,19,17]
RASHI_OWNERS = {0:"Ma",1:"Ve",2:"Me",3:"Mo",4:"Su",5:"Me",6:"Ve",7:"Ma",8:"Ju",9:"Sa",10:"Sa",11:"Ju"}
SUB_DIVS = DASHA_YEARS.copy()

HOUSE_COLORS = {1:"green",2:"green",3:"green",6:"green",10:"green",11:"green",8:"red",12:"red",4:"orange3",5:"orange3",7:"orange3",9:"orange3"}
ASPECT_WEIGHTS = {"Conj":3.0,"Oppo":2.5,"Squa":2.0,"Trin":1.5,"Sext":1.0,"SSxt":0.5,"SSqu":0.5,"Quin":0.5,"Qnt":0.5,"Sesq":0.5}
ALL_ASPECTS = [(0,"Conj"),(60,"Sext"),(90,"Squa"),(120,"Trin"),(180,"Oppo"),(30,"SSxt"),(45,"SSqu"),(150,"Quin"),(72,"Qnt"),(135,"Sesq")]

# ==================== KP ENGINE CORE =====================
class KPEngine:
    def __init__(self, dob, tob, lat, lon):
        self.lat, self.lon = lat, lon
        self.view_date = START_DT
        d, m, y = map(int, dob.split("/"))
        hh, mm, ss = map(int, tob.split(":"))
        self.njd = swe.julday(y, m, d, hh+mm/60+ss/3600-5.5)
        self.refresh()

    def refresh(self):
        flag = swe.FLG_SWIEPH | swe.FLG_SIDEREAL
        self.n_pos, self.t_pos = {}, {}
        t_jd = swe.julday(self.view_date.year, self.view_date.month, self.view_date.day, self.view_date.hour+self.view_date.minute/60-5.5)

        for pid, nm in [(0,"Su"),(1,"Mo"),(2,"Me"),(3,"Ve"),(4,"Ma"),(5,"Ju"),(6,"Sa"),(11,"Ra")]:
            self.n_pos[nm] = swe.calc_ut(self.njd, pid, flag)[0][0]
            self.t_pos[nm] = swe.calc_ut(t_jd, pid, flag)[0][0]

        self.n_pos["Ke"] = (self.n_pos["Ra"]+180)%360
        self.t_pos["Ke"] = (self.t_pos["Ra"]+180)%360
        self.cusps = swe.houses_ex(self.njd, self.lat, self.lon, b'P', flag)[0]
        self.p_to_h = {p: self.house(lon) for p, lon in self.n_pos.items()}
        self.own_map = {p: [] for p in PLANET_LIT}
        for i in range(12): self.own_map[RASHI_OWNERS[int(self.cusps[i]/30)]].append(i+1)

    def house(self, lon):
        for i in range(12):
            s, e = self.cusps[i], self.cusps[(i+1)%12]
            if (s < e and s <= lon < e) or (s > e and (lon >= s or lon < e)): return i+1
        return 1

    def four_lords(self, lon):
        sign = RASHI_OWNERS[int(lon/30)]
        star_idx = int(lon * 60 / 800) % 9
        star = PLANET_LIT[star_idx]
        star_start = (int(lon * 3 / 40)) * (40/3)
        rem = lon - star_start
        s, sub = 0, ""
        for i in range(9):
            p = PLANET_LIT[(star_idx + i) % 9]
            span = (SUB_DIVS[PLANET_LIT.index(p)] / 120) * (40/3)
            if s <= rem < s + span:
                sub = p; break
            s += span
        substar = PLANET_LIT[int(self.n_pos[sub] * 60 / 800) % 9]
        return [sign, star, sub, substar]

    def consolidated(self, p):
        hits, notes, score = [], [], 0
        lords = self.four_lords(self.n_pos[p])
        for l in lords:
            hits += [self.p_to_h[l]] + self.own_map[l]
        
        t_lon = self.t_pos[p]
        hits.append(self.house(t_lon))

        for np, nl in self.n_pos.items():
            diff = abs(t_lon - nl) % 360
            if diff > 180: diff = 360 - diff
            for ang, name in ALL_ASPECTS:
                if abs(diff - ang) <= 2.5:
                    h = self.p_to_h[np]
                    hits.append(h)
                    score += ASPECT_WEIGHTS.get(name, 0.5)
                    notes.append(f"{name}(H{h})")

        counts = Counter(hits)
        # Intensity String for Excel Formatting
        intensity_str = ""
        for h in sorted(counts.keys()):
            cnt = counts[h]
            sym = "" if cnt == 1 else ("+" if cnt == 2 else "*")
            intensity_str += f"{h}{sym} "
            
        return intensity_str, round(score, 2), " ".join(set(notes))

    def dasha6(self, dt):
        t_jd = swe.julday(dt.year, dt.month, dt.day, dt.hour+dt.minute/60-5.5)
        moon = self.n_pos["Mo"]
        one_star = 360/27
        star_idx = int(moon // one_star) % 9
        bal = ((one_star - moon % one_star) / one_star) * DASHA_YEARS[star_idx]
        start = self.njd - (DASHA_YEARS[star_idx] - bal) * YEAR_LEN
        cyc = 120 * YEAR_LEN
        t_norm = start + (t_jd - start) % cyc

        def rec(s, td, i, d):
            if d == 6: return []
            cur = s
            for k in range(9):
                p = (i + k) % 9
                dur = (DASHA_YEARS[p] / 120) * td
                if cur <= t_norm < cur + dur:
                    return [PLANET_LIT[p]] + rec(cur, dur, p, d + 1)
                cur += dur
            return ["?"]
        return rec(start, cyc, star_idx, 0)

# ========================== RUN ============================
step = {"1m":timedelta(minutes=1), "15m":timedelta(minutes=15), "1h":timedelta(hours=1), "1d":timedelta(days=1)}[FREQ]
engine = KPEngine(DOB, TOB, LAT, LON)

if MODE == "EXCEL":
    rows = []
    dt = START_DT
    while dt <= END_DT:
        engine.view_date = dt
        engine.refresh()
        dashas = engine.dasha6(dt)
        for lvl, p in zip(["MAHA","BHUKTI","ANTARA","SOOKSHMA","PRANA","DEHA"], dashas):
            instr, sc, n = engine.consolidated(p)
            rows.append({"DateTime": dt, "Level": lvl, "Planet": p, "Intensity_Strip": instr, "AspectScore": sc, "Aspects": n})
        dt += step
    pd.DataFrame(rows).to_excel(OUT_FILE, index=False)
    print(f"Excel saved → {OUT_FILE}")