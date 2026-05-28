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

# ---------------- INITIALIZATION ----------------
console = Console()

def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

clear_screen()

# ---------------- USER INPUTS ----------------
console.print("[bold yellow]Setup Configuration[/]")
location_input = input("Enter Place [Scottsdale, AZ]: ") or "Scottsdale, AZ"
date_str = input("Enter Date (YYYY-MM-DD) [Today]: ")
time_str = input("Enter Time (HH:MM:SS) [Now]: ")

# Handle Date/Time defaults
try:
    if not date_str:
        start_dt = datetime.now()
    else:
        full_dt_str = f"{date_str} {time_str if time_str else '12:00:00'}"
        start_dt = datetime.strptime(full_dt_str, "%Y-%m-%d %H:%M:%S")
except Exception as e:
    console.print(f"[red]Invalid format, using current time.[/]")
    start_dt = datetime.now()

# Geolocation
geolocator = Nominatim(user_agent="market_sidereal_v16")
tf = TimezoneFinder()
loc = geolocator.geocode(location_input)
lat, lon = (loc.latitude, loc.longitude) if loc else (16.1176, 80.9314)
city_name = loc.address.split(',')[0] if loc else "Scottsdale"

tz_name = tf.timezone_at(lng=lon, lat=lat)
timezone_obj = pytz.timezone(tz_name)
detected_offset = timezone_obj.utcoffset(start_dt).total_seconds() / 3600

# ---------------- ASTRO ENGINE ----------------
LORDS = ["Ke", "Ve", "Su", "Mo", "Ma", "Ra", "Ju", "Sa", "Me"]
NAKSHATRAS = ["Ashwini", "Bharani", "Krittika", "Rohini", "Mrigashira", "Ardra", "Punarvasu", "Pushya", "Ashlesha", "Magha", "Purva Phalguni", "Uttara Phalguni", "Hasta", "Chitra", "Swati", "Vishakha", "Anuradha", "Jyeshtha", "Mula", "Purva Ashadha", "Uttara Ashadha", "Shravana", "Dhanishta", "Shatabhisha", "Purva Bhadrapada", "Uttara Bhadrapada", "Revati"]
RASI_NAMES = ["Ari", "Tau", "Gem", "Can", "Leo", "Vir", "Lib", "Sco", "Sag", "Cap", "Aqu", "Pis"]
ALL_PLANETS = [(0,"Su"), (1,"Mo"), (2,"Me"), (3,"Ve"), (4,"Ma"), (5,"Ju"), (6,"Sa"), (11,"Ra")]

BULLISH_HOUSES = [1, 3, 6, 10, 11]
BEARISH_HOUSES = [5, 8, 12]
LORD_COLORS = {"Ke": "bright_black", "Ve": "magenta", "Su": "bright_yellow", "Mo": "white", "Ma": "red", "Ra": "blue", "Ju": "yellow", "Sa": "cyan", "Me": "green"}

class SiderealEngine:
    def __init__(self, dt, offset_hours):
        self.view_date = dt
        self.offset = offset_hours
        swe.set_ephe_path("./ephe")
        swe.set_sid_mode(swe.SIDM_LAHIRI)

    def get_details(self, lon, vel):
        star_idx = int(lon / (13.33333333))
        lord = LORDS[star_idx % 9]
        pada = int((lon % 13.33333333) / 3.33333333) + 1
        return {"star": NAKSHATRAS[star_idx], "lord": lord, "pada": pada, "lon": lon, "rasi": RASI_NAMES[int(lon / 30)], "deg": lon % 30, "retro": vel < 0}

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

engine = SiderealEngine(start_dt, detected_offset)
running = True

def make_layout():
    data = engine.get_data()
    mo = data["Mo"]
    x_lord, y_lord = mo['lord'], data[mo['lord']]['lord']
    
    table = Table(expand=True)
    table.add_column("Planet")
    table.add_column("Star (Lord)")
    table.add_column("Rasi (Deg)")

    for p, d in data.items():
        row_color = LORD_COLORS.get(d['lord'], "white")
        table.add_row(f"[{row_color}]{p}[/]", f"[{row_color}]{d['star']} ({d['lord']})[/]", f"[{row_color}]{d['rasi']} {d['deg']:.2f}°[/]")

    logic_panel = [f"X: {x_lord} | Y: {y_lord}\n"]
    xn = [p for p, d in data.items() if d['lord'] == x_lord and p != x_lord]
    inf = xn + [p for p, d in data.items() if d['lord'] == y_lord and p != y_lord]

    if inf:
        logic_panel.append("[bold yellow]STELLAR RULE[/]")
        for p in set(inf):
            h = int(((mo['lon'] - data[p]['lon']) % 360) / 30) + 1
            trend = "[green]Bull[/]" if h in BULLISH_HOUSES else "[red]Bear[/]" if h in BEARISH_HOUSES else "Side"
            logic_panel.append(f"{p}->Mo: H{h} ({trend})")
    else:
        logic_panel.append("[bold cyan]PRIMARY RULE[/]")
        for p_n in [x_lord, y_lord]:
            h = int(((data[p_n]['lon'] - mo['lon']) % 360) / 30) + 1
            trend = "[green]Bull[/]" if h in BULLISH_HOUSES else "[red]Bear[/]" if h in BEARISH_HOUSES else "Side"
            logic_panel.append(f"Mo->{p_n}: H{h} ({trend})")

    layout = Layout()
    layout.split_column(
        Layout(Panel(f"LOC: {city_name} | {engine.view_date.strftime('%Y-%m-%d %H:%M:%S')} | GMT {detected_offset:+}"), size=3),
        Layout(name="main")
    )
    layout["main"].split_row(
        Layout(Panel(table, title="Live Degrees"), ratio=2),
        Layout(Panel("\n".join(logic_panel), title="Market Logic"), ratio=1)
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