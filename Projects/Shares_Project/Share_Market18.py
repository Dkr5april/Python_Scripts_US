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
BULLISH_PLANETS = ["Ju", "Ra", "Ne"]
BEARISH_PLANETS = ["Ma", "Sa", "Ur", "Pl"]
SIDEWAYS_PLANETS = ["Su", "Mo", "Me", "Ve", "Ke"]

BULLISH_HOUSES = [1, 3, 6, 10, 11]
BEARISH_HOUSES = [5, 8, 12]
SIDEWAYS_HOUSES = [4, 7]
ANGLE_HOUSES = [2, 9]

LORD_COLORS = {
    "Ke": "bright_black", "Ve": "magenta", "Su": "bright_yellow", 
    "Mo": "white", "Ma": "red", "Ra": "blue", 
    "Ju": "yellow", "Sa": "cyan", "Me": "green"
}

LORDS = ["Ke", "Ve", "Su", "Mo", "Ma", "Ra", "Ju", "Sa", "Me"]
NAKSHATRAS = ["Ashwini", "Bharani", "Krittika", "Rohini", "Mrigashira", "Ardra", "Punarvasu", "Pushya", "Ashlesha", "Magha", "Purva Phalguni", "Uttara Phalguni", "Hasta", "Chitra", "Swati", "Vishakha", "Anuradha", "Jyeshtha", "Mula", "Purva Ashadha", "Uttara Ashadha", "Shravana", "Dhanishta", "Shatabhisha", "Purva Bhadrapada", "Uttara Bhadrapada", "Revati"]
RASI_NAMES = ["Ari", "Tau", "Gem", "Can", "Leo", "Vir", "Lib", "Sco", "Sag", "Cap", "Aqu", "Pis"]
ALL_PLANETS = [(0,"Su"), (1,"Mo"), (2,"Me"), (3,"Ve"), (4,"Ma"), (5,"Ju"), (6,"Sa"), (11,"Ra"), (7,"Ur"), (8,"Ne"), (9,"Pl")]

# ---------------- LOGGING SETUP ----------------
logging.basicConfig(filename='debug_log.txt', level=logging.INFO, format='%(asctime)s | %(message)s')
console = Console()

def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

# ---------------- CORE CALCULATION FUNCTIONS ----------------
def get_precise_house(source_lon, target_lon, direction="to_moon"):
    """
    FIXED: To find house distance, always subtract Source from Target.
    'to_moon': Source=Planet, Target=Moon
    'from_moon': Source=Moon, Target=Planet
    """
    if direction == "to_moon":
        # Target is Moon, Source is Planet
        diff = (target_lon - source_lon) % 360
    else:
        # Target is Planet, Source is Moon
        # CHANGED: target_lon (Planet) - source_lon (Moon)
        diff = (target_lon - source_lon) % 360
        
    return int(diff / 30) + 1

def evaluate_market(data, view_date):
    verdicts = []
    mo = data["Mo"]
    mo_lon = mo['lon']
    
    # Day Lord (Simple calculation based on weekday)
    weekday_to_lord = {0: "Mo", 1: "Ma", 2: "Me", 3: "Ju", 4: "Ve", 5: "Sa", 6: "Su"}
    day_lord = weekday_to_lord[view_date.weekday()]
    
    x_lord = mo['lord']
    y_lord = data[x_lord]['lord']
    
    xn_list = [p for p, d in data.items() if d['lord'] == x_lord and p != x_lord and p not in ["Ur", "Ne", "Pl"]]
    yn_list = [p for p, d in data.items() if d['lord'] == y_lord and p != y_lord and p not in ["Ur", "Ne", "Pl"]]
    all_influence = list(set(xn_list + yn_list))

    if all_influence:
        verdicts.append("[bold yellow]STELLAR RULE: Count Planet -> Moon[/]")
        for p in all_influence:
            h_dist = get_precise_house(data[p]['lon'], mo_lon, direction="to_moon")
            
            if h_dist in BULLISH_HOUSES: trend = "BULLISH"
            elif h_dist in BEARISH_HOUSES: trend = "BEARISH"
            elif h_dist in SIDEWAYS_HOUSES: trend = "SIDEWAYS"
            else: trend = "ANGLE (Key)"
            
            is_retro = data[p].get('retro', False) and p not in ["Ra", "Ke"]
            final_sentiment = "BEARISH (Retro)" if is_retro else trend
            color = "red" if "BEARISH" in final_sentiment else "green" if "BULLISH" in final_sentiment else "white"
            
            verdicts.append(f"[{color}]- {p} (Inf) -> Moon: H{h_dist} ({final_sentiment})[/]")
            logging.info(f"STELLAR | {p} at {data[p]['lon']:.2f} -> Mo at {mo_lon:.2f} | H{h_dist}")
            
    else:
        verdicts.append("[bold cyan]PRIMARY RULE: Count Moon -> Planet[/]")
        for label, p_name in [("X", x_lord), ("Y", y_lord)]:
            # Source is Moon, Target is Planet
            h_dist = get_precise_house(mo_lon, data[p_name]['lon'], direction="from_moon")
            
            is_bullish_rule = (day_lord == p_name) or (p_name == "Mo")
            style = "bold green" if is_bullish_rule else "white"
            
            verdicts.append(f"[{style}]- {label} ({p_name}) Moon -> {p_name}: H{h_dist}[/]")
            logging.info(f"PRIMARY | Mo at {mo_lon:.2f} -> {p_name} at {data[p_name]['lon']:.2f} | H{h_dist}")

    # RULE 5: OWN STAR
    for p_name in [x_lord, y_lord]:
        if data[p_name]['lord'] == p_name:
            h_dist = get_precise_house(data[p_name]['lon'], mo_lon, direction="to_moon")
            verdicts.append(f"[magenta]RULE 5: {p_name} Own Star (Key) H{h_dist}[/]")

    return verdicts

# ---------------- ENGINE & DISPLAY ----------------
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

# ---------------- STARTUP ----------------
clear_screen()
loc_input = input("Enter Place [Scottsdale, AZ]: ") or "Scottsdale, AZ"
date_input = input("Enter Date (YYYY-MM-DD) [Today]: ")
time_input = input("Enter Time (HH:MM:SS) [Now]: ")

try:
    if not date_input: start_dt = datetime.now()
    else: start_dt = datetime.strptime(f"{date_input} {time_input if time_input else '12:00:00'}", "%Y-%m-%d %H:%M:%S")
except: start_dt = datetime.now()

geolocator = Nominatim(user_agent="market_sidereal_v16")
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