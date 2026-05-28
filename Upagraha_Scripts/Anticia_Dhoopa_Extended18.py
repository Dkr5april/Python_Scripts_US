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
        if loc: return loc.latitude, loc.longitude
    except: pass
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

INDIAN_PLANETS = [(0,"Su"), (1,"Mo"), (2,"Me"), (3,"Ve"), (4,"Ma"), (5,"Ju"), (6,"Sa"), (11,"Ra")]
WESTERN_PLANETS = [(7,"Ur"), (8,"Ne"), (9,"Pl")]

# ---------------- HELPERS ----------------
def fmt_deg(v):
    lon = v["lon"]
    deg = int(lon % 30)
    minutes = int((lon % 1) * 60)
    r_mark = " (R)" if v.get("retro") else ""
    return f"{deg:02d}°{minutes:02d}'{r_mark}"

class AstroPDF(FPDF):
    def header(self):
        self.set_font("Arial","B",14)
        self.cell(0,10,f"Comprehensive Forecast for {name}",0,1,"C")
        self.ln(5)

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
        self.n_ant = {k: (180 - v["lon"]) % 360 for k,v in self.n_trop.items()}
        self.n_cant = {k: (360 - v["lon"]) % 360 for k,v in self.n_trop.items()}
        
        sun_lon = self.n_sid["Su"]["lon"]
        dh = (sun_lon + 133.3333) % 360
        vy = (360 - dh) % 360
        pa = (vy+180)%360
        in_ = (360-pa)%360
        self.n_aprakasha = {"Dhuma": dh, "Vyatipata": vy, "Parivesha": pa, "Indrachapa": in_, "Upaketu": (in_+16.666)%360}
        
        try:
            mjd = swe.julday(y, m, d, 0.0)
            rise = swe.rise_trans(mjd, swe.SUN, b_lon, b_lat, 0, 1)[1][0]
            sset = swe.rise_trans(mjd, swe.SUN, b_lon, b_lat, 0, 2)[1][0]
            is_day = (self.njd >= rise and self.njd <= sset)
            dur = (sset - rise) if is_day else (1.0 - (sset - rise))
            part = dur / 8.0
            start_l = int(swe.day_of_week(self.njd) if is_day else (swe.day_of_week(self.njd) + 4) % 7)
            up_map = {0:"Kala", 4:"Mrityu", 2:"Ardhaprahar", 5:"Yamaghantaka", 6:"Gulika"}
            self.n_up = {}
            for i in range(7):
                lord = (start_l + i) % 7
                if lord in up_map:
                    seg = (rise if is_day else sset) + (i * part)
                    _, ascmc = swe.houses_ex(seg, b_lat, b_lon, b'P')
                    self.n_up[up_map[lord]] = ascmc[0]
        except: self.n_up = {}

    def calc_planets(self, jd, sidereal):
        flags = swe.FLG_SWIEPH | swe.FLG_SPEED
        if sidereal: flags |= swe.FLG_SIDEREAL
        data = {}
        plist = INDIAN_PLANETS.copy() if sidereal else INDIAN_PLANETS + WESTERN_PLANETS
        for pid, pnm in plist:
            res = swe.calc_ut(jd, pid, flags)[0]
            data[pnm] = {"lon": res[0], "retro": res[3] < 0}
            if pnm == "Ra": data["Ke"] = {"lon": (res[0]+180)%360, "retro": True}
        return data

engine = AstroEngine()

