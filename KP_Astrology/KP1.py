import swisseph as swe
import os, sys, time
import geocoder
import xlwings as xw
from datetime import datetime, timedelta
from pynput import keyboard
from geopy.geocoders import Nominatim
from rich.live import Live
from rich.table import Table
from rich.console import Console
from rich.layout import Layout
from rich.panel import Panel
from rich.align import Align

# ---------------- STABILITY & SETTINGS ----------------
if sys.platform == "win32":
    os.system("color")

swe.set_ephe_path("./ephe")
console = Console()
geolocator = Nominatim(user_agent="kp_final_engine_v28")

# KP & Dasha Constants
DASHA_YEARS = [7, 20, 6, 10, 7, 18, 16, 19, 17] # Ke, Ve, Su, Mo, Ma, Ra, Ju, Sa, Me
PLANET_LIT = ["Ke", "Ve", "Su", "Mo", "Ma", "Ra", "Ju", "Sa", "Me"]
SIGN_LORDS = ["Ma", "Ve", "Me", "Mo", "Su", "Me", "Ve", "Ma", "Ju", "Sa", "Sa", "Ju"]
OWNERSHIP = {"Ma": [1, 8], "Ve": [2, 7], "Me": [3, 6], "Mo": [4], "Su": [5], "Ju": [9, 12], "Sa": [10, 11]}

# ---------------- INPUTS ----------------
console.clear()
console.print("[bold magenta]=== ASTRO-KP ENGINE V28 (SIDEREAL + TROPICAL) ===[/bold magenta]\n")

name = input("Enter Name: ")
dob = input("Enter DOB (DD/MM/YYYY): ")
tob = input("Enter TOB (HH:MM:SS): ")
birth_city = input("Enter Birth City: ")

def fetch_coords(city):
    try:
        loc = geolocator.geocode(city, timeout=5)
        return (loc.latitude, loc.longitude) if loc else (0.0, 0.0)
    except: return 0.0, 0.0

b_lat, b_lon = fetch_coords(birth_city)
d, m, y = map(int, dob.split("/"))
hh, mm, ss = map(int, tob.split(":"))
birth_hour = hh + mm/60 + ss/3600

# ---------------- ENGINE LOGIC ----------------
def get_kp_lords(lon):
    """Calculates Sign, Star, Sub, SSL, and SSSL lords."""
    total_min = (lon % 360) * 60
    star_idx = int(total_min / 800) % 9
    
    def find_sub(elapsed, total_span, s_idx):
        cumulative = 0
        for i in range(9):
            idx = (s_idx + i) % 9
            span = (DASHA_YEARS[idx] / 120.0) * total_span
            if cumulative + span > elapsed:
                return PLANET_LIT[idx], span, elapsed - cumulative
            cumulative += span
        return PLANET_LIT[8], 0, 0

    sub_l, sub_s, el_sub = find_sub(total_min % 800, 800, star_idx)
    ssl_l, ssl_s, el_ssl = find_sub(el_sub, sub_s, PLANET_LIT.index(sub_l))
    sssl_l, _, _ = find_sub(el_ssl, ssl_s, PLANET_LIT.index(ssl_l))
    return [SIGN_LORDS[int(lon/30)], PLANET_LIT[star_idx], sub_l, ssl_l, sssl_l]

