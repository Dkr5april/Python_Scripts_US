import swisseph as swe
import os, sys, time
import geocoder
from datetime import datetime, timedelta
from pynput import keyboard
from geopy.geocoders import Nominatim
from rich.live import Live
from rich.table import Table
from rich.console import Console
from rich.layout import Layout
from rich.panel import Panel
from rich.align import Align
from rich.progress import Progress
from fpdf import FPDF

# ---------------- STABILITY & PATHS ----------------
if sys.platform == "win32":
    os.system("color")

swe.set_ephe_path("./ephe")
console = Console()
geolocator = Nominatim(user_agent="astro_engine_v24")
ORB_LON = 1.5 
ORB_DEC = 1.0  

# ---------------- INPUT ----------------
console.clear()
console.print("[bold magenta]=== ASTRO ENGINE V25 (OOB + DECLINATION) ===[/bold magenta]\n")

name = input("Enter Name: ")
dob = input("Enter DOB (DD/MM/YYYY): ")
tob = input("Enter TOB (HH:MM:SS): ")
birth_city = input("Enter Birth City: ")

def fetch_coords(city):
    try:
        loc = geolocator.geocode(city, timeout=5)
        if loc: return loc.latitude, loc.longitude
    except: pass
    return None, None

b_lat, b_lon = fetch_coords(birth_city)
g = geocoder.ip("me")
t_lat, t_lon = (g.latlng if g.latlng else (0.0, 0.0))

scan_days = int(input("\nHow many days to scan for PDF? "))

d, m, y = map(int, dob.split("/"))
hh, mm, ss = map(int, tob.split(":"))
birth_hour = hh + mm/60 + ss/3600

INDIAN_PLANETS = [(0,"Su"), (1,"Mo"), (2,"Me"), (3,"Ve"), (4,"Ma"), (5,"Ju"), (6,"Sa"), (11,"Ra")]
WESTERN_PLANETS = [(7,"Ur"), (8,"Ne"), (9,"Pl")]

# ---------------- ENGINE ----------------
class AstroEngine:
    def __init__(self):
        self.ayan_val = swe.get_ayanamsa(swe.julday(y, m, d, birth_hour))
        swe.set_sid_mode(swe.SIDM_LAHIRI)
        self.mode = "SIDEREAL"
        self.view_date = datetime.now()
        self.njd = swe.julday(y, m, d, birth_hour)
        
        self.n_sid = self.calc_planets(self.njd, True)
        self.n_trop = self.calc_planets(self.njd, False)
        
        # Add Angles to Tropical
        _, ascmc = swe.houses_ex(self.njd, b_lat, b_lon, b'P')
        res_asc, _ = swe.calc_ut(self.njd, swe.ASC, swe.FLG_SWIEPH)
        res_mc, _ = swe.calc_ut(self.njd, swe.MC, swe.FLG_SWIEPH)
        self.n_trop["Asc"] = {"lon": ascmc[0], "dec": res_asc[1], "retro": False}
        self.n_trop["MC"] = {"lon": ascmc[1], "dec": res_mc[1], "retro": False}
        
        self.n_ant = {k: (180 - v["lon"]) % 360 for k,v in self.n_trop.items()}
        sun_lon = self.n_sid["Su"]["lon"]
        self.n_aprakasha = {"Dhuma": (sun_lon + 133.333)%360, "Vyatipata": (360-(sun_lon + 133.333))%360}
        
        # Upagrahas
        self.n_up = {}
        try:
            mjd = swe.julday(y, m, d, 0.0)
            rise = swe.rise_trans(mjd, swe.SUN, b_lon, b_lat, 0, 1)[1][0]
            sset = swe.rise_trans(mjd, swe.SUN, b_lon, b_lat, 0, 2)[1][0]
            is_day = (self.njd >= rise and self.njd <= sset)
            start_l = int(swe.day_of_week(self.njd) if is_day else (swe.day_of_week(self.njd) + 4) % 7)
            part = ((sset - rise) if is_day else (1.0 - (sset - rise))) / 8.0
            up_map = {0:"Kala", 4:"Mrityu", 6:"Gulika"}
            for i in range(7):
                lord = (start_l + i) % 7
                if lord in up_map:
                    seg = (rise if is_day else sset) + (i * part)
                    _, ascmc_up = swe.houses_ex(seg, b_lat, b_lon, b'P')
                    self.n_up[up_map[lord]] = ascmc_up[0]
        except: pass

    def calc_planets(self, jd, sidereal):
        flags = swe.FLG_SWIEPH | swe.FLG_SPEED
        if sidereal: flags |= swe.FLG_SIDEREAL
        data = {}
        plist = INDIAN_PLANETS.copy() if sidereal else INDIAN_PLANETS + WESTERN_PLANETS
        for pid, pnm in plist:
            res, _ = swe.calc_ut(jd, pid, flags)
            data[pnm] = {"lon": res[0], "dec": res[1], "retro": res[3] < 0}
        return data

