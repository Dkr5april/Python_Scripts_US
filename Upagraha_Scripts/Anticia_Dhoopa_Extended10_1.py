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
geolocator = Nominatim(user_agent="astro_engine_v23")

ORB = 1.5

# ---------------- INPUT ----------------
console.clear()
console.print("[bold magenta]=== ASTRO ENGINE V23 (LIVE + PDF) ===[/bold magenta]\n")

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

# CHANGE 1: Added Scan Start Date Input
scan_start_str = input("\nEnter Scan Start Date (DD/MM/YYYY) [Leave blank for Today]: ")
if scan_start_str.strip() == "":
    scan_start_date = datetime.now()
else:
    scan_start_date = datetime.strptime(scan_start_str, "%d/%m/%Y")

scan_days = int(input("How many days to scan for PDF? "))

d, m, y = map(int, dob.split("/"))
hh, mm, ss = map(int, tob.split(":"))
birth_hour = hh + mm/60 + ss/3600

# ---------------- PLANETS ----------------
INDIAN_PLANETS = [
    (0,"Su"), (1,"Mo"), (2,"Me"), (3,"Ve"),
    (4,"Ma"), (5,"Ju"), (6,"Sa"), (11,"Ra")
]

WESTERN_PLANETS = [(7,"Ur"), (8,"Ne"), (9,"Pl")]

# ---------------- ENGINE ----------------
class AstroEngine:
    def __init__(self):
        swe.set_sid_mode(swe.SIDM_LAHIRI)
        self.mode = "SIDEREAL"
        self.view_date = datetime.now()
        self.njd = swe.julday(y, m, d, birth_hour)
        self.n_sid = self.calc_planets(self.njd, True)
        self.n_trop = self.calc_planets(self.njd, False)

        self.n_ant = {k:(v["lon"]+180)%360 for k,v in self.n_trop.items()}

        sun_lon = self.n_sid["Su"]["lon"]
        dh = (sun_lon + 133.3333) % 360
        vy = (360 - dh) % 360
        self.n_up = {
            "Dhuma": dh,
            "Vyatipata": vy,
            "Parivesha": (vy+180)%360
        }

    def calc_planets(self, jd, sidereal):
        flags = swe.FLG_SWIEPH | swe.FLG_SPEED
        if sidereal:
            flags |= swe.FLG_SIDEREAL

        plist = INDIAN_PLANETS.copy()
        if not sidereal:
            plist += WESTERN_PLANETS

        data = {}
        for pid, name in plist:
            res = swe.calc_ut(jd, pid, flags)[0]
            lon, vel = res[0], res[3]
            data[name] = {"lon": lon, "retro": vel < 0}
            if name == "Ra":
                data["Ke"] = {"lon": (lon+180)%360, "retro": True}
        return data

engine = AstroEngine()

# ---------------- PDF ----------------
class AstroPDF(FPDF):
    def header(self):
        self.set_font("Arial","B",14)
        self.cell(0,10,"Karmic Forecast Report",0,1,"C")
        self.ln(4)

def create_pdf(days):
    pdf = AstroPDF()
    pdf.add_page()
    pdf.set_font("Arial",size=10)
    pdf.cell(0,8,f"Name: {name} | DOB: {dob} {tob}",0,1)

    for i in range(days):
        # Using the new scan_start_date here
        day = scan_start_date + timedelta(days=i)
        tjd = swe.julday(day.year, day.month, day.day, 12.0)

        t_trop = engine.calc_planets(tjd, False)
        t_sid = engine.calc_planets(tjd, True)

        trop_hits, sid_hits = [], []

        for tp, t in t_trop.items():
            for np, nlon in engine.n_ant.items():
                if abs(t["lon"] - nlon) < ORB:
                    trop_hits.append(f"{tp} hits Ant.{np} (POSITIVE)")

        for tp, t in t_sid.items():
            for up, ulon in engine.n_up.items():
                if abs(t["lon"] - ulon) < ORB:
                    # CHANGE 2: Logic for Benefic vs Malefic hits
                    if tp in ["Ju", "Ve"]:
                        sid_hits.append(f"{tp} hits {up} (REDUCED POSITIVE)")
                    else:
                        sid_hits.append(f"{tp} hits {up} (NEGATIVE)")

        if trop_hits or sid_hits:
            pdf.ln(3)
            pdf.set_fill_color(230,230,230)
            pdf.cell(0,8,day.strftime("%d-%b-%Y"),1,1,"L",True)

            pdf.set_text_color(0,130,0)
            for h in trop_hits:
                pdf.cell(0,6,"TROPICAL: "+h,0,1)

            # Applying Yellow/Brown for Reduced Positive, Red for Negative
            for h in sid_hits:
                if "REDUCED POSITIVE" in h:
                    pdf.set_text_color(180,140,0) # Brownish Yellow
                else:
                    pdf.set_text_color(180,0,0)   # Red
                pdf.cell(0,6,"SIDEREAL: "+h,0,1)

            pdf.set_text_color(0,0,0)

    fname = f"Forecast_{name}_{datetime.now():%Y%m%d_%H%M%S}.pdf"
    pdf.output(fname)
    console.print(f"[bold green]PDF created: {fname}[/bold green]")

