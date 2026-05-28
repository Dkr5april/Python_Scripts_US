import swisseph as swe
import os, time
from datetime import datetime, timedelta
from collections import Counter
from pynput import keyboard
from rich.live import Live
from rich.table import Table
from rich.console import Console

console = Console()

# ==================== CONSTANTS & TOGGLES =======================
DEBUG_MODE = True  # Toggle this to True to see "Score Math", False to hide it
YEAR_LEN = 365.2425
EPS = 1e-7

swe.set_ephe_path("./ephe")
swe.set_sid_mode(swe.SIDM_KRISHNAMURTI)

PLANET_LIT = ["Ke","Ve","Su","Mo","Ma","Ra","Ju","Sa","Me"]
DASHA_YEARS = [7, 20, 6, 10, 7, 18, 16, 19, 17]
RASHI_OWNERS = {0:"Ma", 1:"Ve", 2:"Me", 3:"Mo", 4:"Su", 5:"Me", 6:"Ve", 7:"Ma", 8:"Ju", 9:"Sa", 10:"Sa", 11:"Ju"}

POS_HOUSES = {1, 2, 3, 6, 10, 11}
NEG_HOUSES = {8, 12}

# All 10 Major and Minor Western Aspects
ALL_ASPECTS = [
    (0, "Conj"), (180, "Oppo"), (120, "Trin"), (90, "Squa"), (60, "Sext"), 
    (30, "SSxt"), (45, "SSqu"), (150, "Quin"), (72, "Qnt"), (135, "Sesq")
]

