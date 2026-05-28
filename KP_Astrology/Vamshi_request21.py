# ======================================================
#            KP MASTER ENGINE (INTERACTIVE V89)
# ======================================================

import swisseph as swe
import os, time
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
EPS = 1e-7  # JD tolerance

# Ensure the 'ephe' folder exists or path is correct
swe.set_ephe_path("./ephe")
swe.set_sid_mode(swe.SIDM_KRISHNAMURTI)

PLANET_LIT = ["Ke","Ve","Su","Mo","Ma","Ra","Ju","Sa","Me"]
DASHA_YEARS = [7, 20, 6, 10, 7, 18, 16, 19, 17]

RASHI_OWNERS = {
    0:"Ma", 1:"Ve", 2:"Me", 3:"Mo", 4:"Su", 5:"Me",
    6:"Ve", 7:"Ma", 8:"Ju", 9:"Sa", 10:"Sa", 11:"Ju"
}

POS_HOUSES = {1, 2, 3, 6, 10, 11}
NEG_HOUSES = {8, 12}

HOUSE_COLORS = {
    1:"green", 2:"green", 3:"green", 6:"green", 10:"green", 11:"green",
    8:"red", 12:"red", 4:"orange3", 5:"orange3", 7:"orange3", 9:"orange3"
}

ALL_ASPECTS = [(0,"Conj"), (60,"Sext"), (90,"Squa"), (120,"Trin"), (180,"Oppo")]

