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
geolocator = Nominatim(user_agent="market_sidereal_v11")
tf = TimezoneFinder()

LORDS = ["Ke", "Ve", "Su", "Mo", "Ma", "Ra", "Ju", "Sa", "Me"]
NAKSHATRAS = [
    "Ashwini", "Bharani", "Krittika", "Rohini", "Mrigashira", "Ardra", 
    "Punarvasu", "Pushya", "Ashlesha", "Magha", "Purva Phalguni", "Uttara Phalguni", 
    "Hasta", "Chitra", "Swati", "Vishakha", "Anuradha", "Jyeshtha", 
    "Mula", "Purva Ashadha", "Uttara Ashadha", "Shravana", "Dhanishta", 
    "Shatabhisha", "Purva Bhadrapada", "Uttara Bhadrapada", "Revati"
]

RASI_NAMES = ["Ari", "Tau", "Gem", "Can", "Leo", "Vir", "Lib", "Sco", "Sag", "Cap", "Aqu", "Pis"]
ALL_PLANETS = [(0,"Su"), (1,"Mo"), (2,"Me"), (3,"Ve"), (4,"Ma"), (5,"Ju"), (6,"Sa"), (11,"Ra")]

LORD_COLORS = {
    "Ke": "bright_black", "Ve": "magenta", "Su": "bright_yellow", 
    "Mo": "white", "Ma": "red", "Ra": "blue", 
    "Ju": "yellow", "Sa": "cyan", "Me": "green"
}

# ---------------- INPUTS ----------------
console.clear()
console.print("[bold magenta]=== MARKET TRACKER: SPEED & RETROGRADE ===[/bold magenta]\n")

location_input = input("Enter Place [Scottsdale, AZ]: ") or "Scottsdale, AZ"
loc = geolocator.geocode(location_input)
lat, lon = (loc.latitude, loc.longitude) if loc else (33.4942, -111.9261)
city_name = loc.address.split(',')[0] if loc else "Scottsdale"

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
        pada = int((lon % 13.333333) / 3.333333) + 1
        return {
            "star": NAKSHATRAS[star_idx], "lord": lord, "pada": pada,
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
                p_data["Ke"] = self.get_details((res[0]+180)%360, res[3])
                p_data["Ke"]["retro"] = True
        return p_data

engine = SiderealEngine(current_dt, detected_offset)

# ---------------- UI BUILDER ----------------
def make_layout():
    data = engine.get_data()
    
    # 1. Main Table with Retrograde Symbols
    table = Table(expand=True)
    table.add_column("Planet")
    table.add_column("Star (Lord)")
    table.add_column("Pada")
    table.add_column("Rasi (Deg)")
    table.add_column("Speed (°/Day)")

    for p, d in data.items():
        motion_sym = "[bold red](R)[/]" if d['retro'] else ""
        p_style = "bold red" if d['retro'] else LORD_COLORS[d['lord']]
        
        table.add_row(
            f"[{p_style}]{p}[/] {motion_sym}",
            f"{d['star']} ({d['lord']})",
            str(d['pada']),
            f"{d['rasi']} {d['deg']:.2f}°",
            f"{d['speed']:.4f}"
        )

    # 2. Early Notification (Calculated by Speed)
    mo = data["Mo"]
    dist_to_next_pada = 3.333333 - (engine.get_data()["Mo"]["deg"] % 3.333333) if not mo['retro'] else (mo['deg'] % 3.333333)
    # Speed is degrees per day, convert to hours for better tracking
    time_to_pada = (dist_to_next_pada / mo['speed']) * 24 if mo['speed'] > 0 else 0

    notif = (
        f"[bold cyan]MOON STATUS[/]\n"
        f"Position: {mo['star']} P-{mo['pada']}\n"
        f"Speed   : {mo['speed']:.4f} °/day\n"
        f"Next Pada in: [bold green]{time_to_pada:.2f} hours[/]\n"
        f"[dim](Calculated using current velocity)[/]"
    )

    layout = Layout()
    layout.split_column(
        Layout(Panel(f"LOC: {city_name} | {engine.view_date.strftime('%d-%b-%Y %H:%M:%S')} | GMT {detected_offset:+}", style="white"), size=3),
        Layout(name="main")
    )
    layout["main"].split_row(
        Layout(Panel(table, title="Planet Motion & Degrees"), ratio=2),
        Layout(Panel(notif, title="Transit Notifications"), ratio=1)
    )
    return layout

# ---------------- CONTROLS ----------------
def on_press(key):
    try:
        if key == keyboard.Key.right: engine.view_date += timedelta(hours=1)
        elif key == keyboard.Key.left: engine.view_date -= timedelta(hours=1)
        elif key == keyboard.Key.up: engine.view_date += timedelta(minutes=15)
        elif key == keyboard.Key.down: engine.view_date -= timedelta(minutes=15)
    except: pass

keyboard.Listener(on_press=on_press).start()

# ---------------- RUN ----------------
console.clear()
sys.stdout.write("\033[?1049h")
sys.stdout.flush()

try:
    with Live(make_layout(), refresh_per_second=4, screen=True) as live:
        while True:
            live.update(make_layout())
            time.sleep(0.1)
except KeyboardInterrupt:
    pass
finally:
    sys.stdout.write("\033[?1049l")
    sys.stdout.flush()