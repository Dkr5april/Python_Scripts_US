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

# ---------------- CONFIG & CONSTANTS ----------------
swe.set_ephe_path("./ephe")
console = Console()
geolocator = Nominatim(user_agent="kp_v29_punarvasu_fix")

# STANDARD VIMSHOTTARI ORDER
PLANET_LIT = ["Ke", "Ve", "Su", "Mo", "Ma", "Ra", "Ju", "Sa", "Me"]
DASHA_YEARS = [7, 20, 6, 10, 7, 18, 16, 19, 17]
SIGN_LORDS = ["Ma", "Ve", "Me", "Mo", "Su", "Me", "Ve", "Ma", "Ju", "Sa", "Sa", "Ju"]
OWNERSHIP = {"Ma": [1, 8], "Ve": [2, 7], "Me": [3, 6], "Mo": [4], "Su": [5], "Ju": [9, 12], "Sa": [10, 11]}

# ---------------- INPUTS ----------------
console.print("[bold yellow]RE-RUNNING ENGINE V29...[/]")
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

# ---------------- ENGINE ----------------
def get_kp_lords(lon):
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

class KPEngine:
    def __init__(self):
        self.view_date = datetime.now()
        self.njd = swe.julday(y, m, d, birth_hour)
        swe.set_sid_mode(swe.SIDM_KRISHNAMURTI)
        
        # Natal Data
        self.n_sid = {}
        for i, nm in [(10,"Ke"),(3,"Ve"),(0,"Su"),(1,"Mo"),(4,"Ma"),(11,"Ra"),(5,"Ju"),(6,"Sa"),(2,"Me")]:
            res, _ = swe.calc_ut(self.njd, i, swe.FLG_SWIEPH | swe.FLG_SIDEREAL)
            self.n_sid[nm] = {"lon": res[0], "dec": res[1], "lords": get_kp_lords(res[0])}
        
        cusps, _ = swe.houses_ex(self.njd, b_lat, b_lon, b'P')
        self.cusps = cusps[1:]

    def get_dasha_6(self, target_jd):
        moon_lon = self.n_sid["Mo"]["lon"]
        one_star = 800 / 60
        # 0=Ashwini(Ke), 1=Bharani(Ve)... 6=Punarvasu(Ju)
        star_idx = int(moon_lon / one_star)
        lord_id = star_idx % 9
        
        # Balance calculation
        elapsed_in_star = moon_lon - (star_idx * one_star)
        rem_deg = one_star - elapsed_in_star
        bal_yrs = (rem_deg / one_star) * DASHA_YEARS[lord_id]
        m_start = self.njd - ((DASHA_YEARS[lord_id] - bal_yrs) * 365.25)

        def recurse(start, total_days, p_idx, depth):
            if depth == 6: return []
            curr = start
            for i in range(9):
                idx = (p_idx + i) % 9
                dur = (DASHA_YEARS[idx] / 120.0) * total_days
                if curr <= target_jd < (curr + dur + 0.00001): # Adding epsilon for precision
                    return [PLANET_LIT[idx]] + recurse(curr, dur, idx, depth + 1)
                curr += dur
            return ["?"]
        return recurse(m_start, DASHA_YEARS[lord_id] * 365.25, lord_id, 0)

    def get_significators(self, pnm):
        lon = self.n_sid[pnm]["lon"]
        def find_house(p_lon):
            for i in range(12):
                h_s, h_e = self.cusps[i], self.cusps[(i+1)%12]
                if (h_s < h_e and h_s <= p_lon < h_e) or (h_s > h_e and (p_lon >= h_s or p_lon < h_e)):
                    return i + 1
            return 1
        return sorted(list(set([find_house(lon)] + OWNERSHIP.get(pnm, []))))

engine = KPEngine()

# ---------------- UI & RENDER ----------------
def get_main_table():
    t_jd = swe.julday(engine.view_date.year, engine.view_date.month, engine.view_date.day, engine.view_date.hour + engine.view_date.minute/60)
    t_data = {}
    for i, nm in [(0,"Su"),(1,"Mo"),(2,"Me"),(3,"Ve"),(4,"Ma"),(5,"Ju"),(6,"Sa"),(11,"Ra"),(10,"Ke")]:
        res, _ = swe.calc_ut(t_jd, i, swe.FLG_SWIEPH | swe.FLG_SIDEREAL)
        t_data[nm] = {"lon": res[0], "dec": res[1], "lords": get_kp_lords(res[0])}
    
    dasha = engine.get_dasha_6(t_jd)
    table = Table(title=f"6-LEVEL DASHA (Deha Level): {'-'.join(dasha)}", expand=True, border_style="cyan")
    table.add_column("Planet", style="bold yellow")
    table.add_column("Transit Lon | Dec", style="red")
    table.add_column("Natal Lon | Dec", style="green")
    table.add_column("Transit SSSL (Si-St-Su-Sl-Ss)", style="cyan")
    table.add_column("Houses (Natal)", style="magenta")

    for p in ["Su", "Mo", "Me", "Ve", "Ma", "Ju", "Sa", "Ra", "Ke"]:
        t, n = t_data[p], engine.n_sid[p]
        table.add_row(p, f"{t['lon']:.2f}° | {t['dec']:.1f}", f"{n['lon']:.2f}° | {n['dec']:.1f}", "-".join(t['lords']), ",".join(map(str, engine.get_significators(p))))
    return table

def make_layout():
    layout = Layout()
    layout.split_column(
        Layout(Panel(f"ASTRO-KP V29 | TARGET: {name} | Real-Time Syncing", style="white on blue"), size=3),
        Layout(get_main_table())
    )
    return layout

# ---------------- RUNTIME ----------------
exit_flag = False
def on_press(key):
    global exit_flag
    try:
        if key == keyboard.Key.right: engine.view_date += timedelta(minutes=15)
        elif key == keyboard.Key.left: engine.view_date -= timedelta(minutes=15)
        elif hasattr(key, 'char') and key.char == 'q': exit_flag = True
    except: pass

listener = keyboard.Listener(on_press=on_press); listener.start()

try:
    with Live(make_layout(), refresh_per_second=1, screen=True) as live:
        while not exit_flag:
            live.update(make_layout())
            time.sleep(1)
finally:
    listener.stop()