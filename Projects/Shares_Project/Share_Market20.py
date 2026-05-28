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

# ---------------- CONFIGURATION & MAPPING ----------------
BULLISH_HOUSES = [1, 3, 6, 10, 11]
BEARISH_HOUSES = [5, 8, 12]
SIDEWAYS_HOUSES = [4, 7, 2, 9]

PLANET_NATURE = {
    "Su": "BULLISH", "Mo": "BULLISH", "Ju": "BULLISH", "Ve": "BULLISH",
    "Ma": "BEARISH", "Sa": "BEARISH", "Ra": "BEARISH", "Ke": "BEARISH",
    "Me": "NEUTRAL", "Ur": "NEUTRAL", "Ne": "NEUTRAL", "Pl": "BEARISH"
}

LORD_COLORS = {
    "Ke": "bright_black", "Ve": "magenta", "Su": "bright_yellow", 
    "Mo": "white", "Ma": "red", "Ra": "blue", 
    "Ju": "yellow", "Sa": "cyan", "Me": "green"
}

LORDS = ["Ke", "Ve", "Su", "Mo", "Ma", "Ra", "Ju", "Sa", "Me"]
NAKSHATRAS = ["Ashwini", "Bharani", "Krittika", "Rohini", "Mrigashira", "Ardra", "Punarvasu", "Pushya", "Ashlesha", "Magha", "Purva Phalguni", "Uttara Phalguni", "Hasta", "Chitra", "Swati", "Vishakha", "Anuradha", "Jyeshtha", "Mula", "Purva Ashadha", "Uttara Ashadha", "Shravana", "Dhanishta", "Shatabhisha", "Purva Bhadrapada", "Uttara Bhadrapada", "Revati"]
RASI_NAMES = ["Ari", "Tau", "Gem", "Can", "Leo", "Vir", "Lib", "Sco", "Sag", "Cap", "Aqu", "Pis"]
ALL_PLANETS = [(0,"Su"), (1,"Mo"), (2,"Me"), (3,"Ve"), (4,"Ma"), (5,"Ju"), (6,"Sa"), (11,"Ra"), (7,"Ur"), (8,"Ne"), (9,"Pl")]

logging.basicConfig(filename='debug_log.txt', level=logging.INFO, format='%(asctime)s | %(message)s')

# ---------------- CORE CALCULATION FUNCTIONS ----------------
def get_precise_house(source_lon, target_lon, direction="from_moon"):
    diff = (target_lon - source_lon) % 360
    return int(diff / 30) + 1

def evaluate_market(data, view_date):
    verdicts = []
    total_score = 0
    max_possible_abs_score = 0
    
    mo = data["Mo"]
    mo_lon = mo['lon']
    x_lord = mo['lord']
    y_lord = data[x_lord]['lord']
    
    key_planets = []
    if data[x_lord]['lord'] == x_lord: key_planets.append(x_lord)
    if data[y_lord]['lord'] == y_lord: key_planets.append(y_lord)
    key_planets = list(set(key_planets))

    xn_list = [p for p, d in data.items() if d['lord'] == x_lord and p != x_lord and p != "Mo"]
    yn_list = [p for p, d in data.items() if d['lord'] == y_lord and p != y_lord and p != "Mo"]
    all_influence = list(set(xn_list + yn_list))

    # 1. KEY PLANETS (Weight: 10)
    if key_planets:
        verdicts.append("[bold magenta]KEY PLANET RULE[/]")
        for kp in key_planets:
            nature = PLANET_NATURE.get(kp, "NEUTRAL")
            val = 10 if nature == "BULLISH" else -10 if nature == "BEARISH" else 0
            total_score += val
            max_possible_abs_score += 10
            verdicts.append(f"- {kp} ({nature}) is KEY")

    # 2. STELLAR INFLUENCERS (Weight: 4 per planet)
    if all_influence:
        verdicts.append("[bold yellow]STELLAR RULE[/]")
        for p in all_influence:
            h_dist = get_precise_house(data[p]['lon'], mo_lon, direction="to_moon")
            h_trend = "BULLISH" if h_dist in BULLISH_HOUSES else "BEARISH" if h_dist in BEARISH_HOUSES else "SIDEWAYS"
            p_nature = PLANET_NATURE.get(p, "NEUTRAL")
            
            p_val = 0
            if h_trend == "BULLISH": p_val += 2
            elif h_trend == "BEARISH": p_val -= 2
            
            if p_nature == "BULLISH": p_val += 2
            elif p_nature == "BEARISH": p_val -= 2
            
            total_score += p_val
            max_possible_abs_score += 4
            color = "green" if p_val > 0 else "red" if p_val < 0 else "white"
            verdicts.append(f"[{color}]- {p} ({p_nature}) -> H{h_dist}[/]")

    # 3. PRIMARY FALLBACK (Weight: 5)
    elif not key_planets:
        verdicts.append("[bold cyan]PRIMARY RULE[/]")
        for p_name in [x_lord, y_lord]:
            h_dist = get_precise_house(mo_lon, data[p_name]['lon'], direction="from_moon")
            if h_dist in BULLISH_HOUSES: total_score += 5
            elif h_dist in BEARISH_HOUSES: total_score -= 5
            max_possible_abs_score += 5
            verdicts.append(f"- {p_name}: H{h_dist}")

    # --- FINAL CONCLUSION ENGINE ---
    verdicts.append("─" * 20)
    if max_possible_abs_score == 0:
        verdicts.append("[bold white]CONCLUSION: 50% NEUTRAL (NO DATA)[/]")
    else:
        # Calculate percentage based on the spread
        percentage = (total_score / max_possible_abs_score) * 100
        abs_p = abs(int(percentage))
        
        if percentage >= 80: strength = "EXTREMELY STRONG"
        elif percentage >= 40: strength = "STRONG"
        elif percentage > 10: strength = "MILD"
        elif percentage <= -80: strength = "EXTREMELY STRONG"
        elif percentage <= -40: strength = "STRONG"
        elif percentage < -10: strength = "MILD"
        else: strength = "NEUTRAL / VOLATILE"

        if percentage > 10:
            verdicts.append(f"[bold green]CONCLUSION: {abs_p}% BULLISH ({strength})[/]")
        elif percentage < -10:
            verdicts.append(f"[bold red]CONCLUSION: {abs_p}% BEARISH ({strength})[/]")
        else:
            verdicts.append(f"[bold white]CONCLUSION: 50% {strength}[/]")

    return verdicts