create_pdf(scan_days)

# ---------------- UI ----------------
def get_chart():
    tjd = swe.julday(engine.view_date.year, engine.view_date.month,
                     engine.view_date.day, 12.0)
    transit = engine.calc_planets(tjd, engine.mode=="SIDEREAL")
    natal = engine.n_sid if engine.mode=="SIDEREAL" else engine.n_trop

    grid = {i:{"n":[], "t":[]} for i in range(1,13)}

    for p,v in natal.items():
        grid[int(v["lon"]/30)+1]["n"].append(f"({p})" if v["retro"] else p)
    for p,v in transit.items():
        grid[int(v["lon"]/30)+1]["t"].append(f"({p})" if v["retro"] else p)

    def cell(n):
        return f"[green]{' '.join(grid[n]['n'])}[/]\n[red]{' '.join(grid[n]['t'])}[/]"

    t = Table.grid(expand=True)
    for _ in range(4): t.add_column()
    t.add_row(Panel(cell(12)),Panel(cell(1)),Panel(cell(2)),Panel(cell(3)))
    t.add_row(Panel(cell(11)),Align.center(engine.mode),Align.center(""),Panel(cell(4)))
    t.add_row(Panel(cell(10)),"","",Panel(cell(5)))
    t.add_row(Panel(cell(9)),Panel(cell(8)),Panel(cell(7)),Panel(cell(6)))
    return t

def get_impact_table():
    table = Table(expand=True)
    table.add_column("Transit",style="red")
    table.add_column("Hits",style="green")
    table.add_column("Δ°")
    table.add_column("Result")

    tjd = swe.julday(engine.view_date.year, engine.view_date.month,
                     engine.view_date.day, 12.0)
    tset = engine.calc_planets(tjd, engine.mode=="SIDEREAL")
    nset = engine.n_sid if engine.mode=="SIDEREAL" else engine.n_trop

    for tp,t in tset.items():
        for np,n in nset.items():
            d = abs(t["lon"]-n["lon"])
            if d < ORB:
                table.add_row(tp,np,f"{d:.2f}","PLANET")

    if engine.mode=="TROPICAL":
        for tp,t in tset.items():
            for ap,alon in engine.n_ant.items():
                d = abs(t["lon"]-alon)
                if d < ORB:
                    table.add_row(tp,f"Ant.{ap}",f"{d:.2f}","[green]POSITIVE[/]")

    if engine.mode=="SIDEREAL":
        for tp,t in tset.items():
            for up,ulon in engine.n_up.items():
                d = abs(t["lon"]-ulon)
                if d < ORB:
                    # Reflect the "Reduced Positive" logic in the Live UI as well
                    if tp in ["Ju", "Ve"]:
                        table.add_row(tp,up,f"{d:.2f}","[yellow]REDUCED POSITIVE[/]")
                    else:
                        table.add_row(tp,up,f"{d:.2f}","[red]NEGATIVE[/]")

    return table

def make_layout():
    layout = Layout()
    layout.split_column(
        Layout(Panel(f"{name} | {engine.view_date:%d-%b-%Y} | {engine.mode} | ← → | T Toggle"),size=3),
        Layout(name="body")
    )
    layout["body"].split_row(
        Layout(Panel(get_chart(),title="Chart"),ratio=2),
        Layout(Panel(get_impact_table(),title="Daily Impacts"),ratio=1)
    )
    return layout

# ---------------- CONTROLS ----------------
def on_press(key):
    try:
        if key == keyboard.Key.right:
            engine.view_date += timedelta(days=1)
        elif key == keyboard.Key.left:
            engine.view_date -= timedelta(days=1)
        elif hasattr(key,"char") and key.char.lower()=="t":
            engine.mode = "TROPICAL" if engine.mode=="SIDEREAL" else "SIDEREAL"
    except:
        pass

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