# ==================== CORE ENGINE =====================
class KPEngineV89:
    def __init__(self, dob, tob, lat, lon):
        self.lat, self.lon = lat, lon
        d, m, y = map(int, dob.split("/"))
        hh, mm, ss = map(int, tob.split(":"))

        # Julian Day for birth in UTC (assuming IST -5.5)
        self.njd = swe.julday(y, m, d, hh + mm/60 + ss/3600 - 5.5)
        flag = swe.FLG_SWIEPH | swe.FLG_SIDEREAL

        # Freeze birth Moon
        self.birth_moon = swe.calc_ut(self.njd, swe.MOON, flag)[0][0]

        self.view_date = datetime.now()
        self.refresh()

    def refresh(self):
        flag = swe.FLG_SWIEPH | swe.FLG_SIDEREAL
        self.n_pos, self.t_pos = {}, {}

        t_jd = swe.julday(
            self.view_date.year,
            self.view_date.month,
            self.view_date.day,
            self.view_date.hour + self.view_date.minute/60 - 5.5
        )

        for pid, nm in [(0,"Su"),(2,"Me"),(3,"Ve"),(4,"Ma"),(5,"Ju"),(6,"Sa"),(11,"Ra")]:
            self.n_pos[nm] = swe.calc_ut(self.njd, pid, flag)[0][0]
            self.t_pos[nm] = swe.calc_ut(t_jd, pid, flag)[0][0]

        self.n_pos["Mo"] = self.birth_moon
        self.t_pos["Mo"] = swe.calc_ut(t_jd, swe.MOON, flag)[0][0]
        self.n_pos["Ke"] = (self.n_pos["Ra"] + 180) % 360
        self.t_pos["Ke"] = (self.t_pos["Ra"] + 180) % 360

        self.cusps = swe.houses_ex(self.njd, self.lat, self.lon, b'P', flag)[0]
        self.p_to_h = {p: self.get_h(lon) for p, lon in self.n_pos.items()}

        self.own_map = {p: [] for p in PLANET_LIT}
        for i in range(12):
            owner = RASHI_OWNERS[int(self.cusps[i] / 30)]
            self.own_map[owner].append(i + 1)

    def get_h(self, lon):
        for i in range(12):
            s, e = self.cusps[i], self.cusps[(i+1)%12]
            if (s < e and s <= lon < e) or (s > e and (lon >= s or lon < e)):
                return i + 1
        return 1

    def analyze(self, p, debug=False):
        if p == "?": return {}, 0, "", "", "", []
        lon = self.n_pos[p]
        
        # KP Lords Calculation
        sign_lord = RASHI_OWNERS[int(lon / 30)]
        star_lord = PLANET_LIT[int(lon * 3 / 40) % 9]
        # Simplified Sub calculation for V89
        sub_lord = PLANET_LIT[int(lon * 27 / 40) % 9] 
        substar_lord = PLANET_LIT[int(lon * 243 / 40) % 9]

        hits = [self.p_to_h[sign_lord]] + self.own_map[sign_lord] \
               + [self.p_to_h[star_lord]] + self.own_map[star_lord]

        hits.append(self.get_h(self.t_pos[p]))

        asp = []
        for nm, lon2 in self.n_pos.items():
            if nm == p: continue
            for ang, name in ALL_ASPECTS:
                delta = abs(lon - lon2) % 360
                if abs(delta - ang) < 2:
                    asp.append(f"{nm}:{name}")

        counts = Counter(hits)
        net = sum(counts[h] for h in counts if h in POS_HOUSES) - sum(counts[h] for h in counts if h in NEG_HOUSES)

        if debug:
            debug_text = [
                f"PLANET: {p}", f"Sign: {sign_lord}", f"Star: {star_lord}",
                f"Sub: {sub_lord}", f"H-Hits: {dict(counts)}", f"NET: {net}"
            ]
            return counts, net, sign_lord, star_lord, sub_lord, asp, debug_text
        return counts, net, sign_lord, star_lord, sub_lord, asp

    def dasha6(self, dt):
        STAR_LEN = 360 / 27
        moon = self.birth_moon
        nak = int(moon // STAR_LEN)
        maha_lord_idx = nak % 9

        rem = STAR_LEN - (moon % STAR_LEN)
        bal_years = (rem / STAR_LEN) * DASHA_YEARS[maha_lord_idx]
        maha_start = self.njd - (DASHA_YEARS[maha_lord_idx] - bal_years) * YEAR_LEN
        t_jd = swe.julday(dt.year, dt.month, dt.day, dt.hour + dt.minute / 60 - 5.5)

        def walk(start_jd, total_years, lord_idx, level):
            if level == 6: return []
            cur = start_jd
            for k in range(9):
                idx = (lord_idx + k) % 9
                dur = (DASHA_YEARS[idx] / 120) * total_years * YEAR_LEN
                if (t_jd + EPS) >= cur and (t_jd - EPS) < (cur + dur):
                    return [PLANET_LIT[idx]] + walk(cur, dur / YEAR_LEN, idx, level + 1)
                cur += dur
            return ["?"]
        return walk(maha_start, 120, maha_lord_idx, 0)

# ==================== UI =====================

console.print(Panel("[bold yellow]KP MASTER ENGINE V89[/bold yellow]\n[cyan]Interactive Setup", expand=False))

console.print("\n[1] Use Automated Details (Koteswara Rao)\n[2] Enter Manual Birth Details")
choice_b = input("Select (1-2): ")

if choice_b == "2":
    dob = input("Enter DOB (DD/MM/YYYY): ")
    tob = input("Enter TOB (HH:MM:SS): ")
    lat = float(input("Enter Latitude: "))
    lon = float(input("Enter Longitude: "))
else:
    dob, tob, lat, lon = "05/04/1979", "16:55:00", 16.12, 80.93

engine = KPEngineV89(dob, tob, lat, lon)

console.print("\n[1] Dashboard\n[2] Excel Export")
choice_m = input("Select (1-2): ")
debug_mode = input("Enable debug? (y/n): ").lower() == "y"

exit_f = False

if choice_m == "1":
    def on_p(key):
        global exit_f
        try:
            if key == keyboard.Key.right:
                engine.view_date += timedelta(minutes=5)
                engine.refresh()
            if key == keyboard.Key.left:
                engine.view_date -= timedelta(minutes=5)
                engine.refresh()
            if hasattr(key, 'char') and key.char == 'q':
                exit_f = True
        except: pass

    def draw():
        table = Table(title=f"LIVE KP: {engine.view_date.strftime('%Y-%m-%d %H:%M')}")
        table.add_column("Level")
        table.add_column("Planet")
        table.add_column("Net", justify="right")
        table.add_column("Debug" if debug_mode else "Info")

        lvls = ["MAHA","BHUKTI","ANTARA","SOOKSHMA","PRANA","DEHA"]
        dashas = engine.dasha6(engine.view_date)

        for i, p in enumerate(dashas):
            res = engine.analyze(p, debug=debug_mode)
            if debug_mode:
                counts, net, sign, star, sub, asp, debug_text = res
                info_str = " | ".join(debug_text[1:])
            else:
                counts, net, sign, star, sub, asp = res
                info_str = f"Sign:{sign} Star:{star} Sub:{sub}"

            color = "green" if net >= 0 else "red"
            table.add_row(lvls[i], p, f"[bold {color}]{net}[/bold {color}]", info_str)
        return table

    listener = keyboard.Listener(on_press=on_p)
    listener.start()

    with Live(draw(), refresh_per_second=2, screen=True) as live:
        while not exit_f:
            live.update(draw())
            time.sleep(0.2)
    listener.stop()

else:
    # EXCEL EXPORT LOGIC
    start_s = input("Start Date (DD/MM/YYYY): ")
    end_s = input("End Date (DD/MM/YYYY): ")
    freq_s = input("Frequency (1m, 15m, 1h): ")
    s_dt = datetime.strptime(start_s, "%d/%m/%Y")
    e_dt = datetime.strptime(end_s, "%d/%m/%Y")
    step = {"1m":timedelta(minutes=1), "15m":timedelta(minutes=15), "1h":timedelta(hours=1)}[freq_s]

    rows = []
    curr = s_dt
    while curr <= e_dt:
        engine.view_date = curr
        engine.refresh()
        dashas = engine.dasha6(curr)
        for i, p in enumerate(dashas):
            counts, net, sign, star, sub, asp = engine.analyze(p)
            rows.append({"Time": curr, "Level": i, "Planet": p, "Net": net, "Sign": sign, "Star": star})
        curr += step

    pd.DataFrame(rows).to_excel("KP_EXPORT.xlsx", index=False)
    print("✅ File saved as KP_EXPORT.xlsx")