# ---------------- PDF GENERATOR ----------------
def create_pdf(days):
    pdf = AstroPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    pdf.set_font("Arial", "B", 12)
    pdf.cell(0, 10, f"Natal Reference Points - {name}", 0, 1, "L")
    
    all_sid = {**{k: v["lon"] for k, v in engine.n_sid.items()}, **engine.n_up, **engine.n_aprakasha}
    
    pdf.set_font("Arial", "B", 9)
    pdf.cell(0, 6, "1. SIDEREAL POINTS", 0, 1, "L")
    pdf.set_font("Arial", "", 8)
    pdf.multi_cell(0, 5, " | ".join([f"{k}: {v:.2f}°" for k, v in all_sid.items()]))
    
    pdf.set_font("Arial", "B", 9)
    pdf.cell(0, 6, "2. TROPICAL SYMMETRY", 0, 1, "L")
    pdf.set_font("Arial", "", 8)
    pdf.multi_cell(0, 5, "ANTISCIA: " + " | ".join([f"{k}: {v:.2f}°" for k, v in engine.n_ant.items()]))
    pdf.multi_cell(0, 5, "CONTRA-ANTISCIA: " + " | ".join([f"{k}: {v:.2f}°" for k, v in engine.n_cant.items()]))
    pdf.ln(5)

    malefics = ["Gulika", "Kala", "Dhuma", "Vyatipata", "Mrityu", "Sa", "Ma", "Ra", "Ke"]
    
    with Progress() as progress:
        task = progress.add_task("[cyan]Scanning Days...", total=days)
        for i in range(days):
            day = datetime.now() + timedelta(days=i)
            tjd = swe.julday(day.year, day.month, day.day, 12.0)
            hits = []
            
            t_trop = engine.calc_planets(tjd, False)
            for tp, t in t_trop.items():
                r = " (R)" if t["retro"] else ""
                for np, alon in engine.n_ant.items():
                    if abs(t["lon"]-alon) < ORB: hits.append(f"[TROPICAL] {tp}{r} hits Antiscion of {np}")
                for np, clon in engine.n_cant.items():
                    if abs(t["lon"]-clon) < ORB: hits.append(f"[TROPICAL] {tp}{r} hits Contra-Antiscion of {np}")

            t_sid = engine.calc_planets(tjd, True)
            for tp, t in t_sid.items():
                r = " (R)" if t["retro"] else ""
                for natal_name, natal_lon in all_sid.items():
                    if abs(t["lon"] - natal_lon) < ORB:
                        tag = "[CRITICAL]" if natal_name in malefics else "[INFO]"
                        hits.append(f"[SIDEREAL{tag}] {tp}{r} Conjunct Natal {natal_name}")

            if hits:
                if pdf.get_y() > 250: pdf.add_page()
                pdf.set_font("Arial", "B", 10); pdf.set_fill_color(240, 240, 240)
                pdf.cell(0, 7, f"DATE: {day.strftime('%d-%b-%Y')}", 1, 1, "L", True)
                pdf.set_font("Arial", "", 9)
                for h in hits: pdf.cell(0, 6, f"  > {h}", 0, 1)
                pdf.ln(2)
            progress.update(task, advance=1)

    try:
        fname = f"Forecast_{name}.pdf".replace(" ", "_")
        pdf.output(fname)
        console.print(f"\n[bold green]Complete Report Generated:[/] {fname}")
        time.sleep(1)
    except PermissionError:
        console.print(f"\n[bold red]ERROR: Close the PDF file first![/]")

create_pdf(scan_days)

# ---------------- UI LAYOUT ----------------
def get_chart():
    tjd = swe.julday(engine.view_date.year, engine.view_date.month, engine.view_date.day, 12.0)
    transit = engine.calc_planets(tjd, engine.mode=="SIDEREAL")
    natal = engine.n_sid if engine.mode=="SIDEREAL" else engine.n_trop
    grid = {i:{"n":[], "t":[]} for i in range(1,13)}
    for p,v in natal.items(): grid[int(v["lon"]/30)+1]["n"].append(f"{p} {fmt_deg(v)}")
    for p,v in transit.items(): grid[int(v["lon"]/30)+1]["t"].append(f"{p} {fmt_deg(v)}")
    
    def cell(n): return f"[green]{' '.join(grid[n]['n'])}[/]\n[red]{' '.join(grid[n]['t'])}[/]"
    t = Table.grid(expand=True)
    for _ in range(4): t.add_column()
    t.add_row(Panel(cell(12)),Panel(cell(1)),Panel(cell(2)),Panel(cell(3)))
    aya_str = f"Aya: {int(engine.ayan_val)}°{int((engine.ayan_val%1)*60)}'"
    t.add_row(Panel(cell(11)),Align.center(f"[bold]{engine.mode}[/]"),Align.center(aya_str),Panel(cell(4)))
    t.add_row(Panel(cell(10)),"","",Panel(cell(5)))
    t.add_row(Panel(cell(9)),Panel(cell(8)),Panel(cell(7)),Panel(cell(6)))
    return t