# ---------------- ENGINE & DISPLAY (V18) ----------------
class SiderealEngine:
    def __init__(self, dt, offset_hours):
        self.view_date = dt
        self.offset = offset_hours
        swe.set_ephe_path("./ephe")
        swe.set_sid_mode(swe.SIDM_LAHIRI)

    def get_details(self, lon, vel):
        star_idx = int(lon / (13.33333333))
        lord = LORDS[star_idx % 9]
        return {"star": NAKSHATRAS[star_idx], "lord": lord, "lon": lon, "rasi": RASI_NAMES[int(lon / 30)], "deg": lon % 30, "retro": vel < 0}

    def get_data(self):
        gmt_dt = self.view_date - timedelta(hours=self.offset)
        jd = swe.julday(gmt_dt.year, gmt_dt.month, gmt_dt.day, gmt_dt.hour + gmt_dt.minute/60)
        p_data = {}
        for pid, name in ALL_PLANETS:
            res, _ = swe.calc_ut(jd, pid, swe.FLG_SWIEPH | swe.FLG_SPEED | swe.FLG_SIDEREAL)
            p_data[name] = self.get_details(res[0], res[3])
            if name == "Ra":
                p_data["Ke"] = self.get_details((res[0]+180)%360, -res[3])
        return p_data

def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

clear_screen()
loc_input = input("Enter Place [Scottsdale, AZ]: ") or "Scottsdale, AZ"
date_input = input("Enter Date (YYYY-MM-DD) [Today]: ")
time_input = input("Enter Time (HH:MM:SS) [Now]: ")

try:
    start_dt = datetime.strptime(f"{date_input} {time_input}", "%Y-%m-%d %H:%M:%S") if date_input else datetime.now()
except: start_dt = datetime.now()

geolocator = Nominatim(user_agent="market_sidereal_v18")
loc = geolocator.geocode(loc_input)
lat, lon = (loc.latitude, loc.longitude) if loc else (16.1176, 80.9314)
tz_name = TimezoneFinder().timezone_at(lng=lon, lat=lat)
detected_offset = pytz.timezone(tz_name).utcoffset(start_dt).total_seconds() / 3600

engine = SiderealEngine(start_dt, detected_offset)
running = True

def make_layout():
    data = engine.get_data()
    table = Table(expand=True)
    table.add_column("Planet")
    table.add_column("Star (Lord)")
    table.add_column("Rasi (Deg)")

    for p, d in data.items():
        row_color = LORD_COLORS.get(d['lord'], "white")
        table.add_row(f"[{row_color}]{p}[/]", f"[{row_color}]{d['star']} ({d['lord']})[/]", f"[{row_color}]{d['rasi']} {d['deg']:.2f}°[/]")

    layout = Layout()
    layout.split_column(
        Layout(Panel(f"{loc_input} | {engine.view_date.strftime('%Y-%m-%d %H:%M:%S')} | GMT {detected_offset:+}"), size=3),
        Layout(name="main")
    )
    layout["main"].split_row(
        Layout(Panel(table, title="Live Degrees"), ratio=2),
        Layout(Panel("\n".join(evaluate_market(data, engine.view_date)), title="Market Logic"), ratio=1)
    )
    return layout

def on_press(key):
    global running
    try:
        if key == keyboard.Key.right: engine.view_date += timedelta(hours=1)
        elif key == keyboard.Key.left: engine.view_date -= timedelta(hours=1)
        elif key == keyboard.Key.up: engine.view_date += timedelta(days=1)
        elif key == keyboard.Key.down: engine.view_date -= timedelta(days=1)
        elif key == keyboard.Key.esc: running = False
    except: pass

listener = keyboard.Listener(on_press=on_press)
listener.start()

clear_screen()
try:
    with Live(make_layout(), refresh_per_second=2, screen=True) as live:
        while running:
            live.update(make_layout())
            time.sleep(0.5)
finally:
    listener.stop()
    clear_screen()