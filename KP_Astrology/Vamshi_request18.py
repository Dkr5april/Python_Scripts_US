# ======================================================
#            KP MASTER ENGINE (INTERACTIVE V91)
# ======================================================

import swisseph as swe
from datetime import datetime, timedelta
from collections import Counter
from pynput import keyboard
from rich.live import Live
from rich.table import Table
from rich.console import Console
from rich.panel import Panel
from rich.text import Text
import pandas as pd
import time

console = Console()

# ==================== CONSTANTS =======================
YEAR_LEN = 365.2425
EPS = 1e-7  # Julian Day tolerance

swe.set_ephe_path("./ephe")
swe.set_sid_mode(swe.SIDM_KRISHNAMURTI)

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

ASPECTS = [
    (0,"Conj"),(60,"Sext"),(90,"Square"),(120,"Trine"),(180,"Opp"),
    (72,"Quint"),(144,"BiQuint"),(30,"Semisextile"),(45,"Semisquare"),(135,"Sesquiquadrate")
]

# ==================== CORE ENGINE =====================
class KPEngineV91:
    def __init__(self, dob, tob, lat, lon):
        self.lat, self.lon = lat, lon
        d,m,y = map(int,dob.split("/"))
        hh,mm,ss = map(int,tob.split(":"))
        self.njd = swe.julday(y,m,d,hh+mm/60+ss/3600-5.5)
        self.view_date = datetime.now()

        flag = swe.FLG_SWIEPH | swe.FLG_SIDEREAL

        # 🔒 Freeze birth Moon for stable Mahadasha
        self.birth_moon = swe.calc_ut(self.njd, swe.MOON, flag)[0][0]

        self.refresh()

    def refresh(self):
        flag = swe.FLG_SWIEPH | swe.FLG_SIDEREAL
        self.n_pos, self.t_pos = {},{}
        t_jd = swe.julday(self.view_date.year,self.view_date.month,self.view_date.day,
                          self.view_date.hour + self.view_date.minute/60 - 5.5)

        # Planets except Moon
        for pid, nm in [(0,"Su"),(2,"Me"),(3,"Ve"),(4,"Ma"),(5,"Ju"),(6,"Sa"),(11,"Ra")]:
            self.n_pos[nm] = swe.calc_ut(self.njd, pid, flag)[0][0]
            self.t_pos[nm] = swe.calc_ut(t_jd, pid, flag)[0][0]

        # Moon
        self.n_pos["Mo"] = self.birth_moon
        self.t_pos["Mo"] = swe.calc_ut(t_jd, swe.MOON, flag)[0][0]

        # Ketu
        self.n_pos["Ke"] = (self.n_pos["Ra"] + 180) % 360
        self.t_pos["Ke"] = (self.t_pos["Ra"] + 180) % 360

        # Houses
        self.cusps = swe.houses_ex(self.njd,self.lat,self.lon,b'P',flag)[0]
        self.p_to_h = {p:self.get_h(lon) for p,lon in self.n_pos.items()}

        # Own map
        self.own_map = {p:[] for p in PLANET_LIT}
        for i in range(12):
            self.own_map[RASHI_OWNERS[int(self.cusps[i]/30)]].append(i+1)

    def get_h(self, lon):
        for i in range(12):
            s,e = self.cusps[i],self.cusps[(i+1)%12]
            if (s<e and s<=lon<e) or (s>e and (lon>=s or lon<e)):
                return i+1
        return 1

    # ==================== ASPECT CALC =====================
    def aspect_score(self, p_lon, other_lon):
        net = 0
        aspect_debug = []
        for ang,name in ASPECTS:
            diff = (other_lon - p_lon) % 360
            if abs(diff - ang) < 1.0:  # 1° orb
                net += 1
                aspect_debug.append(f"{name}({diff:.2f})")
        return net, aspect_debug

    # ==================== PLANET ANALYSIS =================
    def analyze(self, p):
        hits = []
        debug_lines = []

        lon = self.n_pos[p]
        # Star / Nakshatra
        star_idx = int(lon * 60 / 800) % 9
        star = PLANET_LIT[star_idx]
        # Sublord
        sublord_idx = star_idx
        sublord = PLANET_LIT[sublord_idx]
        # Substar lord
        substar_idx = (sublord_idx + 1) % 9
        substar = PLANET_LIT[substar_idx]

        lords = [RASHI_OWNERS[int(lon/30)], star, sublord, substar]

        # House hits for planet + lords
        for l in lords:
            hits += [self.p_to_h[l]] + self.own_map[l]

        # Target house
        hits.append(self.get_h(self.t_pos[p]))
        counts = Counter(hits)

        # Aspect contribution
        aspect_net = 0
        aspect_debug = []
        for other, other_lon in self.n_pos.items():
            if other==p: continue
            n, dbg = self.aspect_score(lon, other_lon)
            aspect_net += n
            aspect_debug += [f"{other}:{dbg}" for dbg in dbg]

        net = 0
        strip = Text()
        for h in sorted(counts):
            cnt = counts[h]
            sym = "" if cnt==1 else ("⁺" if cnt==2 else "★")
            color = HOUSE_COLORS.get(h,"white")
            strip.append(f"{h}{sym} ", style=f"bold {color}" if cnt>1 else color)
            if h in POS_HOUSES: net+=cnt
            if h in NEG_HOUSES: net-=cnt
        net += aspect_net

        # DEBUG
        debug_lines.append(f"PLANET: {p}")
        debug_lines.append(f"Sign lord: {RASHI_OWNERS[int(lon/30)]}")
        debug_lines.append(f"Star lord: {star}")
        debug_lines.append(f"Sublord: {sublord}")
        debug_lines.append(f"Substar lord: {substar}")
        debug_lines.append(f"HOUSE hits: {dict(counts)}")
        debug_lines.append(f"ASPECTS: {aspect_debug}")
        debug_lines.append(f"NET: {net}")

        return strip, net, debug_lines

    # ==================== STABLE DASHA =====================
    def dasha6(self, dt):
        STAR_LEN = 360/27
        LORD_SEQ = ["Ke","Ve","Su","Mo","Ma","Ra","Ju","Sa","Me"]

        moon = self.birth_moon
        nak = int(moon // STAR_LEN)
        maha_lord = nak % 9

        rem = STAR_LEN - (moon % STAR_LEN)
        bal_years = (rem/STAR_LEN) * DASHA_YEARS[maha_lord]
        maha_start = self.njd - (DASHA_YEARS[maha_lord]-bal_years)*YEAR_LEN

        t_jd = swe.julday(dt.year,dt.month,dt.day,dt.hour+dt.minute/60-5.5)

        def walk(start_jd, total_years, lord_idx, level):
            if level==6: return []
            cur = start_jd
            for k in range(9):
                idx = (lord_idx+k)%9
                dur = (DASHA_YEARS[idx]/120)*total_years*YEAR_LEN
                if (t_jd+EPS)>=cur and (t_jd-EPS)<(cur+dur):
                    return [LORD_SEQ[idx]] + walk(cur,dur/ YEAR_LEN,idx,level+1)
                cur+=dur
            return ["?"]

        return walk(maha_start,120,maha_lord,0)

# ==================== UI =====================
console.print(Panel("[bold yellow]KP MASTER ENGINE V91[/bold yellow]\n[cyan]Interactive Setup",expand=False))

console.print("\n[1] Use Automated Details\n[2] Enter Manual Birth Details")
choice_b = input("Select (1-2): ")

if choice_b=="2":
    dob = input("Enter DOB (DD/MM/YYYY): ")
    tob = input("Enter TOB (HH:MM:SS): ")
    lat = float(input("Enter Latitude: "))
    lon = float(input("Enter Longitude: "))
else:
    dob,tob,lat,lon="05/04/1979","16:55:00",16.12,80.93

engine = KPEngineV91(dob,tob,lat,lon)

console.print("\n[1] Dashboard\n[2] Excel Export")
choice_m = input("Select (1-2): ")

if choice_m=="1":
    exit_f = False
    def on_p(key):
        global exit_f
        try:
            if key==keyboard.Key.right:
                engine.view_date+=timedelta(minutes=5)
                engine.refresh()
            if key==keyboard.Key.left:
                engine.view_date-=timedelta(minutes=5)
                engine.refresh()
            if hasattr(key,'char') and key.char=='q':
                exit_f=True
        except: pass

    def draw():
        table = Table(title=f"LIVE KP DEBUG: {engine.view_date.strftime('%Y-%m-%d %H:%M')}")
        table.add_column("Level")
        table.add_column("Planet")
        table.add_column("Net")
        table.add_column("Debug",overflow="fold")

        lvls = ["MAHA","BHUKTI","ANTARA","SOOKSHMA","PRANA","DEHA"]
        d = engine.dasha6(engine.view_date)

        for i,p in enumerate(d):
            strip,net,debug = engine.analyze(p)
            debug_text = "\n".join(debug)
            table.add_row(lvls[i],p,str(net),debug_text)

        return table

    listener = keyboard.Listener(on_press=on_p)
    listener.start()
    with Live(draw(),refresh_per_second=2,screen=True) as live:
        while not exit_f:
            live.update(draw())
            time.sleep(0.2)
    listener.stop()

else:
    # Excel export: consolidated TOTAL_NET per Dasa level
    start_s = input("Start Date (DD/MM/YYYY): ")
    end_s = input("End Date (DD/MM/YYYY): ")
    freq_s = input("Frequency (1m,15m,1h): ")

    s_dt = datetime.strptime(start_s,"%d/%m/%Y")
    e_dt = datetime.strptime(end_s,"%d/%m/%Y")
    step = {"1m":timedelta(minutes=1),"15m":timedelta(minutes=15),"1h":timedelta(hours=1)}[freq_s]

    rows=[]
    curr=s_dt
    print("⏳ Processing Excel Export...")

    while curr<=e_dt:
        engine.view_date=curr
        engine.refresh()
        dashas=engine.dasha6(curr)
        for i,p in enumerate(dashas):
            _,net,_ = engine.analyze(p)
            rows.append({"Time":curr,"Level":i,"Planet":p,"Net":net})
        curr+=step

    pd.DataFrame(rows).to_excel("KP_EXPORT.xlsx",index=False)
    print("✅ Done! File saved as KP_EXPORT.xlsx")
