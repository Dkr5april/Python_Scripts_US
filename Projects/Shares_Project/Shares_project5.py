import swisseph as swe
import os, sys, time
from datetime import datetime, timedelta, timezone
from pynput import keyboard
from geopy.geocoders import Nominatim
from timezonefinder import TimezoneFinder
import pytz
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

# ---------------- CONFIG ----------------
swe.set_ephe_path("./ephe")
console = Console()
geolocator = Nominatim(user_agent="market_sidereal_auto")
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

# ---------------- ENGINE ----------------
class SiderealEngine:
    def __init__(self, dt, offset_hours):
        self.view_date = dt
        self.offset = offset_hours
        swe.set_sid_mode(swe.SIDM_LAHIRI)

    def get_data(self):
        # Automatically handles GMT conversion based on the detected offset
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

# ---------------- AUTOMATED LOCATION LOGIC ----------------
console.clear()
console.print("[bold cyan]=== AUTOMATED SIDEREAL ENGINE ===[/bold cyan]\n")

location_input = input("Enter Place and State (e.g., Scottsdale, AZ): ")

if not location_input:
    # Defaulting to your stored coordinates
    lat, lon = 16.1176, 80.9314
    city_name = "Default (Scottsdale/Custom)"
else:
    loc = geolocator.geocode(location_input)
    if loc:
        lat, lon = loc.latitude, loc.longitude
        city_name = loc.address.split(',')[0]
    else:
        console.print("[red]Location not found. Using defaults.[/]")
        lat, lon = 16.1176, 80.9314
        city_name = "Default"

# Get Timezone and GMT Offset automatically
tz_name = tf.timezone_at(lng=lon, lat=lat)
timezone_obj = pytz.timezone(tz_name)
# Calculate offset for the current date (handles Daylight Savings automatically)
offset_seconds = timezone_obj.utcoffset(datetime.now()).total_seconds()
detected_offset = offset_seconds / 3600

d_str = input("Date (DD/MM/YYYY) [Today]: ") or datetime.now().strftime("%d/%m/%Y")
t_str = input("Time (HH:MM:SS) [Now]: ") or datetime.now().strftime("%H:%M:%S")
current_dt = datetime.strptime(f"{d_str} {t_str}", "%d/%m/%Y %H:%M:%S")

engine = SiderealEngine(current_dt, detected_offset)

# ---------------- RENDER ----------------
def refresh_ui():
    os.system('cls' if os.name == 'nt' else 'clear')
    data = engine.get_data()
    
    table = Table(expand=True, border_style="cyan")
    table.add_column("Planet", style="bold cyan")
    table.add_column("Rasi", justify="center")
    table.add_column("Degrees", style="green")
    table.add_column("Motion")
    
    for p, v in data["planets"].items():
        table.add_row(p, RASI_NAMES[int(v['lon']/30)], f"{v['lon']%30:05.2f}°", "Retro" if v['retro'] else "Direct")

    m_info = (
        f"[yellow]STAR:[/][bold green] {data['moon_star']}[/]\n"
        f"[yellow]POS :[/] {data['moon_rasi']} {data['moon_deg']:.4f}°\n"
        f"[yellow]MATES:[/][cyan] {', '.join(data['moon_mates']) if data['moon_mates'] else 'None'}[/]"
    )

    header = Panel(f"LOCATION: [bold green]{city_name}[/] | [bold yellow]{engine.view_date.strftime('%H:%M:%S')}[/] | GMT: {detected_offset:+}")
    
    body = Table.grid(expand=True)
    body.add_column(ratio=2); body.add_column(ratio=1)
    body.add_row(Panel(table, title="Zodiac (Lahiri)"), Panel(m_info, title="Market Logic"))
    
    console.print(header)
    console.print(body)
    console.print("[dim]Arrows: Time | PgUp/Dn: Day | Esc: Exit[/]")

# ---------------- CONTROLS ----------------
def on_press(key):
    try:
        updated = False
        if key == keyboard.Key.right: 
            engine.view_date += timedelta(hours=1); updated = True
        elif key == keyboard.Key.left: 
            engine.view_date -= timedelta(hours=1); updated = True
        elif key == keyboard.Key.up: 
            engine.view_date += timedelta(minutes=5); updated = True
        elif key == keyboard.Key.down: 
            engine.view_date -= timedelta(minutes=5); updated = True
        elif key == keyboard.Key.page_up: 
            engine.view_date += timedelta(days=1); updated = True
        elif key == keyboard.Key.page_down: 
            engine.view_date -= timedelta(days=1); updated = True
        elif key == keyboard.Key.esc: return False 

        if updated: refresh_ui()
    except: pass

refresh_ui()
with keyboard.Listener(on_press=on_press) as listener:
    listener.join()