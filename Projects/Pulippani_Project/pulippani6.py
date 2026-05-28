import swisseph as swe
import os, sys, time, json
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
from rich.align import Align

# ---------------- CONFIGURATION ----------------
if sys.platform == "win32":
    os.system("color")

JSON_FILE = "pulippani_300.json"
swe.set_ephe_path("./ephe")

console = Console()
geolocator = Nominatim(user_agent="pulippani_engine_v3")
tf = TimezoneFinder()

# ---------------- INPUT ----------------
console.clear()
console.print("[bold yellow]=== PULIPPANI SIDDHAR 300: MASTER ENGINE ===[/bold yellow]\n")

name = input("Enter Name: ")
dob = input("Enter DOB (DD/MM/YYYY): ")
tob = input("Enter TOB (HH:MM:SS): ")
birth_city = input("Enter Birth City: ")

# ---------------- LOCATION + TZ ----------------
def get_auto_location(city, date_str, time_str):
    try:
        loc = geolocator.geocode(city, timeout=10)
        if loc:
            lat, lon = loc.latitude, loc.longitude
        else:
            console.print("[red]⚠ City not found. Using fallback coordinates.[/red]")
            lat, lon = 16.1176, 80.9314  # Andhra fallback
        tz_name = tf.timezone_at(lat=lat, lng=lon)
        if not tz_name:
            tz_name = "Asia/Kolkata"
        target_tz = pytz.timezone(tz_name)
        dt_obj = datetime.strptime(f"{date_str} {time_str}", "%d/%m/%Y %H:%M:%S")
        localized_dt = target_tz.localize(dt_obj)
        offset = localized_dt.utcoffset().total_seconds() / 3600
        return lat, lon, offset, tz_name
    except Exception as e:
        console.print(f"[red]⚠ Location error: {e}[/red]")
        return 16.1176, 80.9314, 5.5, "Asia/Kolkata"

b_lat, b_lon, tz_offset, detected_tz = get_auto_location(birth_city, dob, tob)
d, m, y = map(int, dob.split("/"))
hh, mm, ss = map(int, tob.split(":"))
birth_hour_utc = (hh + mm/60 + ss/3600) - tz_offset

# ---------------- ENGINE ----------------
class PulippaniEngine:
    def __init__(self):
        swe.set_sid_mode(swe.SIDM_LAHIRI)
        self.view_date = datetime.now()
        self.njd = swe.julday(y, m, d, birth_hour_utc)
        self.grandham = self.load_grandham()
        self.natal_planets = self.calc_planets(self.njd)
        self.lagna_lon = self.calc_lagna(self.njd, b_lat, b_lon)
        self.gulika_lon = self.calc_gulika(self.njd)

    def load_grandham(self):
        if os.path.exists(JSON_FILE):
            with open(JSON_FILE, 'r') as f:
                return json.load(f)
        return {"placements": {}, "combinations": [], "lagna_rules": {}}

    def calc_planets(self, jd):
        flags = swe.FLG_SWIEPH | swe.FLG_SPEED | swe.FLG_SIDEREAL
        planets = [(0,"Su"), (1,"Mo"), (2,"Me"), (3,"Ve"), (4,"Ma"), (5,"Ju"), (6,"Sa"), (11,"Ra")]
        data = {}
        for pid, name in planets:
            res = swe.calc_ut(jd, pid, flags)[0]
            data[name] = {"lon": res[0], "speed": res[3]}
            if name == "Ra":
                data["Ke"] = {"lon": (res[0] + 180) % 360, "speed": res[3]}
        return data

    def calc_lagna(self, jd, lat, lon):
        houses = swe.houses_ex(jd, lat, lon, b'W')
        return houses[0][0]

    def calc_gulika(self, jd):
        weekday = int((jd + 1.5) % 7)
        offsets = [26, 22, 18, 14, 10, 6, 2]
        return (self.natal_planets["Su"]["lon"] + offsets[weekday] * 15) % 360

    def get_house(self, lon):
        lagna_rasi = int(self.lagna_lon / 30)
        planet_rasi = int(lon / 30)
        return (planet_rasi - lagna_rasi + 12) % 12 + 1

    def get_analysis(self):
        natal_results = []
        transit_results = []
        h_occ = {i: set() for i in range(1, 13)}

        # --- NATAL LOGIC ---
        lagna_rasi = int(self.lagna_lon / 30)
        l_type = "Movable" if lagna_rasi in [0,3,6,9] else "Fixed" if lagna_rasi in [1,4,7,10] else "Dual"
        
        if l_type in self.grandham.get("lagna_rules", {}):
            sl, dsc = self.grandham["lagna_rules"][l_type]
            natal_results.append(f"[yellow][*] Sloka {sl} (Lagna):[/] {dsc}")

        pl_db = self.grandham.get("placements", {})
        for p, v in self.natal_planets.items():
            h = self.get_house(v['lon'])
            h_occ[h].add(p)
            if p in pl_db and str(h) in pl_db[p]:
                sl, dsc = pl_db[p][str(h)]
                natal_results.append(f"[*] Sloka {sl}: {dsc}")

        gu_h = self.get_house(self.gulika_lon)
        h_occ[gu_h].add("Gu")
        if "Gu" in pl_db and str(gu_h) in pl_db["Gu"]:
            sl, dsc = pl_db["Gu"][str(gu_h)]
            natal_results.append(f"[*] Sloka {sl}: {dsc}")

        for cb in self.grandham.get("combinations", []):
            target = set(cb["planets"])
            for h, present in h_occ.items():
                if target.issubset(present) and (cb["house"] == "any" or cb["house"] == h):
                    natal_results.append(f"[green][+] Sloka {cb['sloka']}:[/] {cb['title']}")

        # --- TRANSIT LOGIC (Gochara) ---
        tjd = swe.julday(self.view_date.year, self.view_date.month, self.view_date.day, 12.0)
        transit_planets = self.calc_planets(tjd)
        
        for p in ["Sa", "Ju", "Ra", "Ke", "Ma"]: # Major influencers
            lon = transit_planets[p]['lon']
            h = self.get_house(lon)
            transit_results.append(f"[red]→[/] {p} is currently in [bold]House {h}[/]")

        return natal_results, transit_results

