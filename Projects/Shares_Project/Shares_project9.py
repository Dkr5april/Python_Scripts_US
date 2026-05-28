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
geolocator = Nominatim(user_agent="market_sidereal_v13")
tf = TimezoneFinder()

# Vimshottari Star Lords
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

# Color Mapping for the 9 Groups
LORD_COLORS = {
    "Ke": "bright_black", "Ve": "magenta", "Su": "bright_yellow", 
    "Mo": "white", "Ma": "red", "Ra": "blue", 
    "Ju": "yellow", "Sa": "cyan", "Me": "green"
}

running = True

# ---------------- INPUTS ----------------
console.clear()
console.print("[bold magenta]=== SIDEREAL MARKET TRACKER: LORD COLOR GROUPS ===[/bold magenta]\n")

# Defaulting to Scottsdale, AZ
location_input = input("Enter Place [Scottsdale, AZ]: ") or "Scottsdale, AZ"
loc = geolocator.geocode(location_input)
lat, lon = (loc.latitude, loc.longitude) if loc else (33.4942, -111.9261)
city_name = loc.address.split(',')[0] if loc else "Scottsdale"

tz_name = tf.timezone_at(lng=lon, lat=lat)
timezone_obj = pytz.timezone(tz_name)
# Arizona stays at GMT-7
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
    
    table = Table(expand=True, title="Planetary Grouping by Star Lord")
    table.add_column("Planet")
    table.add_column("Star (Lord)")
    table.add_column("Pada")
    table.add_column("Rasi (Deg)")
    table.add_column("Speed")

    for p, d in data.items():
        # Get the color based on the Star Lord
        row_color = LORD_COLORS[d['lord']]
        motion_sym = "[bold italic red](R)[/]" if d['retro'] else ""
        
        # Apply the Star Lord's color to the entire row for clarity
        table.add_row(
            f"[{row_color}]{p}[/] {motion_sym}",
            f"[{row_color}]{d['star']} ({d['lord']})[/]",
            f"[{row_color}]{d['pada']}[/]",
            f"[{row_color}]{d['rasi']} {d['deg']:.2f}°[/]",
            f"[{row_color}]{d['speed']:.4f}[/]"
        )

    mo = data["Mo"]
    dist_to_next = 3.333333 - (mo["deg"] % 3.333333) if not mo['retro'] else (mo['deg'] % 3.333333)
    # Using actual velocity to calculate the next transit
    time_to_pada = (dist_to_next / mo['speed']) * 24 if mo['speed'] > 0 else 0

    notif = (
        f"[bold cyan]MOON ANALYSIS[/]\n"
        f"Group   : [{LORD_COLORS[mo['lord']]}] {mo['lord']} Stars [/]\n"
        f"Current : {mo['star']} P-{mo['pada']}\n"
        f"Next Transit in: [bold green]{time_to_pada:.2f} hours[/]\n"
        f"\n[dim white]ESC or 'q' to Quit[/]"
    )

    layout = Layout()
    layout.split_column(
        Layout(Panel(f"LOC: {city_name} | {engine.view_date.strftime('%d-%b-%Y %H:%M:%S')} | GMT {detected_offset:+}", style="white"), size=3),
        Layout(name="main")
    )
    layout["main"].split_row(
        Layout(Panel(table, title="Synchronized Lord Groups"), ratio=2),
        Layout(Panel(notif, title="Live Notifications"), ratio=1)
    )
    return layout

# ---------------- CONTROLS ----------------
def on_press(key):
    global running
    try:
        if key == keyboard.Key.right: engine.view_date += timedelta(hours=1)
        elif key == keyboard.Key.left: engine.view_date -= timedelta(hours=1)
        elif key == keyboard.Key.up: engine.view_date += timedelta(minutes=15)
        elif key == keyboard.Key.down: engine.view_date -= timedelta(minutes=15)
        elif key == keyboard.Key.page_up: engine.view_date += timedelta(days=1)
        elif key == keyboard.Key.page_down: engine.view_date -= timedelta(days=1)
        elif key == keyboard.Key.esc or (hasattr(key, 'char') and key.char == 'q'):
            running = False
            return False 
    except: pass

# ---------------- RUN ----------------
listener = keyboard.Listener(on_press=on_press)
listener.start()

console.clear()
sys.stdout.write("\033[?1049h")
sys.stdout.flush()

try:
    with Live(make_layout(), refresh_per_second=4, screen=True) as live:
        while running:
            live.update(make_layout())
            time.sleep(0.1)
finally:
    sys.stdout.write("\033[?1049l")
    sys.stdout.flush()
    listener.stop()