engine = AstroEngine()

# ---------------- UI HELPERS ----------------
def get_dec_str(dec):
    side = "N" if dec >= 0 else "S"
    oob = "⭐" if abs(dec) > 23.44 else ""
    return f"{abs(dec):.1f}{side}{oob}"

def get_impact_table():
    table = Table(expand=True, box=None)
    table.add_column("Tr", style="red", width=5)
    table.add_column("Dec", style="yellow", width=7)
    table.add_column("Natal", style="green")
    table.add_column("Type", style="cyan")
    
    tjd = swe.julday(engine.view_date.year, engine.view_date.month, engine.view_date.day, 12.0)
    t_trop = engine.calc_planets(tjd, False)

    if engine.mode == "TROPICAL":
        for tp, t in t_trop.items():
            dec_label = get_dec_str(t['dec'])
            for np, n in engine.n_trop.items():
                if abs(t["lon"] - n["lon"]) < ORB_LON: table.add_row(tp, dec_label, np, "Conj")
                if abs(t["dec"] - n["dec"]) < ORB_DEC: table.add_row(tp, dec_label, np, "Para")
                if abs(t["dec"] + n["dec"]) < ORB_DEC: table.add_row(tp, dec_label, np, "C-Para")
            for np, alon in engine.n_ant.items():
                if abs(t["lon"] - alon) < ORB_LON: table.add_row(tp, dec_label, f"Ant.{np}", "Mirror")
    else:
        t_sid = engine.calc_planets(tjd, True)
        all_sid = {**{k: v["lon"] for k, v in engine.n_sid.items()}, **engine.n_up, **engine.n_aprakasha}
        for tp, t in t_sid.items():
            for name, lon in all_sid.items():
                if abs(t["lon"] - lon) < ORB_LON: table.add_row(tp, "", name, "Hit")
    return table

def get_chart():
    tjd = swe.julday(engine.view_date.year, engine.view_date.month, engine.view_date.day, 12.0)
    transit = engine.calc_planets(tjd, engine.mode=="SIDEREAL")
    natal = engine.n_sid if engine.mode=="SIDEREAL" else engine.n_trop
    grid = {i:{"n":[], "t":[]} for i in range(1,13)}
    for p,v in natal.items(): grid[int(v["lon"]/30)+1]["n"].append(p)
    for p,v in transit.items(): grid[int(v["lon"]/30)+1]["t"].append(p)
    
    t = Table.grid(expand=True)
    for _ in range(4): t.add_column()
    def cell(n): return Panel(f"[green]{' '.join(grid[n]['n'])}[/]\n[red]{' '.join(grid[n]['t'])}[/]", padding=(0,1))
    t.add_row(cell(12), cell(1), cell(2), cell(3))
    t.add_row(cell(11), Align.center(f"[bold]{engine.mode}[/]"), Align.center(f"{engine.view_date:%d-%b}"), cell(4))
    t.add_row(cell(10), "", "", cell(5))
    t.add_row(cell(9), cell(8), cell(7), cell(6))
    return t

def make_layout():
    layout = Layout()
    layout.split_column(
        Layout(Panel(f"TARGET: {name} | [T] Mode | [J] Jump | [Arrows] Navigate", style="white on blue"), size=3),
        Layout(name="body")
    )
    layout["body"].split_row(
        Layout(Panel(get_chart(), title="Rasi/Wheel"), ratio=2),
        Layout(Panel(get_impact_table(), title="Impact (Dec + Lon)"), ratio=1)
    )
    return layout

# ---------------- CONTROLS & MAIN ----------------
engine.request_jump = False
exit_flag = False

def on_press(key):
    global exit_flag
    try:
        if key == keyboard.Key.right: engine.view_date += timedelta(days=1)
        elif key == keyboard.Key.left: engine.view_date -= timedelta(days=1)
        elif hasattr(key, 'char'):
            if key.char == 't': engine.mode = "TROPICAL" if engine.mode == "SIDEREAL" else "SIDEREAL"
            if key.char == 'j': engine.request_jump = True
            if key.char == 'q': exit_flag = True
    except: pass

listener = keyboard.Listener(on_press=on_press)
listener.start()

sys.stdout.write("\033[?1049h")
try:
    with Live(make_layout(), refresh_per_second=4, screen=True) as live:
        while not exit_flag:
            if engine.request_jump:
                live.stop()
                target = console.input("\nJump Date (DD/MM/YYYY): ")
                try: engine.view_date = datetime.strptime(target, "%d/%m/%Y")
                except: pass
                engine.request_jump = False
                live.start()
            live.update(make_layout())
            time.sleep(0.1)
except KeyboardInterrupt: pass
finally:
    sys.stdout.write("\033[?1049l")
    listener.stop()