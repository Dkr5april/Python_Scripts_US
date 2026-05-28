import swisseph as swe
import os, sys, time, logging
from datetime import datetime, timedelta
from pynput import keyboard
from geopy.geocoders import Nominatim
from timezonefinder import TimezoneFinder
import pytz
from rich.live import Live
from rich.table import Table
from rich.console import Console
from rich.layout import Layout
from rich.panel import Panel
from fpdf import FPDF

# ---------------- CONFIGURATION & MAPPING ----------------
BULLISH_HOUSES = [1, 3, 6, 10, 11]
BEARISH_HOUSES = [5, 8, 12]
PLANET_NATURE = {
    "Su": "BULLISH", "Mo": "BULLISH", "Ju": "BULLISH", "Ve": "BULLISH",
    "Ma": "BEARISH", "Sa": "BEARISH", "Ra": "BEARISH", "Ke": "BEARISH",
    "Me": "NEUTRAL", "Ur": "NEUTRAL", "Ne": "NEUTRAL", "Pl": "BEARISH"
}
LORD_COLORS = {"Ke": "bright_black", "Ve": "magenta", "Su": "bright_yellow", "Mo": "white", "Ma": "red", "Ra": "blue", "Ju": "yellow", "Sa": "cyan", "Me": "green"}
LORDS = ["Ke", "Ve", "Su", "Mo", "Ma", "Ra", "Ju", "Sa", "Me"]
NAKSHATRAS = ["Ashwini", "Bharani", "Krittika", "Rohini", "Mrigashira", "Ardra", "Punarvasu", "Pushya", "Ashlesha", "Magha", "Purva Phalguni", "Uttara Phalguni", "Hasta", "Chitra", "Swati", "Vishakha", "Anuradha", "Jyeshtha", "Mula", "Purva Ashadha", "Uttara Ashadha", "Shravana", "Dhanishta", "Shatabhisha", "Purva Bhadrapada", "Uttara Bhadrapada", "Revati"]
RASI_NAMES = ["Ari", "Tau", "Gem", "Can", "Leo", "Vir", "Lib", "Sco", "Sag", "Cap", "Aqu", "Pis"]
ALL_PLANETS = [(0,"Su"), (1,"Mo"), (2,"Me"), (3,"Ve"), (4,"Ma"), (5,"Ju"), (6,"Sa"), (11,"Ra"), (7,"Ur"), (8,"Ne"), (9,"Pl")]

console = Console()

# ---------------- CORE CALCULATION FUNCTIONS ----------------
def get_precise_house(source_lon, target_lon):
    return int(((target_lon - source_lon) % 360) / 30) + 1

def get_snapshot(engine, dt):
    # Temporarily set engine date to calculate specific time
    original_dt = engine.view_date
    engine.view_date = dt
    data = engine.get_data()
    engine.view_date = original_dt
    return data

def track_movements(engine):
    """Checks for the NEXT Sign or Star change in the next 6 hours."""
    moves = []
    now_data = engine.get_data()
    
    # Track which planets we've already found a transition for
    found_transition = set()

    # Check every 1 minute for high precision over the next 6 hours (360 mins)
    for mins in range(1, 361):
        future_dt = engine.view_date + timedelta(minutes=mins)
        future_data = get_snapshot(engine, future_dt)
        
        for p in now_data:
            # Create a unique key for the planet and the type of change
            sign_key = f"{p}_sign"
            star_key = f"{p}_star"

            # Check Sign Change - Only if not already found
            if sign_key not in found_transition and now_data[p]['rasi'] != future_data[p]['rasi']:
                moves.append(f"[bold cyan]{p}[/] enters [bold]{future_data[p]['rasi']}[/] in {mins}m")
                found_transition.add(sign_key)
            
            # Check Star Change - Only if not already found
            if star_key not in found_transition and now_data[p]['star'] != future_data[p]['star']:
                moves.append(f"[bold yellow]{p}[/] enters [bold]{future_data[p]['star']}[/] in {mins}m")
                found_transition.add(star_key)
                
    return moves if moves else ["No transitions in next 6h"]

