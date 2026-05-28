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

# ---------------- STABILITY & CONFIG ----------------
if sys.platform == "win32":
    os.system("color")

swe.set_ephe_path("./ephe")
console = Console()
geolocator = Nominatim(user_agent="market_sidereal_v8")
tf = TimezoneFinder()

NAKSHATRAS = [
    "Ashwini", "Bharani", "Krittika", "Rohini", "Mrigashira", "Ardra", 
    "Punarvasu", "Pushya", "Ashlesha", "Magha", "Purva Phalguni", "Uttara Phalguni", 
    "Hasta", "Chitra", "Swati", "Vishakha", "Anuradha", "Jyeshtha", 
    "Mula", "Purva Ashadha", "Uttara Ashadha", "Shravana", "Dhanishta", 
    "Shatabhisha", "Purva Bhadrapada", "Uttara Bhadrapada", "Revati"
]

RASI_NAMES = ["Ari", "Tau", "Gem", "Can", "Leo", "Vir", "Lib", "Sco", "Sag", "Cap", "Aqu", "Pis"]
ALL_PLANETS = [(0,"Su"), (1,"Mo"), (2,"Me"), (3,"Ve"), (4,"Ma"), (5,"Ju"), (6,"Sa"), (11,"Ra"), (7,"Ur"), (8,"Ne"), (9,"Pl")]

# ---------------- INPUT PHASE ----------------
console.clear()
console.print("[bold cyan]=== SIDEREAL MARKET TRACKER ===[/bold cyan]\n")

location_input = input("Enter Place and State (e.g., Scottsdale, AZ) [Enter for default]: ")

if not location_input:
    # Using your saved default coordinates
    lat, lon = 16.1176, 80.9314
    city_name = "Scottsdale (Default)"
else:
    loc = geolocator.geocode(location_input)
    if loc:
        lat, lon = loc.latitude, loc.longitude
        city_name = loc.address.split(',')[0]
    else:
        lat, lon = 16.1176, 80.9314
        city_name = "Default (Not Found)"

# Auto-GMT Logic
tz_name = tf.timezone_at(lng=lon, lat=lat)
timezone_obj = pytz.timezone(tz_name)
offset_seconds = timezone_obj.utcoffset(datetime.now()).total_seconds()
detected_offset = offset_seconds / 3600

d_str = input("Date (DD/MM/YYYY) [Today]: ") or datetime.now().strftime("%d/%m/%Y")
t_str = input("Time (HH:MM:SS) [09:15:00]: ") or "09:15:00"
current_dt = datetime.strptime(f"{d_str} {t_str}", "%d/%m/%Y %H:%M:%S")

# ---------------- ENGINE ----------------
class SiderealEngine:
    def __init__(self, dt, offset_hours):
        self.view_date = dt
        self.offset = offset_hours
        swe.set_sid_mode(swe.SIDM_LAHIRI)

    def get_data(self):
        gmt_dt = self.view_date - timedelta(hours=self.offset)
        jd = swe.julday(gmt_dt.year, gmt_dt.month, 
                        gmt_dt.day, gmt_dt.hour + gmt_dt.minute/60 + gmt_dt.second/3600)
        
        flags = swe.FLG_SWIEPH | swe.FLG_SPEED | swe.FLG_SIDEREAL
        data = {}
        for pid, name in ALL_PLANETS:
            res, _ = swe.calc_ut(jd, pid, flags)
            lon, vel = res[0], res[3]
            data[name] = {"lon": lon, "retro": vel < 0}
            if name == "Ra":
                data["Ke"] = {"lon": (lon + 180) % 360, "retro": True}
        
        m_lon = data["Mo"]["lon"]
        star_idx = int(m_lon / (13 + 1/3))
        mates = [p for p, v in data.items() if p != "Mo" and int(v["lon"]/(13+1/3)) == star_idx]
                
        return {
            "planets": data,
            "moon_star": NAKSHATRAS[star_idx],
            "moon_mates": mates,
            "moon_deg": m_lon % 30,
            "moon_rasi": RASI_NAMES[int(m_lon / 30)]
        }

engine = SiderealEngine(current_dt, detected_offset)

# ---------------- UI BUILDER (Matches Reference Logic) ----------------
def make_layout():
    data = engine.get_data()
    
    # Left Table: Planets
    table = Table(expand=True, border_style="cyan")
    table.add_column("Planet", style="bold cyan")
    table.add_column("Rasi", justify="center")
    table.add_column("Degrees", style="green")
    table.add_column("Motion")
    
    for p, v in data["planets"].items():
        table.add_row(p, RASI_NAMES[int(v['lon']/30)], f"{v['lon']%30:05.2f}°", "Retro" if v['retro'] else "Direct")

    # Right Panel: Moon Data
    m_info = (
        f"\n[yellow]NAKSHATRA :[/][bold green] {data['moon_star']}[/]\n"
        f"[yellow]RASI      :[/][bold white] {data['moon_rasi']} {data['moon_deg']:.4f}°[/]\n"
        f"[yellow]CONJUNCT  :[/][cyan] {', '.join(data['moon_mates']) if data['moon_mates'] else 'None'}[/]"
    )

    # Header with Date and Location
    date_header = engine.view_date.strftime('%d-%b-%Y | %H:%M:%S')
    
    layout = Layout()
    layout.split_column(
        Layout(Panel(f"LOCATION: [bold green]{city_name}[/]  |  [bold yellow]{date_header}[/]  |  GMT {detected_offset:+}", style="white"), size=3),
        Layout(name="main")
    )
    layout["main"].split_row(
        Layout(Panel(table, title="Zodiac (Lahiri)"), ratio=2),
        Layout(Panel(m_info, title="Moon Analysis"), ratio=1)
    )
    return layout

# ---------------- CONTROLS (Matches Reference Logic) ----------------
def on_press(key):
    try:
        if key == keyboard.Key.right: engine.view_date += timedelta(hours=1)
        elif key == keyboard.Key.left: engine.view_date -= timedelta(hours=1)
        elif key == keyboard.Key.up: engine.view_date += timedelta(minutes=5)
        elif key == keyboard.Key.down: engine.view_date -= timedelta(minutes=5)
        elif key == keyboard.Key.page_up: engine.view_date += timedelta(days=1)
        elif key == keyboard.Key.page_down: engine.view_date -= timedelta(days=1)
        elif key == keyboard.Key.esc: return False
    except: pass

# Start listener in background
keyboard.Listener(on_press=on_press).start()

# ---------------- RUN PHASE (The Reference Script Implementation) ----------------
# Step 1: Wipe the initial input text
console.clear() 

# Step 2: Use the Alternate Screen Buffer (\033[?1049h)
sys.stdout.write("\033[?1049h")
sys.stdout.flush()

try:
    # Step 3: Run the Live loop
    with Live(make_layout(), refresh_per_second=4, screen=True) as live:
        while True:
            live.update(make_layout())
            time.sleep(0.1)
except KeyboardInterrupt:
    pass
finally:
    # Step 4: Clean exit from Alternate Screen Buffer
    sys.stdout.write("\033[?1049l")
    sys.stdout.flush()