class KPEngineV89:
    def __init__(self, dob, tob, lat, lon):
        self.lat, self.lon = lat, lon
        d, m, y = map(int, dob.split("/"))
        hh, mm, ss = map(int, tob.split(":"))

        # Julian Day Calculation
        self.njd = swe.julday(y, m, d, hh + mm/60 + ss/3600 - 5.5)
        flag = swe.FLG_SWIEPH | swe.FLG_SIDEREAL

        # FIX: Calculate birth_moon BEFORE refresh to avoid AttributeError
        self.birth_moon = swe.calc_ut(self.njd, swe.MOON, flag)[0][0]
        
        self.view_date = datetime.now()
        self.refresh()

    def refresh(self):
        flag = swe.FLG_SWIEPH | swe.FLG_SIDEREAL
        t_jd = swe.julday(self.view_date.year, self.view_date.month, self.view_date.day, 
                          self.view_date.hour + self.view_date.minute/60 - 5.5)
        
        self.n_pos, self.t_pos = {}, {}
        for pid, nm in [(0,"Su"),(1,"Mo"),(2,"Me"),(3,"Ve"),(4,"Ma"),(5,"Ju"),(6,"Sa"),(11,"Ra")]:
            self.n_pos[nm] = swe.calc_ut(self.njd, pid, flag)[0][0]
            self.t_pos[nm] = swe.calc_ut(t_jd, pid, flag)[0][0]
            
        self.n_pos["Ke"] = (self.n_pos["Ra"] + 180) % 360
        self.t_pos["Ke"] = (self.t_pos["Ra"] + 180) % 360
        
        self.cusps = swe.houses_ex(self.njd, self.lat, self.lon, b'P', flag)[0]
        self.p_to_h = {p: self.get_h(lon) for p, lon in self.n_pos.items()}
        
        self.own_map = {p: [] for p in PLANET_LIT}
        for i in range(12):
            owner = RASHI_OWNERS[int(self.cusps[i]/30)]
            self.own_map[owner].append(i + 1)

    def get_h(self, lon):
        for i in range(12):
            s, e = self.cusps[i], self.cusps[(i+1)%12]
            if (s < e and s <= lon < e) or (s > e and (lon >= s or lon < e)): 
                return i + 1
        return 1

    def analyze(self, p):
        # Always return 7 items to avoid unpacking errors
        if p == "?" or p not in self.n_pos: 
            return "-", "-", "-", "-", [], 0, []
        
        n_lon, t_lon = self.n_pos[p], self.t_pos[p]
        
        sgn = RASHI_OWNERS[int(n_lon/30)]
        str_l = PLANET_LIT[int(n_lon*3/40)%9]
        sub = PLANET_LIT[int(n_lon*27/40)%9]
        substar = PLANET_LIT[int(self.n_pos[sub]*3/40)%9]

        # KP Significator Logic: Planet + Star Lord + Sign Lord + Transit House
        hits = [self.p_to_h[p], self.p_to_h[str_l], self.p_to_h[sgn]] + \
               self.own_map[str_l] + self.own_map[sgn] + [self.get_h(t_lon)]
        
        pos_f = sorted([h for h in hits if h in POS_HOUSES])
        neg_f = sorted([h for h in hits if h in NEG_HOUSES])
        debug_info = [f"P:{pos_f}", f"N:{neg_f}"]
        
        net = len(pos_f) - len(neg_f)

        # 10 Western Transit-to-Natal Aspects
        asp_hits = []
        for n_nm, n_lon_birth in self.n_pos.items():
            diff = abs(t_lon - n_lon_birth) % 360
            if diff > 180: diff = 360 - diff
            for ang, name in ALL_ASPECTS:
                orb = 2.5 if ang in [0, 180, 120, 90, 60] else 1.2
                if abs(diff - ang) < orb:
                    col = "green" if ang in [60,120,30,72] else "red" if ang in [90,180,45,135,150] else "white"
                    asp_hits.append(f"[{col}]{name}->{n_nm}[/]")

        return sgn, str_l, sub, substar, asp_hits, net, debug_info

    def dasha6(self, dt):
        moon = self.birth_moon
        nak = int(moon // (360/27))
        m_lord_idx = nak % 9
        bal = (((360/27) - (moon % (360/27))) / (360/27)) * DASHA_YEARS[m_lord_idx]
        m_start = self.njd - (DASHA_YEARS[m_lord_idx] - bal) * YEAR_LEN
        t_jd = swe.julday(dt.year, dt.month, dt.day, dt.hour + dt.minute / 60 - 5.5)
        
        def walk(s_jd, t_yrs, l_idx, lvl):
            if lvl == 6: return []
            cur = s_jd
            for k in range(9):
                idx = (l_idx + k) % 9
                dur = (DASHA_YEARS[idx]/120) * t_yrs * YEAR_LEN
                if (t_jd + EPS) >= cur and (t_jd - EPS) < (cur + dur):
                    return [PLANET_LIT[idx]] + walk(cur, dur/YEAR_LEN, idx, lvl+1)
                cur += dur
            return ["?"]
        return walk(m_start, 120, m_lord_idx, 0)

# ==================== RUNTIME UI =====================
engine = KPEngineV89("05/04/1979", "16:55:00", 16.12, 80.93)
exit_f = False

def on_p(key):
    global exit_f
    try:
        if key == keyboard.Key.right: engine.view_date += timedelta(minutes=60); engine.refresh()
        if key == keyboard.Key.left: engine.view_date -= timedelta(minutes=60); engine.refresh()
        if hasattr(key, 'char') and key.char == 'q': exit_f = True
    except: pass

def draw():
    table = Table(title=f"KP MASTER ENGINE V89.8 | {engine.view_date.strftime('%Y-%m-%d %H:%M')}", expand=True)
    table.add_column("Level", style="cyan")
    table.add_column("Planet", style="bold yellow")
    table.add_column("Lords (Sgn/Str/Sub/SStr)")
    
    if DEBUG_MODE:
        table.add_column("Score Math (Debug)", justify="center") 
        
    table.add_column("Net", justify="right")
    table.add_column("Transit Aspects (T->N)")

    dashas = engine.dasha6(engine.view_date)
    lvls = ["MAHA","BHUKTI","ANTARA","SOOKSHMA","PRANA","DEHA"]
    
    for i, p in enumerate(dashas):
        sgn, star, sub, sstr, asp, net, debug_info = engine.analyze(p)
        color = "green" if net > 0 else "red" if net < 0 else "white"
        
        row_data = [lvls[i], p, f"{sgn}/{star}/{sub}/{sstr}"]
        
        if DEBUG_MODE:
            math_str = f"[green]{debug_info[0]}[/] [red]{debug_info[1]}[/]"
            row_data.append(math_str)
            
        row_data.extend([f"[bold {color}]{net}[/]", ", ".join(asp)])
        table.add_row(*row_data)
        
    return table

listener = keyboard.Listener(on_press=on_p); listener.start()
with Live(draw(), refresh_per_second=2, screen=True) as live:
    while not exit_f:
        live.update(draw())
        time.sleep(0.2)
listener.stop()