import swisseph as swe
import os, sys, time
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

# ---------------- CONFIG & MAPPINGS ----------------
swe.set_ephe_path("./ephe")
console = Console()
geolocator = Nominatim(user_agent="market_sidereal_debug")
tf = TimezoneFinder()

LORDS = ["Ke", "Ve", "Su", "Mo", "Ma", "Ra", "Ju", "Sa", "Me"]
NAKSHATRAS = ["Ashwini", "Bharani", "Krittika", "Rohini", "Mrigashira", "Ardra", "Punarvasu", "Pushya", "Ashlesha", "Magha", "Purva Phalguni", "Uttara Phalguni", "Hasta", "Chitra", "Swati", "Vishakha", "Anuradha", "Jyeshtha", "Mula", "Purva Ashadha", "Uttara Ashadha", "Shravana", "Dhanishta", "Shatabhisha", "Purva Bhadrapada", "Uttara Bhadrapada", "Revati"]
RASI_NAMES = ["Ari", "Tau", "Gem", "Can", "Leo", "Vir", "Lib", "Sco", "Sag", "Cap", "Aqu", "Pis"]

ALL_PLANETS = [(0,"Su"), (1,"Mo"), (2,"Me"), (3,"Ve"), (4,"Ma"), (5,"Ju"), (6,"Sa"), (11,"Ra"), (7,"Ur"), (8,"Ne"), (9,"Pl")]

BULLISH_HOUSES = [1, 3, 6, 10, 11]
BEARISH_HOUSES = [5, 8, 12]

LORD_COLORS = {"Ke": "bright_black", "Ve": "magenta", "Su": "bright_yellow", "Mo": "white", "Ma": "red", "Ra": "blue", "Ju": "yellow", "Sa": "cyan", "Me": "green"}

running = True

# ---------------- INPUTS ----------------
console.clear()
console.print("[bold magenta]=== SIDEREAL DEBUGGER: LOGIC BREAKDOWN ===[/bold magenta]\n")

location_input = input("Enter Place [Scottsdale, AZ]: ") or "Scottsdale, AZ"
loc = geolocator.geocode(location_input)
lat, lon = (loc.latitude, loc.longitude) if loc else (16.1176, 80.9314)
city_name = loc.address.split(',')[0] if loc else "Scottsdale"

tz_name = tf.timezone_at(lng=lon, lat=lat)
timezone_obj = pytz.timezone(tz_name)
detected_offset = timezone_obj.utcoffset(datetime.now()).total_seconds() / 3600

current_dt = datetime.now() # Using current time for live debug

# ---------------- ENGINE ----------------
class SiderealEngine:
    def __init__(self, dt, offset_hours):
        self.view_date = dt
        self.offset = offset_hours
        swe.set_sid_mode(swe.SIDM_LAHIRI)

    def get_details(self, lon, vel):
        star_idx = int(lon / (13.333333))
        lord = LORDS[star_idx % 9]
        return {"star": NAKSHATRAS[star_idx], "lord": lord, "lon": lon, "rasi": RASI_NAMES[int(lon / 30)], "deg": lon % 30, "retro": vel < 0}

    def get_data(self):
        gmt_dt = self.view_date - timedelta(hours=self.offset)
        jd = swe.julday(gmt_dt.year, gmt_dt.month, gmt_dt.day, gmt_dt.hour + gmt_dt.minute/60 + gmt_dt.second/3600)
        flags = swe.FLG_SWIEPH | swe.FLG_SPEED | swe.FLG_SIDEREAL
        p_data = {}
        for pid, name in ALL_PLANETS:
            res, _ = swe.calc_ut(jd, pid, flags)
            p_data[name] = self.get_details(res[0], res[3])
            if name == "Ra":
                p_data["Ke"] = self.get_details((res[0]+180)%360, -res[3])
        return p_data

engine = SiderealEngine(current_dt, detected_offset)

# ---------------- UI BUILDER ----------------
def make_layout():
    data = engine.get_data()
    mo = data["Mo"]
    x_lord = mo['lord']
    y_lord = data[x_lord]['lord']
    
    xn_list = [p for p, d in data.items() if d['lord'] == x_lord and p != x_lord]
    yn_list = [p for p, d in data.items() if d['lord'] == y_lord and p != y_lord]
    all_influence = xn_list + yn_list

    # Main Degrees Table (Mirroring your image_b751b6.png)
    table = Table(expand=True)
    table.add_column("Planet")
    table.add_column("Star (Lord)")
    table.add_column("Rasi (Deg)")

    for p, d in data.items():
        row_color = LORD_COLORS.get(d['lord'], "white")
        table.add_row(f"[{row_color}]{p}[/]", f"[{row_color}]{d['star']} ({d['lord']})[/]", f"[{row_color}]{d['rasi']} {d['deg']:.2f}°[/]")

    # NEW DEBUG PANEL LOGIC
    debug = [f"[bold white]X Lord: {x_lord} | Y Lord: {y_lord}[/]\n"]
    
    if all_influence:
        debug.append("[yellow]STELLAR ACTIVE: Planet -> Moon[/]")
        for p in all_influence:
            diff = (mo['lon'] - data[p]['lon']) % 360
            h_num = int(diff / 30) + 1
            trend = "Bullish" if h_num in BULLISH_HOUSES else "Bearish" if h_num in BEARISH_HOUSES else "Side"
            debug.append(f"• {p}({data[p]['lon']:.1f}°) to Mo({mo['lon']:.1f}°)")
            debug.append(f"  Diff: {diff:.1f}° | [bold]H{h_num} ({trend})[/]")
    else:
        debug.append("[cyan]PRIMARY ACTIVE: Moon -> Planet[/]")
        for p_name in [x_lord, y_lord]:
            diff = (data[p_name]['lon'] - mo['lon']) % 360
            h_num = int(diff / 30) + 1
            debug.append(f"• Mo to {p_name}: [bold]H{h_num}[/]")

    layout = Layout()
    layout.split_column(
        Layout(Panel(f"DEBUG MODE | {engine.view_date.strftime('%H:%M:%S')}", style="white"), size=3),
        Layout(name="main")
    )
    layout["main"].split_row(
        Layout(Panel(table, title="Synchronized Groups"), ratio=1),
        Layout(Panel("\n".join(debug), title="How it's Calculating"), ratio=1)
    )
    return layout

# ---------------- CONTROLS & RUN ----------------
def on_press(key):
    global running
    if key == keyboard.Key.esc: running = False

listener = keyboard.Listener(on_press=on_press)
listener.start()

try:
    with Live(make_layout(), refresh_per_second=2, screen=True) as live:
        while running:
            live.update(make_layout())
            time.sleep(0.5)
finally:
    listener.stop()