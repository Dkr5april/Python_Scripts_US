# ======================================================
#            KP MASTER ENGINE (INTERACTIVE V89)
# ======================================================

import swisseph as swe
import os, time, sys
from datetime import datetime, timedelta
from collections import Counter
from pynput import keyboard
from rich.live import Live
from rich.table import Table
from rich.console import Console
from rich.panel import Panel
from rich.text import Text
import pandas as pd

console = Console()

# ==================== CONSTANTS =======================
YEAR_LEN = 365.2425
swe.set_ephe_path("./ephe")
swe.set_sid_mode(swe.SIDM_KRISHNAMURTI)

PLANET_LIT = ["Ke","Ve","Su","Mo","Ma","Ra","Ju","Sa","Me"]
DASHA_YEARS = [7,20,6,10,7,18,16,19,17]
RASHI_OWNERS = {0:"Ma",1:"Ve",2:"Me",3:"Mo",4:"Su",5:"Me",6:"Ve",7:"Ma",8:"Ju",9:"Sa",10:"Sa",11:"Ju"}
POS_HOUSES = {1, 2, 3, 6, 10, 11}
NEG_HOUSES = {8, 12}
HOUSE_COLORS = {1:"green",2:"green",3:"green",6:"green",10:"green",11:"green",8:"red",12:"red",4:"orange3",5:"orange3",7:"orange3",9:"orange3"}
ALL_ASPECTS = [(0,"Conj"),(60,"Sext"),(90,"Squa"),(120,"Trin"),(180,"Oppo")]

# ==================== CORE ENGINE =====================
class KPEngineV89:
    def __init__(self, dob, tob, lat, lon):
        self.lat, self.lon = lat, lon
        d, m, y = map(int, dob.split("/"))
        hh, mm, ss = map(int, tob.split(":"))
        self.njd = swe.julday(y, m, d, hh+mm/60+ss/3600-5.5)
        self.view_date = datetime.now()
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
        self.p_to_h = {p: self.get_h(lon) for p, lon in self.n_pos.items()}
        self.own_map = {p: [] for p in PLANET_LIT}
        for i in range(12): self.own_map[RASHI_OWNERS[int(self.cusps[i]/30)]].append(i+1)

    def get_h(self, lon):
        for i in range(12):
            s, e = self.cusps[i], self.cusps[(i+1)%12]
            if (s < e and s <= lon < e) or (s > e and (lon >= s or lon < e)): return i+1
        return 1

    def analyze(self, p):
        hits = []
        # significators (Sign/Star/Sub)
        lon = self.n_pos[p]
        idx = int(lon * 60 / 800) % 9
        star = PLANET_LIT[idx]
        lords = [RASHI_OWNERS[int(lon/30)], star]
        for l in lords:
            hits += [self.p_to_h[l]] + self.own_map[l]
        hits.append(self.get_h(self.t_pos[p]))
        
        counts = Counter(hits)
        strip = Text()
        net = 0
        for h in sorted(counts.keys()):
            cnt = counts[h]
            sym = "" if cnt == 1 else ("⁺" if cnt == 2 else "★")
            color = HOUSE_COLORS.get(h, "white")
            strip.append(f"{h}{sym} ", style=f"bold {color}" if cnt > 1 else color)
            if h in POS_HOUSES: net += cnt
            if h in NEG_HOUSES: net -= cnt
        return strip, net, counts

    def dasha6(self, dt):
        t_jd = swe.julday(dt.year, dt.month, dt.day, dt.hour+dt.minute/60-5.5)
        moon = self.n_pos["Mo"]
        star_idx = int(moon // (360/27)) % 9
        bal = ((360/27 - moon % (360/27)) / (360/27)) * DASHA_YEARS[star_idx]
        start = self.njd - (DASHA_YEARS[star_idx] - bal) * YEAR_LEN
        t_norm = start + (t_jd - start) % (120 * YEAR_LEN)
        def rec(s, td, i, d):
            if d == 6: return []
            cur = s
            for k in range(9):
                p = (i + k) % 9
                dur = (DASHA_YEARS[p] / 120) * td
                if cur <= t_norm < cur + dur: return [PLANET_LIT[p]] + rec(cur, dur, p, d + 1)
                cur += dur
            return ["?"]
        return rec(start, 120 * YEAR_LEN, star_idx, 0)

# ==================== INTERACTIVE MENU =====================
console.print(Panel("[bold yellow]KP MASTER ENGINE V89[/bold yellow]\n[cyan]Interactive Setup", expand=False))

# 1. Birth Details
console.print("\n[1] Use Automated Details (Koteswara Rao)\n[2] Enter Manual Birth Details")
choice_b = input("Select (1-2): ")
if choice_b == "2":
    dob = input("Enter DOB (DD/MM/YYYY): ")
    tob = input("Enter TOB (HH:MM:SS): ")
    lat = float(input("Enter Latitude (e.g. 16.12): "))
    lon = float(input("Enter Longitude (e.g. 80.93): "))
else:
    dob, tob, lat, lon = "05/04/1979", "16:55:00", 16.12, 80.93

engine = KPEngineV89(dob, tob, lat, lon)

# 2. Mode Selection
console.print("\n[1] Dashboard (Live Interactive Screen)\n[2] Excel (Bulk Data Export)")
choice_m = input("Select (1-2): ")

if choice_m == "1":
    # DASHBOARD MODE
    exit_f = False
    def on_p(key):
        global exit_f
        try:
            if key == keyboard.Key.right: engine.view_date += timedelta(minutes=5); engine.refresh()
            if key == keyboard.Key.left: engine.view_date -= timedelta(minutes=5); engine.refresh()
            if hasattr(key, 'char') and key.char == 'q': exit_f = True
        except: pass

    def draw():
        table = Table(title=f"LIVE KP: {engine.view_date.strftime('%Y-%m-%d %H:%M')}")
        table.add_column("Level"); table.add_column("Planet"); table.add_column("Intensity Strip"); table.add_column("Net", justify="right")
        d = engine.dasha6(engine.view_date)
        lvls = ["MAHA","BHUKTI","ANTARA","SOOKSHMA","PRANA","DEHA"]
        for i, p in enumerate(d):
            strip, net, _ = engine.analyze(p)
            table.add_row(lvls[i], p, strip, str(net))
        return table

    listener = keyboard.Listener(on_press=on_p); listener.start()
    with Live(draw(), refresh_per_second=2, screen=True) as live:
        while not exit_f: live.update(draw()); time.sleep(0.2)
    listener.stop()

else:
    # EXCEL MODE
    start_s = input("Start Date (DD/MM/YYYY): ")
    end_s = input("End Date (DD/MM/YYYY): ")
    freq_s = input("Frequency (1m, 15m, 1h): ")
    
    s_dt = datetime.strptime(start_s, "%d/%m/%Y")
    e_dt = datetime.strptime(end_s, "%d/%m/%Y")
    step = {"1m":timedelta(minutes=1), "15m":timedelta(minutes=15), "1h":timedelta(hours=1)}[freq_s]
    
    rows = []
    curr = s_dt
    print("⏳ Processing Excel Export...")
    while curr <= e_dt:
        engine.view_date = curr
        engine.refresh()
        dashas = engine.dasha6(curr)
        for i, p in enumerate(dashas):
            strip, net, counts = engine.analyze(p)
            rows.append({"Time": curr, "Level": i, "Planet": p, "Net": net, "Significators": str(dict(counts))})
        curr += step
    pd.DataFrame(rows).to_excel("KP_EXPORT.xlsx", index=False)
    print("✅ Done! File saved as KP_EXPORT.xlsx")