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
if sys.platform == "win32":
    os.system("color")

swe.set_ephe_path("./ephe")
console = Console()
geolocator = Nominatim(user_agent="market_sidereal_v14")
tf = TimezoneFinder()

LORDS = ["Ke", "Ve", "Su", "Mo", "Ma", "Ra", "Ju", "Sa", "Me"]
NAKSHATRAS = ["Ashwini", "Bharani", "Krittika", "Rohini", "Mrigashira", "Ardra", "Punarvasu", "Pushya", "Ashlesha", "Magha", "Purva Phalguni", "Uttara Phalguni", "Hasta", "Chitra", "Swati", "Vishakha", "Anuradha", "Jyeshtha", "Mula", "Purva Ashadha", "Uttara Ashadha", "Shravana", "Dhanishta", "Shatabhisha", "Purva Bhadrapada", "Uttara Bhadrapada", "Revati"]
RASI_NAMES = ["Ari", "Tau", "Gem", "Can", "Leo", "Vir", "Lib", "Sco", "Sag", "Cap", "Aqu", "Pis"]

# Explicitly defining the 12-body system for calculation
ALL_PLANETS = [
    (0,"Su"), (1,"Mo"), (2,"Me"), (3,"Ve"), (4,"Ma"), 
    (5,"Ju"), (6,"Sa"), (11,"Ra"), (7,"Ur"), (8,"Ne"), (9,"Pl")
]

# Market Logic Constants
BULLISH_PLANETS = ["Ju", "Ra", "Ne"]
BEARISH_PLANETS = ["Ma", "Sa", "Ur", "Pl"]
BULLISH_HOUSES = [1, 3, 6, 10, 11]
BEARISH_HOUSES = [5, 8, 12]
SIDEWAYS_HOUSES = [4, 7]
ANGLE_HOUSES = [2, 9]

LORD_COLORS = {
    "Ke": "bright_black", "Ve": "magenta", "Su": "bright_yellow", 
    "Mo": "white", "Ma": "red", "Ra": "blue", 
    "Ju": "yellow", "Sa": "cyan", "Me": "green"
}

running = True

# ---------------- INPUTS ----------------
console.clear()
console.print("[bold magenta]=== FULL SIDEREAL MARKET TRACKER ===[/bold magenta]\n")

# Default Scottsdale Logic
location_input = input("Enter Place [Scottsdale, AZ]: ") or "Scottsdale, AZ"
loc = geolocator.geocode(location_input)
# Default Lat/Lon per user instructions
lat, lon = (loc.latitude, loc.longitude) if loc else (16.1176, 80.9314)
city_name = loc.address.split(',')[0] if loc else "Default Loc"

tz_name = tf.timezone_at(lng=lon, lat=lat)
timezone_obj = pytz.timezone(tz_name)
detected_offset = timezone_obj.utcoffset(datetime.now()).total_seconds() / 3600

d_str = input("Date (DD/MM/YYYY) [Today]: ") or datetime.now().strftime("%d/%m/%Y")
t_str = input("Time (HH:MM:SS) [Now]: ") or datetime.now().strftime("%H:%M:%S")
current_dt = datetime.strptime(f"{d_str} {t_str}", "%d/%m/%Y %H:%M:%S")

