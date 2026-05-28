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
geolocator = Nominatim(user_agent="astro_master_v27_final")
ORB_LON = 1.5 
ORB_DEC = 1.0  

# ---------------- INPUT ----------------
console.clear()
console.print("[bold magenta]=== ASTRO ENGINE V27 (TOTAL INTEGRATION) ===[/bold magenta]\n")

name = input("Enter Name: ")
dob = input("Enter DOB (DD/MM/YYYY): ")
tob = input("Enter TOB (HH:MM:SS): ")
birth_city = input("Enter Birth City: ")

def fetch_coords(city):
    try:
        loc = geolocator.geocode(city, timeout=10)
        if loc: return float(loc.latitude), float(loc.longitude)
    except: pass
    return 16.12, 80.92 # Fallback for Challapally area

b_lat, b_lon = fetch_coords(birth_city)
g = geocoder.ip("me")
t_lat, t_lon = (g.latlng if g.latlng else (0.0, 0.0))

scan_days = int(input("\nHow many days to scan for Master PDF? "))

d, m, y = map(int, dob.split("/"))
hh, mm, ss = map(int, tob.split(":"))
birth_hour = hh + mm/60 + ss/3600

INDIAN_PLANETS = [(0,"Su"), (1,"Mo"), (2,"Me"), (3,"Ve"), (4,"Ma"), (5,"Ju"), (6,"Sa"), (11,"Ra")]
WESTERN_PLANETS = [(7,"Ur"), (8,"Ne"), (9,"Pl")]

