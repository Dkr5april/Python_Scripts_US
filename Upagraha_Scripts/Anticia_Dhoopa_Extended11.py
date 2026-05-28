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
from fpdf import FPDF

# ---------------- STABILITY ----------------
if sys.platform == "win32":
    os.system("color")

swe.set_ephe_path("./ephe")
console = Console()
geolocator = Nominatim(user_agent="astro_engine_v24")

ORB = 1.5

# ---------------- INPUT ----------------
console.clear()
console.print("[bold magenta]=== ASTRO ENGINE V24 (SYMMETRY + SHADOWS) ===[/bold magenta]\n")

name = input("Enter Name: ")
dob = input("Enter DOB (DD/MM/YYYY): ")
tob = input("Enter TOB (HH:MM:SS): ")
birth_city = input("Enter Birth City: ")

def fetch_coords(city):
    try:
        loc = geolocator.geocode(city, timeout=5)
        if loc:
            return loc.latitude, loc.longitude
    except:
        pass
    return None, None

b_lat, b_lon = fetch_coords(birth_city)

console.print("\n[cyan]Transit Location Setup[/]")
t_choice = input("1: Auto | 2: City | 3: Manual | Choice: ")

if t_choice == "1":
    g = geocoder.ip("me")
    t_lat, t_lon = g.latlng
elif t_choice == "2":
    t_city = input("Enter Transit City: ")
    t_lat, t_lon = fetch_coords(t_city)
else:
    t_lat = float(input("Lat: "))
    t_lon = float(input("Lon: "))

scan_days = int(input("\nHow many days to scan for PDF? "))

d, m, y = map(int, dob.split("/"))
hh, mm, ss = map(int, tob.split(":"))
birth_hour = hh + mm/60 + ss/3600

# ---------------- PLANET LISTS ----------------
INDIAN_PLANETS = [(0,"Su"), (1,"Mo"), (2,"Me"), (3,"Ve"), (4,"Ma"), (5,"Ju"), (6,"Sa"), (11,"Ra")]
WESTERN_PLANETS = [(7,"Ur"), (8,"Ne"), (9,"Pl")]