def evaluate_market(data):
    total_score, max_possible = 0, 0
    mo_lon = data["Mo"]['lon']
    x_lord, y_lord = data["Mo"]['lord'], data[data["Mo"]['lord']]['lord']
    
    key_planets = [p for p in [x_lord, y_lord] if data[p]['lord'] == p]
    all_influence = list(set([p for p, d in data.items() if d['lord'] in [x_lord, y_lord] and p not in ["Mo"] + key_planets]))

    results = []
    if key_planets:
        for kp in set(key_planets):
            n = PLANET_NATURE.get(kp, "NEUTRAL")
            total_score += (10 if n == "BULLISH" else -10 if n == "BEARISH" else 0)
            max_possible += 10
            results.append(f"[magenta]KEY: {kp} ({n})[/]")

    for p in all_influence:
        h = get_precise_house(data[p]['lon'], mo_lon)
        h_t = "BULLISH" if h in BULLISH_HOUSES else "BEARISH" if h in BEARISH_HOUSES else "SIDEWAYS"
        p_n = PLANET_NATURE.get(p, "NEUTRAL")
        p_v = (2 if h_t == "BULLISH" else -2 if h_t == "BEARISH" else 0) + (2 if p_n == "BULLISH" else -2 if p_n == "BEARISH" else 0)
        total_score, max_possible = total_score + p_v, max_possible + 4
        results.append(f"[{'green' if p_v > 0 else 'red' if p_v < 0 else 'white'}]{p} ({p_n})->H{h}[/]")

    perc = (total_score / max_possible * 100) if max_possible != 0 else 0
    abs_p = abs(int(perc))
    strength = "EXTREMELY STRONG" if abs_p >= 80 else "STRONG" if abs_p >= 40 else "MILD" if abs_p > 10 else "NEUTRAL"
    color = "green" if perc > 10 else "red" if perc < -10 else "white"
    results.append("─" * 15)
    results.append(f"[bold {color}]{abs_p}% {'BULLISH' if perc > 10 else 'BEARISH' if perc < -10 else 'NEUTRAL'} ({strength})[/]")
    return results

# ---------------- ENGINE & MAIN ----------------
class SiderealEngine:
    def __init__(self, dt, offset):
        self.view_date, self.offset = dt, offset
        swe.set_sid_mode(swe.SIDM_LAHIRI)

    def get_data(self):
        gmt_dt = self.view_date - timedelta(hours=self.offset)
        jd = swe.julday(gmt_dt.year, gmt_dt.month, gmt_dt.day, gmt_dt.hour + gmt_dt.minute/60)
        p_data = {}
        for pid, name in ALL_PLANETS:
            res, _ = swe.calc_ut(jd, pid, swe.FLG_SWIEPH | swe.FLG_SIDEREAL)
            idx = int(res[0] / 13.33333333)
            p_data[name] = {"star": NAKSHATRAS[idx], "lord": LORDS[idx % 9], "lon": res[0], "rasi": RASI_NAMES[int(res[0] / 30)], "deg": res[0] % 30}
            if name == "Ra":
                k_lon = (res[0] + 180) % 360
                k_idx = int(k_lon/13.33333333)
                p_data["Ke"] = {"star": NAKSHATRAS[k_idx], "lord": LORDS[k_idx%9], "lon": k_lon, "rasi": RASI_NAMES[int(k_lon/30)], "deg": k_lon % 30}
        return p_data

# STARTUP
os.system('cls' if os.name == 'nt' else 'clear')
loc_input = input("Enter Place [Scottsdale, AZ]: ") or "Scottsdale, AZ"
date_input = input("Enter Start Date (YYYY-MM-DD) [Today]: ")
mode = input("Select Mode: [1] Live View [2] 30-Day Poster: ")

start_dt = datetime.strptime(date_input, "%Y-%m-%d").replace(hour=9, minute=30) if date_input else datetime.now().replace(hour=9, minute=30, second=0, microsecond=0)
loc = Nominatim(user_agent="market_v21").geocode(loc_input)
lat, lon = (loc.latitude, loc.longitude) if loc else (16.1176, 80.9314)
offset = pytz.timezone(TimezoneFinder().timezone_at(lng=lon, lat=lat)).utcoffset(start_dt).total_seconds() / 3600
engine = SiderealEngine(start_dt, offset)

if mode == "1":
    running = True
    def make_layout():
        data = engine.get_data()
        moves = track_movements(engine)
        table = Table(expand=True)
        table.add_column("Planet"); table.add_column("Star (Lord)")
        for p, d in data.items(): table.add_row(f"[{LORD_COLORS.get(d['lord'])}]{p}[/]", f"{d['star']} ({d['lord']})")
        
        layout = Layout()
        layout.split_column(Layout(Panel(f"{loc_input} | {engine.view_date}"), size=3), Layout(name="main"))
        layout["main"].split_row(
            Layout(Panel(table, title="Degrees"), ratio=1),
            Layout(name="right", ratio=1)
        )
        layout["right"].split_column(
            Layout(Panel("\n".join(evaluate_market(data)), title="Market Logic")),
            Layout(Panel("\n".join(moves), title="Next 6h Transitions"), size=10)
        )
        return layout

    def on_press(key):
        global running
        if key == keyboard.Key.right: engine.view_date += timedelta(minutes=15)
        elif key == keyboard.Key.left: engine.view_date -= timedelta(minutes=15)
        elif key == keyboard.Key.up: engine.view_date += timedelta(days=1)
        elif key == keyboard.Key.down: engine.view_date -= timedelta(days=1)
        elif key == keyboard.Key.esc: running = False

    keyboard.Listener(on_press=on_press).start()
    with Live(make_layout(), refresh_per_second=1, screen=True) as live:
        while running:
            live.update(make_layout())
            time.sleep(1)