# ---------------- ENGINE ----------------
class AstroEngine:
    def __init__(self):
        self.njd = swe.julday(y, m, d, birth_hour)
        swe.set_sid_mode(swe.SIDM_LAHIRI)
        self.mode = "SIDEREAL"
        self.view_date = datetime.now()
        
        # Natal Data
        self.n_sid = self.calc_planets(self.njd, True)
        self.n_trop = self.calc_planets(self.njd, False)
        
        # 13 Sidereal Points (8 Upagrahas + 5 Aprakasha)
        self.n_up = self.get_upagrahas()
        sun_lon = self.n_sid["Su"]["lon"]
        self.n_apra = {
            "Dhuma": (sun_lon + 133.333) % 360,
            "Vyatipata": (360 - (sun_lon + 133.333 + 53.333)) % 360,
            "Paridhi": (360 - (sun_lon + 133.333 + 53.333) + 180) % 360,
            "Chapa": (360 - (360 - (sun_lon + 133.333 + 53.333) + 180 + 16.666)) % 360,
            "Upaketu": (360 - (360 - (sun_lon + 133.333 + 53.333) + 180 + 16.666) + 16.666) % 360
        }
        
        # Tropical Symmetry
        self.n_ant = {k: (180 - v["lon"]) % 360 for k,v in self.n_trop.items()}
        self.dagdha_signs = self.get_dagdha_rashis(self.njd)

    def get_dagdha_rashis(self, jd):
        res_s, _ = swe.calc_ut(jd, 0, swe.FLG_SWIEPH)
        res_m, _ = swe.calc_ut(jd, 1, swe.FLG_SWIEPH)
        tithi = int(((res_m[0] - res_s[0]) % 360) / 12) + 1
        mapping = {1:[7,10], 2:[9,12], 3:[11,2], 4:[5,2], 5:[4,7], 6:[6,3], 7:[3,4], 8:[6,9], 9:[5,11], 10:[5,11], 11:[9,12], 12:[10,1], 13:[11,2], 14:[3,4,6,9], 15:[], 30:[]}
        return mapping.get(tithi if tithi <= 15 else tithi-15, [])

    def get_upagrahas(self):
        # Reliable calculation for Upagrahas based on Day/Night parts
        mjd = swe.julday(y, m, d, 0.0)
        # Using a safer way to get rise/set without the float error
        res = swe.rise_trans(mjd, swe.SUN, b_lon, b_lat, 0, int(swe.BIT_DISALLOW_CACHING | 1))
        r = res[1][0]
        res = swe.rise_trans(mjd, swe.SUN, b_lon, b_lat, 0, int(swe.BIT_DISALLOW_CACHING | 2))
        s = res[1][0]
        
        is_day = (self.njd >= r and self.njd <= s)
        part = ((s - r) if is_day else (1.0 - (s - r))) / 8.0
        start_l = int(swe.day_of_week(self.njd) if is_day else (swe.day_of_week(self.njd) + 4) % 7)
        lords = {0:"Kala", 1:"Gauri", 2:"Artha", 3:"Khanda", 4:"Mrityu", 5:"Yama", 6:"Gulika", 7:"M-Kala"}
        up_pos = {}
        for i in range(8):
            lord = (start_l + i) % 7
            seg = (r if is_day else s) + (i * part)
            _, ascmc = swe.houses_ex(seg, b_lat, b_lon, b'P')
            up_pos[lords.get(lord, f"U{i}")] = ascmc[0]
        return up_pos

    def calc_planets(self, jd, sidereal):
        flags = int(swe.FLG_SWIEPH | swe.FLG_SPEED | (swe.FLG_SIDEREAL if sidereal else 0))
        data = {}
        plist = INDIAN_PLANETS.copy() if sidereal else INDIAN_PLANETS + WESTERN_PLANETS
        for pid, pnm in plist:
            res, _ = swe.calc_ut(jd, pid, flags)
            data[pnm] = {"lon": res[0], "dec": res[1], "retro": res[3] < 0}
        return data

    def score_day(self, target_date):
        tjd = swe.julday(target_date.year, target_date.month, target_date.day, 12.0)
        t_sid = self.calc_planets(tjd, True)
        t_trop = self.calc_planets(tjd, False)
        score, hits = 0, []
        for tp, t in t_sid.items():
            for name, lon in {**self.n_up, **self.n_apra}.items():
                if abs(t["lon"] - lon) < ORB_LON:
                    wt = 2 if name == "Yama" else -4 if name == "Vyatipata" else -2
                    score += wt; hits.append(f"{tp} hit {name}")
        for tp, t in t_trop.items():
            for np, n in self.n_trop.items():
                if abs(t["dec"] - n["dec"]) < ORB_DEC:
                    wt = 2 if np in ["Ju","Ve","Su"] else -2 if np in ["Sa","Ma"] else 0
                    score += wt; hits.append(f"{tp} Para {np}")
            for np, alon in self.n_ant.items():
                if abs(t["lon"] - alon) < ORB_LON:
                    score += 1.5; hits.append(f"{tp} Antisc {np}")
        return score, hits

engine = AstroEngine()

# ---------------- UI HELPERS (FULL VERSION) ----------------
def get_dec_str(dec):
    side = "N" if dec >= 0 else "S"
    oob = "⭐" if abs(dec) > 23.44 else ""
    return f"{abs(dec):.1f}{side}{oob}"

def get_impact_table():
    table = Table(expand=True, box=None)
    table.add_column("Tr", style="red")
    table.add_column("Dec/Lon", style="yellow")
    table.add_column("Natal", style="green")
    table.add_column("Type", style="cyan")
    
    tjd = swe.julday(engine.view_date.year, engine.view_date.month, engine.view_date.day, 12.0)
    if engine.mode == "TROPICAL":
        t_trop = engine.calc_planets(tjd, False)
        for tp, t in t_trop.items():
            r = "(R)" if t["retro"] else ""
            for np, n in engine.n_trop.items():
                if abs(t["dec"] - n["dec"]) < ORB_DEC: table.add_row(f"{tp}{r}", get_dec_str(t['dec']), np, "Para")
            for np, alon in engine.n_ant.items():
                if abs(t["lon"] - alon) < ORB_LON: table.add_row(f"{tp}{r}", f"{t['lon']:.1f}", f"Ant.{np}", "Mirror")
    else:
        t_sid = engine.calc_planets(tjd, True)
        all_sid = {**{k: v["lon"] for k, v in engine.n_sid.items()}, **engine.n_up, **engine.n_apra}
        for tp, t in t_sid.items():
            r = "(R)" if t["retro"] else ""
            burnt = "🔥" if (int(t["lon"]/30)+1) in engine.dagdha_signs else ""
            for name, lon in all_sid.items():
                if abs(t["lon"] - lon) < ORB_LON: table.add_row(f"{tp}{r}{burnt}", f"{t['lon']:.1f}", name, "Hit")
    return table