# ---------------- ENGINE ----------------
class AstroEngine:
    def __init__(self):
        swe.set_sid_mode(swe.SIDM_LAHIRI)
        self.mode = "SIDEREAL"
        self.view_date = datetime.now()
        self.njd = swe.julday(y, m, d, birth_hour)
        
        # 1. POSITIONS
        self.n_sid = self.calc_planets(self.njd, True)
        self.n_trop = self.calc_planets(self.njd, False)

        # 2. WESTERN SYMMETRY (Tropical Points)
        self.n_ant = {k: (180 - v["lon"]) % 360 for k,v in self.n_trop.items()}
        self.n_cant = {k: (360 - v["lon"]) % 360 for k,v in self.n_trop.items()}
        
        self.n_decs = {}
        for pid, pnm in INDIAN_PLANETS + WESTERN_PLANETS:
            res = swe.calc_ut(self.njd, pid, swe.FLG_SWIEPH | swe.FLG_EQUATORIAL)[0]
            self.n_decs[pnm] = res[3]

        self.n_midpoints = {}
        plist = list(self.n_trop.keys())
        for i in range(len(plist)):
            for j in range(i+1, len(plist)):
                l1, l2 = self.n_trop[plist[i]]["lon"], self.n_trop[plist[j]]["lon"]
                diff = l1 - l2
                mid = ((l1 + l2 + 360) / 2) % 360 if abs(diff) > 180 else (l1 + l2) / 2
                self.n_midpoints[f"{plist[i]}/{plist[j]}"] = mid

        # 3. VEDIC SHADOWS (Sidereal Points)
        sun_lon = self.n_sid["Su"]["lon"]
        dh = (sun_lon + 133.3333) % 360
        vy = (360 - dh) % 360
        pa = (vy+180)%360
        in_ = (360-pa)%360
        self.n_aprakasha = {
            "Dhuma": dh, "Vyatipata": vy, "Parivesha": pa, 
            "Indrachapa": in_, "Upaketu": (in_+16.666)%360
        }
        
        try:
            # We use 0.0 to represent midnight at the start of the birth day
            midnight_jd = swe.julday(y, m, d, 0.0)
            
            # Use 1 for Rising and 2 for Setting flags to avoid BIT_RISE error
            res_rise = swe.rise_trans(midnight_jd, swe.SUN, b_lon, b_lat, 0, 1)[1][0]
            res_set = swe.rise_trans(midnight_jd, swe.SUN, b_lon, b_lat, 0, 2)[1][0]
            
            # Determine if born during day or night
            is_day = (self.njd >= res_rise and self.njd <= res_set)
            
            # Calculation of the 8-part division (Yama)
            duration = (res_set - res_rise) if is_day else (1.0 - (res_set - res_rise))
            start_time = res_rise if is_day else res_set
            part = duration / 8.0
            
            # Determine starting planet for the segments
            weekday = swe.day_of_week(self.njd)
            order_start = weekday if is_day else (weekday + 4) % 7
            
            up_map = {0:"Kala", 4:"Mrityu", 2:"Ardhaprahar", 5:"Yamaghantaka", 6:"Gulika"}
            self.n_up = {}
            
            for i in range(7):
                lord = (order_start + i) % 7
                if lord in up_map:
                    seg_time = start_time + (i * part)
                    _, ascmc = swe.houses_ex(seg_time, b_lat, b_lon, b'P')
                    self.n_up[up_map[lord]] = ascmc[0]
                    
        except Exception as e:
            self.n_up = {}

        # --- DAGHA RASIS ---
        tithi = int(((self.n_sid["Mo"]["lon"] - sun_lon) % 360) / 12) + 1
        d_map = {1:[8,11], 2:[1,12], 3:[5,10], 4:[2,7], 5:[3,6], 6:[4,9], 7:[4,9], 8:[3,6], 9:[5,10], 10:[1,12], 11:[8,11], 12:[2,7], 13:[2,5,8,11], 14:[3,6,9,12]}
        self.dagha_rasis = d_map.get(tithi, [])
        # --- END REPLACEMENT HERE ---

    def calc_planets(self, jd, sidereal):
        flags = swe.FLG_SWIEPH | swe.FLG_SPEED
        if sidereal: flags |= swe.FLG_SIDEREAL
        plist = INDIAN_PLANETS.copy() if sidereal else INDIAN_PLANETS + WESTERN_PLANETS
        data = {}
        for pid, pnm in plist:
            res = swe.calc_ut(jd, pid, flags)[0]
            data[pnm] = {"lon": res[0], "retro": res[3] < 0}
            if pnm == "Ra": data["Ke"] = {"lon": (res[0]+180)%360, "retro": True}
        return data

engine = AstroEngine()

# ---------------- PDF ----------------
class AstroPDF(FPDF):
    def header(self):
        self.set_font("Arial","B",14)
        self.cell(0,10,"Advanced Karmic Forecast",0,1,"C")
        self.ln(4)

def create_pdf(days):
    pdf = AstroPDF()
    pdf.add_page()
    pdf.set_font("Arial",size=10)
    pdf.cell(0,8,f"Name: {name} | Location: {birth_city}",0,1)

    for i in range(days):
        day = datetime.now() + timedelta(days=i)
        tjd = swe.julday(day.year, day.month, day.day, 12.0)
        
        t_trop = engine.calc_planets(tjd, False)
        t_sid = engine.calc_planets(tjd, True)
        hits = []

        if engine.mode == "TROPICAL":
            for tp, t in t_trop.items():
                for np, alon in engine.n_ant.items():
                    if abs(t["lon"]-alon) < ORB: hits.append(f"{tp} hits Antiscion of {np}")
                for mp, mlon in engine.n_midpoints.items():
                    if abs(t["lon"]-mlon) < ORB: hits.append(f"{tp} triggers Midpoint {mp}")
        else:
            for tp, t in t_sid.items():
                for un, ul in engine.n_up.items():
                    if abs(t["lon"]-ul) < ORB: hits.append(f"{tp} hits Upagraha {un}")

        if hits:
            pdf.ln(2)
            pdf.set_fill_color(240,240,240)
            pdf.cell(0,6,day.strftime("%d-%b-%Y") + f" ({engine.mode})",1,1,"L",True)
            for h in hits:
                pdf.cell(0,5, "- " + h,0,1)

    fname = f"Forecast_{name}_{datetime.now():%Y%m%d}.pdf"
    pdf.output(fname)
    console.print(f"[bold green]Report Generated: {fname}[/bold green]")