def get_impact_table():
    table = Table(expand=True)
    table.add_column("Transit", style="red")
    table.add_column("Hits Natal", style="green")
    table.add_column("Logic", style="cyan")
    tjd = swe.julday(engine.view_date.year, engine.view_date.month, engine.view_date.day, 12.0)
    tset = engine.calc_planets(tjd, engine.mode=="SIDEREAL")
    for tp, t in tset.items():
        r_mark = " (R)" if t["retro"] else ""
        if engine.mode == "SIDEREAL":
            for un, ul in {**engine.n_up, **engine.n_aprakasha}.items():
                if abs(t["lon"]-ul) < ORB: table.add_row(f"{tp}{r_mark}", un, "Shadow")
        else:
            for np, alon in engine.n_ant.items():
                if abs(t["lon"]-alon) < ORB: table.add_row(f"{tp}{r_mark}", f"Ant.{np}", "Mirror")
            for np, clon in engine.n_cant.items():
                if abs(t["lon"]-clon) < ORB: table.add_row(f"{tp}{r_mark}", f"C-Ant.{np}", "Mirror")
    return table

def make_layout():
    layout = Layout()
    layout.split_column(
        Layout(Panel(f"{name} | {engine.view_date:%d-%b-%Y} | [T] Mode | [J] Jump | [Arrows] Navigate", style="bold white on blue"), size=3),
        Layout(name="body")
    )
    layout["body"].split_row(
        Layout(Panel(get_chart(), title="Rasi Chart"), ratio=2),
        Layout(Panel(get_impact_table(), title="Active Hits"), ratio=1)
    )
    return layout

# ---------------- KEYBOARD LOGIC ----------------
exit_flag = False

def on_press(key):
    global exit_flag
    try:
        if key == keyboard.Key.right:
            engine.view_date += timedelta(days=1)
        elif key == keyboard.Key.left:
            engine.view_date -= timedelta(days=1)
        elif hasattr(key, 'char') and key.char is not None:
            k = key.char.lower()
            if k == "t":
                engine.mode = "TROPICAL" if engine.mode == "SIDEREAL" else "SIDEREAL"
            elif k == "j":
                # Signal the loop to handle the input out-of-band to avoid terminal locking
                engine.request_jump = True 
            elif k == "q":
                exit_flag = True
    except Exception:
        pass

engine.request_jump = False
listener = keyboard.Listener(on_press=on_press)
listener.start()

# ---------------- MAIN UI LOOP ----------------
sys.stdout.write("\033[?1049h") # Switch to Alt Screen
try:
    with Live(make_layout(), refresh_per_second=4, screen=True) as live:
        while not exit_flag:
            if engine.request_jump:
                live.stop() # Stop live display to allow standard input
                console.print("\n[bold yellow]JUMP TO DATE[/]")
                target = console.input("Enter Date (DD/MM/YYYY): ")
                try:
                    engine.view_date = datetime.strptime(target, "%d/%m/%Y")
                    console.print("[green]Date updated![/]")
                except:
                    console.print("[red]Invalid Format. Use DD/MM/YYYY[/]")
                time.sleep(1)
                engine.request_jump = False
                live.start() # Restart live display
            
            live.update(make_layout())
            time.sleep(0.1)
except KeyboardInterrupt:
    pass
finally:
    sys.stdout.write("\033[?1049l") # Restore Terminal
    listener.stop()