def get_chart():
    tjd = swe.julday(engine.view_date.year, engine.view_date.month, engine.view_date.day, 12.0)
    transit = engine.calc_planets(tjd, engine.mode=="SIDEREAL")
    natal = engine.n_sid if engine.mode=="SIDEREAL" else engine.n_trop
    grid = {i:{"n":[], "t":[]} for i in range(1,13)}
    for p,v in natal.items(): grid[int(v["lon"]/30)+1]["n"].append(f"{p}")
    for p,v in transit.items(): grid[int(v["lon"]/30)+1]["t"].append(f"{p}")
    t = Table.grid(expand=True)
    for _ in range(4): t.add_column()
    def cell(n): 
        b = "🔥" if n in engine.dagdha_signs else ""
        return Panel(f"[green]{' '.join(grid[n]['n'])}[/]\n[red]{' '.join(grid[n]['t'])}[/]", title=f"H{n}{b}")
    t.add_row(cell(12), cell(1), cell(2), cell(3))
    t.add_row(cell(11), Align.center(f"{engine.mode}"), Align.center(f"{engine.view_date:%d-%b}"), cell(4))
    t.add_row(cell(10), "", "", cell(5))
    t.add_row(cell(9), cell(8), cell(7), cell(6))
    return t

def make_layout():
    score, _ = engine.score_day(engine.view_date)
    layout = Layout()
    layout.split_column(
        Layout(Panel(f"TARGET: {name} | SCORE: {score} | [T] Mode | [Q] Quit", style="white on blue"), size=3),
        Layout(name="body")
    )
    layout["body"].split_row(Layout(get_chart(), ratio=2), Layout(get_impact_table(), ratio=1))
    return layout

# ---------------- CONTROLS & PDF ----------------
def generate_pdf():
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", "B", 16); pdf.cell(0, 10, f"MASTER ASTRO FORECAST: {name}", 0, 1, "C")
    for i in range(scan_days):
        day = datetime.now() + timedelta(days=i)
        score, hits = engine.score_day(day)
        color = (0, 150, 0) if score >= 3 else (200, 0, 0) if score <= -3 else (0,0,0)
        pdf.set_text_color(*color); pdf.set_font("Arial", "B", 10)
        pdf.cell(0, 8, f"{day.strftime('%d-%b-%Y')} | Score: {score}", 1, 1, "L")
        pdf.set_font("Arial", "", 8); pdf.set_text_color(60,60,60)
        pdf.multi_cell(0, 5, " | ".join(hits) if hits else "Normal Day")
        pdf.ln(1)
    pdf.output(f"Master_{name}.pdf"); print(f"PDF Saved: Master_{name}.pdf")

generate_pdf()
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

listener = keyboard.Listener(on_press=on_press); listener.start()
sys.stdout.write("\033[?1049h")
try:
    with Live(make_layout(), refresh_per_second=4, screen=True) as live:
        while not exit_flag:
            if engine.request_jump:
                live.stop()
                target = console.input("\nJump Date (DD/MM/YYYY): ")
                try: engine.view_date = datetime.strptime(target, "%d/%m/%Y")
                except: pass
                engine.request_jump = False; live.start()
            live.update(make_layout()); time.sleep(0.1)
except KeyboardInterrupt: pass
finally:
    sys.stdout.write("\033[?1049l"); listener.stop()