class AstroEngine:
    def __init__(self):
        self.view_date = datetime.now()
        self.njd = swe.julday(y, m, d, birth_hour)
        self.mode = "SIDEREAL"
        
        # Natal Calculations
        swe.set_sid_mode(swe.SIDM_KRISHNAMURTI)
        self.n_sid = self.calc_set(self.njd, True)
        self.n_trop = self.calc_set(self.njd, False)
        
        # House Cusps (Placidus)
        cusps, _ = swe.houses_ex(self.njd, b_lat, b_lon, b'P')
        self.cusps = cusps[1:]

    def calc_set(self, jd, sidereal):
        data = {}
        flags = swe.FLG_SWIEPH | (swe.FLG_SIDEREAL if sidereal else 0)
        for i, nm in [(0,"Su"),(1,"Mo"),(2,"Me"),(3,"Ve"),(4,"Ma"),(5,"Ju"),(6,"Sa"),(11,"Ra"),(10,"Ke")]:
            res, _ = swe.calc_ut(jd, i, flags)
            data[nm] = {"lon": res[0], "dec": res[1], "lords": get_kp_lords(res[0]) if sidereal else []}
        return data

    def get_dasha_6(self, target_jd):
        moon_lon = self.n_sid["Mo"]["lon"]
        star_idx = int((moon_lon * 60) / 800) % 9
        rem_deg = (((star_idx + 1) * 800) / 60) - moon_lon
        bal_yrs = (rem_deg / (800/60)) * DASHA_YEARS[star_idx]
        m_start = self.njd - ((DASHA_YEARS[star_idx] - bal_yrs) * 365.25)

        def recurse(start, total_days, p_idx, depth):
            if depth == 6: return []
            curr = start
            for i in range(9):
                idx = (p_idx + i) % 9
                dur = (DASHA_YEARS[idx] / 120.0) * total_days
                if curr <= target_jd < curr + dur:
                    return [PLANET_LIT[idx]] + recurse(curr, dur, idx, depth + 1)
                curr += dur
            return ["?"]
        return recurse(m_start, DASHA_YEARS[star_idx] * 365.25, star_idx, 0)

    def get_significators(self, pnm):
        lon = self.n_sid[pnm]["lon"]
        def find_house(p_lon):
            for i in range(12):
                h_start, h_end = self.cusps[i], self.cusps[(i+1)%12]
                if (h_start < h_end and h_start <= p_lon < h_end) or (h_start > h_end and (p_lon >= h_start or p_lon < h_end)):
                    return i + 1
            return 1
        occ = find_house(lon)
        return sorted(list(set([occ] + OWNERSHIP.get(pnm, []))))

engine = AstroEngine()

# ---------------- UI & RENDER ----------------
def get_main_table():
    t_jd = swe.julday(engine.view_date.year, engine.view_date.month, engine.view_date.day, engine.view_date.hour)
    is_sid = (engine.mode == "SIDEREAL")
    t_data = engine.calc_set(t_jd, is_sid)
    n_data = engine.n_sid if is_sid else engine.n_trop
    dasha = engine.get_dasha_6(t_jd)
    
    table = Table(title=f"DASHA: {'-'.join(dasha)}", expand=True, border_style="cyan")
    table.add_column("Planet", style="bold")
    table.add_column("Transit Lon | Dec", style="red")
    table.add_column("Natal Lon | Dec", style="green")
    
    if is_sid:
        table.add_column("Transit SSSL (Si-St-Su-Sl-Ss)", style="yellow")
        table.add_column("Houses Triggered", style="magenta")

    for p in ["Su", "Mo", "Me", "Ve", "Ma", "Ju", "Sa", "Ra", "Ke"]:
        t, n = t_data[p], n_data[p]
        t_str = f"{t['lon']:.2f}° | {t['dec']:.1f}"
        n_str = f"{n['lon']:.2f}° | {n['dec']:.1f}"
        row = [p, t_str, n_str]
        if is_sid:
            row.append("-".join(t['lords']))
            row.append(",".join(map(str, engine.get_significators(p))))
        table.add_row(*row)
    return table

def make_layout():
    layout = Layout()
    layout.split_column(
        Layout(Panel(f"TARGET: {name} | MODE: {engine.mode} | [T] Toggle | [Arrows] Time Step | [Q] Quit", style="white on blue"), size=3),
        Layout(get_main_table())
    )
    return layout

# ---------------- CONTROLS ----------------
exit_flag = False
def on_press(key):
    global exit_flag
    try:
        if key == keyboard.Key.right: engine.view_date += timedelta(hours=1)
        elif key == keyboard.Key.left: engine.view_date -= timedelta(hours=1)
        elif hasattr(key, 'char'):
            if key.char == 't': engine.mode = "TROPICAL" if engine.mode == "SIDEREAL" else "SIDEREAL"
            if key.char == 'q': exit_flag = True
    except: pass

listener = keyboard.Listener(on_press=on_press); listener.start()

# ---------------- MAIN ----------------
try:
    with Live(make_layout(), refresh_per_second=2, screen=True) as live:
        while not exit_flag:
            live.update(make_layout())
            time.sleep(0.5)
finally:
    listener.stop()
    console.clear()
    console.print("[bold green]Engine Stopped Safely.[/]")