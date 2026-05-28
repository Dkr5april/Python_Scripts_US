# ======================================================
#            KP MASTER ENGINE (INTERACTIVE V89 FIXED)
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
EPS = 1e-7
PLANET_LIT = ["Ke","Ve","Su","Mo","Ma","Ra","Ju","Sa","Me"]
DASHA_YEARS = [7,20,6,10,7,18,16,19,17]

RASHI_OWNERS = {
    0:"Ma",1:"Ve",2:"Me",3:"Mo",4:"Su",5:"Me",
    6:"Ve",7:"Ma",8:"Ju",9:"Sa",10:"Sa",11:"Ju"
}

POS_HOUSES = {1,2,3,6,10,11}
NEG_HOUSES = {8,12}

HOUSE_COLORS = {
    1:"green",2:"green",3:"green",6:"green",10:"green",11:"green",
    8:"red",12:"red",4:"orange3",5:"orange3",7:"orange3",9:"orange3"
}

# ==================== CORE ENGINE =====================
class KPEngineV89:
    def __init__(self, dob, tob, lat, lon):
        self.lat, self.lon = lat, lon
        d, m, y = map(int, dob.split("/"))
        hh, mm, ss = map(int, tob.split(":"))

        swe.set_ephe_path("./ephe")
        swe.set_sid_mode(swe.SIDM_KRISHNAMURTI)

        self.njd = swe.julday(y, m, d, hh+mm/60+ss/3600-5.5)
        self.view_date = datetime.now()

        # 🔒 FIX: compute birth Moon ONCE
        flag = swe.FLG_SWIEPH | swe.FLG_SIDEREAL
        self.birth_moon = swe.calc_ut(self.njd, swe.MOON, flag)[0][0]

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

        for pid, nm in [(0,"Su"),(1,"Mo"),(2,"Me"),(3,"Ve"),
                        (4,"Ma"),(5,"Ju"),(6,"Sa"),(11,"Ra")]:
            self.n_pos[nm] = swe.calc_ut(self.njd, pid, flag)[0][0]
            self.t_pos[nm] = swe.calc_ut(t_jd, pid, flag)[0][0]

        self.n_pos["Ke"] = (self.n_pos["Ra"] + 180) % 360
        self.t_pos["Ke"] = (self.t_pos["Ra"] + 180) % 360

        self.cusps = swe.houses_ex(self.njd, self.lat, self.lon, b'P', flag)[0]
        self.p_to_h = {p: self.get_h(lon) for p, lon in self.n_pos.items()}

        self.own_map = {p: [] for p in PLANET_LIT}
        for i in range(12):
            self.own_map[RASHI_OWNERS[int(self.cusps[i]/30)]].append(i+1)

    def get_h(self, lon):
        for i in range(12):
            s, e = self.cusps[i], self.cusps[(i+1)%12]
            if (s < e and s <= lon < e) or (s > e and (lon >= s or lon < e)):
                return i+1
        return 1

    def analyze(self, p):
        hits = []
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

        for h in sorted(counts):
            cnt = counts[h]
            sym = "" if cnt == 1 else ("⁺" if cnt == 2 else "★")
            color = HOUSE_COLORS.get(h, "white")
            strip.append(f"{h}{sym} ", style=f"bold {color}" if cnt > 1 else color)
            if h in POS_HOUSES: net += cnt
            if h in NEG_HOUSES: net -= cnt

        return strip, net, counts

    # ================= DASHAS =================
    def dasha6(self, dt):
        STAR_LEN = 360 / 27
        LORD_SEQ = ["Ke","Ve","Su","Mo","Ma","Ra","Ju","Sa","Me"]

        moon = self.birth_moon   # 🔒 FIXED
        nak = int(moon // STAR_LEN)
        maha_lord = nak % 9

        rem = STAR_LEN - (moon % STAR_LEN)
        bal_years = (rem / STAR_LEN) * DASHA_YEARS[maha_lord]
        maha_start = self.njd - (DASHA_YEARS[maha_lord] - bal_years) * YEAR_LEN

        t_jd = swe.julday(
            dt.year, dt.month, dt.day,
            dt.hour + dt.minute / 60 - 5.5
        )

        def walk(start_jd, total_years, lord_idx, level):
            if level == 6:
                return []

            cur = start_jd
            for k in range(9):
                idx = (lord_idx + k) % 9
                dur = (DASHA_YEARS[idx] / 120) * total_years * YEAR_LEN

                if cur - EPS <= t_jd < cur + dur + EPS:
                    return [LORD_SEQ[idx]] + walk(
                        cur, dur / YEAR_LEN, idx, level + 1
                    )
                cur += dur
            return ["?"]

        return walk(maha_start, 120, maha_lord, 0)
