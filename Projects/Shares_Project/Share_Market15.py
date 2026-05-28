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

# ---------------- LOGGING SETUP ----------------
logging.basicConfig(
    filename='debug_log.txt',
    level=logging.INFO,
    format='%(asctime)s | %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

swe.set_ephe_path("./ephe")
console = Console()
geolocator = Nominatim(user_agent="market_sidereal_v16")
tf = TimezoneFinder()

LORDS = ["Ke", "Ve", "Su", "Mo", "Ma", "Ra", "Ju", "Sa", "Me"]
NAKSHATRAS = ["Ashwini", "Bharani", "Krittika", "Rohini", "Mrigashira", "Ardra", "Punarvasu", "Pushya", "Ashlesha", "Magha", "Purva Phalguni", "Uttara Phalguni", "Hasta", "Chitra", "Swati", "Vishakha", "Anuradha", "Jyeshtha", "Mula", "Purva Ashadha", "Uttara Ashadha", "Shravana", "Dhanishta", "Shatabhisha", "Purva Bhadrapada", "Uttara Bhadrapada", "Revati"]
RASI_NAMES = ["Ari", "Tau", "Gem", "Can", "Leo", "Vir", "Lib", "Sco", "Sag", "Cap", "Aqu", "Pis"]
ALL_PLANETS = [(0,"Su"), (1,"Mo"), (2,"Me"), (3,"Ve"), (4,"Ma"), (5,"Ju"), (6,"Sa"), (11,"Ra"), (7,"Ur"), (8,"Ne"), (9,"Pl")]

BULLISH_HOUSES = [1, 3, 6, 10, 11]
BEARISH_HOUSES = [5, 8, 12]
LORD_COLORS = {"Ke": "bright_black", "Ve": "magenta", "Su": "bright_yellow", "Mo": "white", "Ma": "red", "Ra": "blue", "Ju": "yellow", "Sa": "cyan", "Me": "green"}

running = True

# ---------------- INPUTS (Default to Scottsdale per your profile) ----------------
console.clear()
location_input = "Scottsdale, AZ" # Default value
loc = geolocator.geocode(location_input)
lat, lon = (loc.latitude, loc.longitude) if loc else (16.1176, 80.9314)
city_name = loc.address.split(',')[0] if loc else "Scottsdale"

tz_name = tf.timezone_at(lng=lon, lat=lat)
timezone_obj = pytz.timezone(tz_name)
detected_offset = timezone_obj.utcoffset(datetime.now()).total_seconds() / 3600

class SiderealEngine:
    def __init__(self, dt, offset_hours):
        self.view_date = dt
        self.offset = offset_hours
        swe.set_sid_mode(swe.SIDM_LAHIRI)

    def get_details(self, lon, vel):
        star_idx = int(lon / (13.33333333))
        lord = LORDS[star_idx % 9]
        pada = int((lon % 13.33333333) / 3.33333333) + 1
        return {"star": NAKSHATRAS[star_idx], "lord": lord, "pada": pada, "lon": lon, "rasi": RASI_NAMES[int(lon / 30)], "deg": lon % 30, "retro": vel < 0, "speed": abs(vel)}

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
                p_data["Ke"]["retro"] = True
        return p_data

engine = SiderealEngine(datetime.now(), detected_offset)

def make_layout():
    data = engine.get_data()
    mo = data["Mo"]
    x_lord, y_lord = mo['lord'], data[mo['lord']]['lord']
    
    table = Table(expand=True, border_style="dim")
    table.add_column("Planet")
    table.add_column("Star (Lord)")
    table.add_column("Rasi (Deg)")
    table.add_column("Speed")

    for p, d in data.items():
        if p in ["Ur", "Ne", "Pl"]: continue # Keep table clean
        row_color = LORD_COLORS.get(d['lord'], "white")
        motion = "[bold red](R)[/]" if d['retro'] else ""
        table.add_row(f"[{row_color}]{p}[/] {motion}", f"[{row_color}]{d['star']} ({d['lord']})[/]", f"[{row_color}]{d['rasi']} {d['deg']:.2f}°[/]", f"[{row_color}]{d['speed']:.4f}[/]")

    logic_text = [f"X-Lord: [bold]{x_lord}[/] | Y-Lord: [bold]{y_lord}[/]\n"]
    xn = [p for p, d in data.items() if d['lord'] == x_lord and p != x_lord and p not in ["Ur", "Ne", "Pl"]]
    yn = [p for p, d in data.items() if d['lord'] == y_lord and p != y_lord and p not in ["Ur", "Ne", "Pl"]]
    inf = xn + yn

    if inf:
        logic_text.append("[bold yellow]STELLAR RULE (Planet -> Moon)[/]")
        for p in inf:
            diff = (mo['lon'] - data[p]['lon']) % 360
            h = int(diff / 30) + 1
            trend = "[green]Bull[/]" if h in BULLISH_HOUSES else "[red]Bear[/]" if h in BEARISH_HOUSES else "Side"
            logic_text.append(f" {p} in H{h} from Mo: {trend}")
    else:
        logic_text.append("[bold cyan]PRIMARY RULE (Moon -> Planet)[/]")
        for lbl, p_n in [("X", x_lord), ("Y", y_lord)]:
            diff = (data[p_n]['lon'] - mo['lon']) % 360
            h = int(diff / 30) + 1
            trend = "[green]Bull[/]" if h in BULLISH_HOUSES else "[red]Bear[/]" if h in BEARISH_HOUSES else "Side"
            logic_text.append(f" {lbl}({p_n}): House {h} ({trend})")

    layout = Layout()
    layout.split_column(
        Layout(Panel(f"LOC: {city_name} | {engine.view_date.strftime('%d-%b-%Y %H:%M:%S')} | GMT {detected_offset:+}\n[dim]Arrows: Time Change | D/B: Day Change | N: Now | ESC: Exit[/]", style="bright_blue"), size=4),
        Layout(name="main")
    )
    layout["main"].split_row(
        Layout(Panel(table, title="Live Degrees"), ratio=2),
        Layout(Panel("\n".join(logic_text), title="Market Logic"), ratio=1)
    )
    return layout

def on_press(key):
    global running
    try:
        if key == keyboard.Key.right: engine.view_date += timedelta(hours=1)
        elif key == keyboard.Key.left: engine.view_date -= timedelta(hours=1)
        elif key == keyboard.Key.up: engine.view_date += timedelta(minutes=15)
        elif key == keyboard.Key.down: engine.view_date -= timedelta(minutes=15)
        elif hasattr(key, 'char'):
            if key.char == 'd': engine.view_date += timedelta(days=1)
            elif key.char == 'b': engine.view_date -= timedelta(days=1)
            elif key.char == 'n': engine.view_date = datetime.now()
        elif key == keyboard.Key.esc: running = False
    except: pass

listener = keyboard.Listener(on_press=on_press)
listener.start()

try:
    # Removed screen=True to stop flickering
    with Live(make_layout(), refresh_per_second=4) as live:
        while running:
            live.update(make_layout())
            time.sleep(0.1)
finally:
    listener.stop()
    console.clear()