create_pdf(scan_days)

# ---------------- UI HELPERS ----------------
def get_chart():
    tjd = swe.julday(engine.view_date.year, engine.view_date.month, engine.view_date.day, 12.0)
    transit = engine.calc_planets(tjd, engine.mode=="SIDEREAL")
    natal = engine.n_sid if engine.mode=="SIDEREAL" else engine.n_trop
    grid = {i:{"n":[], "t":[]} for i in range(1,13)}
    for p,v in natal.items(): grid[int(v["lon"]/30)+1]["n"].append(f"({p})" if v["retro"] else p)
    for p,v in transit.items(): grid[int(v["lon"]/30)+1]["t"].append(f"({p})" if v["retro"] else p)
    
    def cell(n): return f"[green]{' '.join(grid[n]['n'])}[/]\n[red]{' '.join(grid[n]['t'])}[/]"
    t = Table.grid(expand=True)
    for _ in range(4): t.add_column()
    t.add_row(Panel(cell(12)),Panel(cell(1)),Panel(cell(2)),Panel(cell(3)))
    t.add_row(Panel(cell(11)),Align.center(engine.mode),Align.center(""),Panel(cell(4)))
    t.add_row(Panel(cell(10)),"","",Panel(cell(5)))
    t.add_row(Panel(cell(9)),Panel(cell(8)),Panel(cell(7)),Panel(cell(6)))
    return t

def get_impact_table():
    table = Table(expand=True)
    table.add_column("Transit", style="red")
    table.add_column("Hits Natal", style="green")
    table.add_column("Logic", style="cyan")
    table.add_column("Nature")
    tjd = swe.julday(engine.view_date.year, engine.view_date.month, engine.view_date.day, 12.0)
    
    if engine.mode == "TROPICAL":
        tset = engine.calc_planets(tjd, False)
        for tp, t in tset.items():
            for np, alon in engine.n_ant.items():
                if abs(t["lon"]-alon) < ORB: table.add_row(tp, f"Ant.{np}", "Mirror", "Support")
            for mp, mlon in engine.n_midpoints.items():
                if abs(t["lon"]-mlon) < ORB: table.add_row(tp, mp, "Midpoint", "Focus")
            if any(abs(t["lon"] - ap) < ORB for ap in [0, 90, 180, 270]):
                table.add_row(tp, "Aries Pt", "World", "Public")
    else:
        tset = engine.calc_planets(tjd, True)
        for tp, t in tset.items():
            for un, ul in engine.n_aprakasha.items():
                if abs(t["lon"]-ul) < ORB: table.add_row(tp, un, "Shadow", "Karmic")
            for un, ul in engine.n_up.items():
                if abs(t["lon"]-ul) < ORB: table.add_row(tp, un, "Upagraha", "Critical")
            if (int(t["lon"]/30)+1) in engine.dagha_rasis:
                table.add_row(tp, f"Sign {int(t['lon']/30)+1}", "Dagha", "Burnt")
    return table

def make_layout():
    layout = Layout()
    layout.split_column(
        Layout(Panel(f"{name} | {engine.view_date:%d-%b-%Y} | Mode: {engine.mode} | [T] Toggle Mode | [<- ->] Change Date"),size=3),
        Layout(name="body")
    )
    layout["body"].split_row(
        Layout(Panel(get_chart(),title="Rasi Chart"),ratio=2),
        Layout(Panel(get_impact_table(),title="Sensitive Hits"),ratio=1)
    )
    return layout

# ---------------- CONTROLS ----------------
def on_press(key):
    try:
        if key == keyboard.Key.right: engine.view_date += timedelta(days=1)
        elif key == keyboard.Key.left: engine.view_date -= timedelta(days=1)
        elif hasattr(key,"char") and key.char.lower()=="t":
            engine.mode = "TROPICAL" if engine.mode=="SIDEREAL" else "SIDEREAL"
    except: pass

keyboard.Listener(on_press=on_press).start()

# ---------------- RUN ----------------
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