# ---------------- UI ----------------
engine = PulippaniEngine()

def get_chart_table():
    tjd = swe.julday(engine.view_date.year, engine.view_date.month, engine.view_date.day, 12.0)
    transit = engine.calc_planets(tjd)
    grid = {i: {"n": [], "t": []} for i in range(1, 13)}
    for p,v in engine.natal_planets.items():
        grid[int(v["lon"]/30)+1]["n"].append(p)
    grid[int(engine.lagna_lon/30)+1]["n"].append("[bold yellow]Lagn[/]")
    grid[int(engine.gulika_lon/30)+1]["n"].append("[bold cyan]Gu[/]")
    for p,v in transit.items():
        grid[int(v["lon"]/30)+1]["t"].append(p)

    def cell(n):
        return f"[green]{' '.join(grid[n]['n'])}[/]\n[red]{' '.join(grid[n]['t'])}[/]"

    t = Table.grid(expand=True)
    for _ in range(4): t.add_column()
    t.add_row(Panel(cell(12)),Panel(cell(1)),Panel(cell(2)),Panel(cell(3)))
    t.add_row(Panel(cell(11)),Align.center("PULIPPANI"),Align.center("300 ENGINE"),Panel(cell(4)))
    t.add_row(Panel(cell(10)),"","",Panel(cell(5)))
    t.add_row(Panel(cell(9)),Panel(cell(8)),Panel(cell(7)),Panel(cell(6)))
    return t

def make_layout():
    n_res, t_res = engine.get_analysis()
    layout = Layout()
    layout.split_column(
        Layout(Panel(f"Pulippani Master | Transit: {engine.view_date:%d-%b-%Y} | Zone: {detected_tz}"), size=3),
        Layout(name="body")
    )
    layout["body"].split_row(
        Layout(Panel(get_chart_table(), title="Chart (Green=Natal, Red=Transit)"), ratio=2),
        Layout(name="side", ratio=1)
    )
    layout["side"].split_column(
        Layout(Panel("\n".join(n_res), title="[bold green]Natal Promises (Fixed)[/]")),
        Layout(Panel("\n".join(t_res), title="[bold red]Transit Gochara (Moving)[/]"))
    )
    return layout

def on_press(key):
    try:
        if key == keyboard.Key.right: engine.view_date += timedelta(days=1)
        elif key == keyboard.Key.left: engine.view_date -= timedelta(days=1)
    except: pass

keyboard.Listener(on_press=on_press).start()

sys.stdout.write("\033[?1049h")
sys.stdout.flush()

try:
    with Live(make_layout(), refresh_per_second=4, screen=True) as live:
        while True:
            live.update(make_layout())
            time.sleep(0.1)
except KeyboardInterrupt: pass
finally:
    sys.stdout.write("\033[?1049l")
    sys.stdout.flush()