# ---------------- ENGINE ----------------
class SiderealEngine:
    def __init__(self, dt, offset_hours):
        self.view_date = dt
        self.offset = offset_hours
        swe.set_sid_mode(swe.SIDM_LAHIRI)

    def get_details(self, lon, vel):
        star_idx = int(lon / (13.333333))
        lord = LORDS[star_idx % 9]
        return {
            "star": NAKSHATRAS[star_idx], "lord": lord, "lon": lon,
            "rasi": RASI_NAMES[int(lon / 30)], "deg": lon % 30,
            "retro": vel < 0, "speed": abs(vel)
        }

    def get_data(self):
        gmt_dt = self.view_date - timedelta(hours=self.offset)
        jd = swe.julday(gmt_dt.year, gmt_dt.month, gmt_dt.day, 
                        gmt_dt.hour + gmt_dt.minute/60 + gmt_dt.second/3600)
        
        flags = swe.FLG_SWIEPH | swe.FLG_SPEED | swe.FLG_SIDEREAL
        p_data = {}
        for pid, name in ALL_PLANETS:
            res, _ = swe.calc_ut(jd, pid, flags)
            p_data[name] = self.get_details(res[0], res[3])
            if name == "Ra":
                p_data["Ke"] = self.get_details((res[0]+180)%360, -res[3])
        return p_data

    def calculate_market_verdict(self, data):
        verdicts = []
        mo_lon = data["Mo"]["lon"]
        x_lord = data["Mo"]["lord"]
        y_lord = data[x_lord]["lord"]
        day_lord = LORDS[int((self.view_date.weekday() + 1) % 7)] # Simplified day lord

        # Find Xn and Yn
        influencers = [p for p, d in data.items() if (d['lord'] == x_lord and p != x_lord) or (d['lord'] == y_lord and p != y_lord)]

        if influencers:
            verdicts.append("[yellow]STELLAR RULE: Counting Planet -> Moon[/]")
            for p in influencers:
                # Degree based count from Planet to Moon
                diff = (mo_lon - data[p]['lon']) % 360
                h_dist = int(diff / 30) + 1
                
                # Trend logic
                trend = "Bullish" if h_dist in BULLISH_HOUSES else "Bearish" if h_dist in BEARISH_HOUSES else "Sideways"
                if data[p]['retro'] and p not in ["Ra", "Ke"]: trend = "BEARISH (Retro)"
                
                color = "green" if "Bullish" in trend else "red" if "Bearish" in trend else "white"
                verdicts.append(f"[{color}]- {p}: H{h_dist} ({trend})[/]")
        else:
            verdicts.append("[cyan]PRIMARY RULE: Counting Moon -> Planet[/]")
            for label, p_name in [("X", x_lord), ("Y", y_lord)]:
                diff = (data[p_name]['lon'] - mo_lon) % 360
                h_dist = int(diff / 30) + 1
                verdicts.append(f"- {label} ({p_name}): H{h_dist}")

        return "\n".join(verdicts)

engine = SiderealEngine(current_dt, detected_offset)

# ---------------- UI BUILDER ----------------
def make_layout():
    data = engine.get_data()
    market_txt = engine.calculate_market_verdict(data)
    
    table = Table(expand=True, title="Live Degrees & Lords")
    table.add_column("Planet")
    table.add_column("Star (Lord)")
    table.add_column("Rasi (Deg)")

    for p, d in data.items():
        row_color = LORD_COLORS.get(d['lord'], "white")
        motion = "[red](R)[/]" if d['retro'] else ""
        table.add_row(f"[{row_color}]{p}[/] {motion}", f"{d['star']} ({d['lord']})", f"{d['rasi']} {d['deg']:.2f}°")

    layout = Layout()
    layout.split_column(
        Layout(Panel(f"LOC: {city_name} | {engine.view_date.strftime('%d-%b-%Y %H:%M:%S')}", style="white"), size=3),
        Layout(name="main")
    )
    layout["main"].split_row(
        Layout(Panel(table), ratio=2),
        Layout(Panel(market_txt, title="Market Verdict Logic"), ratio=1)
    )
    return layout

# ---------------- CONTROLS & RUN ----------------
def on_press(key):
    global running
    try:
        if key == keyboard.Key.right: engine.view_date += timedelta(hours=1)
        elif key == keyboard.Key.left: engine.view_date -= timedelta(hours=1)
        elif key == keyboard.Key.esc: running = False
    except: pass

listener = keyboard.Listener(on_press=on_press)
listener.start()

try:
    with Live(make_layout(), refresh_per_second=4, screen=True) as live:
        while running:
            live.update(make_layout())
            time.sleep(0.1)
finally:
    listener.stop()