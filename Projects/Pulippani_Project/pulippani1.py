import swisseph as swe
import os, sys, time, json
from datetime import datetime, timedelta
from pynput import keyboard
from geopy.geocoders import Nominatim
from rich.live import Live
from rich.table import Table
from rich.console import Console
from rich.layout import Layout
from rich.panel import Panel
from rich.align import Align

# ---------------- STABILITY & PATHS ----------------
if sys.platform == "win32":
    os.system("color")

swe.set_ephe_path("./ephe") 
console = Console()
geolocator = Nominatim(user_agent="pulippani_project_v1")

# ---------------- INPUT & DEFAULTS ----------------
console.clear()
console.print("[bold yellow]=== PULIPPANI SIDDHAR AI ENGINE (Whole Sign) ===[/bold yellow]\n")

name = input("Enter Name: ")
dob = input("Enter DOB (DD/MM/YYYY): ")
tob = input("Enter TOB (HH:MM:SS): ")
birth_city = input("Enter Birth City: ")

def fetch_coords(city):
    try:
        loc = geolocator.geocode(city, timeout=5)
        if loc: 
            return loc.latitude, loc.longitude, 5.5
    except: 
        pass
    return 16.1176, 80.9314, 5.5 

b_lat, b_lon, tz = fetch_coords(birth_city)

d, m, y = map(int, dob.split("/"))
hh, mm, ss = map(int, tob.split(":"))
birth_hour_utc = (hh + mm/60 + ss/3600) - tz

# ---------------- ENGINE CLASS ----------------
class PulippaniEngine:
    def __init__(self):
        swe.set_sid_mode(swe.SIDM_LAHIRI)
        self.view_date = datetime.now()
        self.njd = swe.julday(y, m, d, birth_hour_utc)
        self.natal_planets = self.calc_planets(self.njd)
        self.lagna_lon = self.calc_lagna(self.njd, b_lat, b_lon)
        
    def calc_planets(self, jd):
        flags = swe.FLG_SWIEPH | swe.FLG_SPEED | swe.FLG_SIDEREAL
        planets = [(0,"Su"), (1,"Mo"), (2,"Me"), (3,"Ve"), (4,"Ma"), (5,"Ju"), (6,"Sa"), (11,"Ra")]
        data = {}
        for pid, p_name in planets:
            res = swe.calc_ut(jd, pid, flags)[0]
            lon, vel = res[0], res[3]
            data[p_name] = {"lon": lon, "retro": vel < 0}
            if p_name == "Ra":
                data["Ke"] = {"lon": (lon+180)%360, "retro": True}
        return data

    def calc_lagna(self, jd, lat, lon):
        res = swe.houses_ex(jd, lat, lon, b'W')[0] 
        return res[0] 

    def get_house(self, planet_lon):
        lagna_rasi = int(self.lagna_lon / 30)
        planet_rasi = int(planet_lon / 30)
        house = (planet_rasi - lagna_rasi + 12) % 12 + 1
        return house

    def analyze_pulippani_full(self):
        """
        Comprehensive Analysis based on Pulippani Siddhar's 300 Slokas.
        Consolidated into English for terminal stability.
        """
        results = []
        
        # 1. LORDSHIP MAPPING
        # 1/8=Ma, 2/7=Ve, 3/6=Me, 4=Mo, 5=Su, 9/12=Ju, 10/11=Sa
        lord_map = {1:"Ma", 2:"Ve", 3:"Me", 4:"Mo", 5:"Su", 6:"Me", 
                    7:"Ve", 8:"Ma", 9:"Ju", 10:"Sa", 11:"Sa", 12:"Ju"}
        
        # Calculate House Lords based on Lagna
        lagna_sign = int(self.lagna_lon / 30) + 1
        house_lords = {}
        for h in range(1, 13):
            sign_at_house = (lagna_sign + h - 2) % 12 + 1
            house_lords[h] = lord_map[sign_at_house]

        # 2. EXALTATION & DEBILITATION MAPS
        exalt = {"Su": 1, "Mo": 2, "Ma": 10, "Me": 6, "Ju": 4, "Ve": 12, "Sa": 7}
        debilit = {"Su": 7, "Mo": 8, "Ma": 4, "Me": 12, "Ju": 10, "Ve": 6, "Sa": 1}

        # 3. CORE CALCULATIONS (Slokas 1-150)
        for p, v in self.natal_planets.items():
            rasi = int(v['lon'] / 30) + 1
            house = self.get_house(v['lon'])

            # Foundational Strengths (Exaltation/Debilitation)
            if p in exalt and rasi == exalt[p]:
                results.append(f"[+] {p} is EXALTED - High Strength (Sloka 15-21)")
            if p in debilit and rasi == debilit[p]:
                results.append(f"[-] {p} is DEBILITATED - Low Strength (Sloka 22-24)")

            # Directional Strength (Digbala)
            if p == "Su" and house == 10: results.append("[*] SUN has DIGBALA - Career Peak (Sloka 36)")
            if p == "Ma" and house == 10: results.append("[*] MARS has DIGBALA - Success in Work (Sloka 37)")
            if p == "Ju" and house == 1:  results.append("[*] JUPITER has DIGBALA - Protection (Sloka 40)")
            if p == "Sa" and house == 7:  results.append("[*] SATURN has DIGBALA - Social Influence (Sloka 39)")
            if p == "Me" and house == 1:  results.append("[*] MERCURY has DIGBALA - Sharp Intellect (Sloka 38)")

        # 4. YOGA & LORD PLACEMENTS (Slokas 151-300)
        # Check for Dharma Karmadhipati Yoga (9th & 10th lords together)
        l9, l10 = house_lords[9], house_lords[10]
        if l9 in self.natal_planets and l10 in self.natal_planets:
            if self.get_house(self.natal_planets[l9]['lon']) == self.get_house(self.natal_planets[l10]['lon']):
                results.append("[+] DHARMA KARMADHIPATI YOGA - Ethical Success (Sloka 152)")

        # Check for Dhana Yoga (2nd lord in 11th)
        l2 = house_lords[2]
        if l2 in self.natal_planets and self.get_house(self.natal_planets[l2]['lon']) == 11:
            results.append("[+] STRONG DHANA YOGA - Wealth Inflow (Sloka 174)")

        # Check for Vipreet Rajayoga (8th lord in 6th or 12th)
        l8 = house_lords[8]
        if l8 in self.natal_planets:
            h8 = self.get_house(self.natal_planets[l8]['lon'])
            if h8 in [6, 12]:
                results.append("[+] VIPREET RAJAYOGA - Gain through challenges (Sloka 248)")

        # Malefic in 8th (Caution Sloka)
        for p in ["Ma", "Sa", "Ra"]:
            if p in self.natal_planets and self.get_house(self.natal_planets[p]['lon']) == 8:
                results.append(f"[!] {p} in 8th house - Health/Obstacle Caution (Sloka 101/201)")

        return results

engine = PulippaniEngine()

# ---------------- UI COMPONENTS ----------------
def get_chart_table():
    tjd = swe.julday(engine.view_date.year, engine.view_date.month, engine.view_date.day, 12.0 - 5.5)
    transit = engine.calc_planets(tjd)
    grid = {i:{"n":[], "t":[]} for i in range(1,13)}
    for p,v in engine.natal_planets.items():
        grid[int(v["lon"]/30)+1]["n"].append(p)
    grid[int(engine.lagna_lon/30)+1]["n"].append("[bold yellow]Lagn[/]")
    for p,v in transit.items():
        grid[int(v["lon"]/30)+1]["t"].append(p)

    def cell(n):
        return f"[green]{' '.join(grid[n]['n'])}[/]\n[red]{' '.join(grid[n]['t'])}[/]"

    t = Table.grid(expand=True)
    for _ in range(4): t.add_column()
    t.add_row(Panel(cell(12)),Panel(cell(1)),Panel(cell(2)),Panel(cell(3)))
    t.add_row(Panel(cell(11)),Align.center("PULIPPANI"),Align.center("PROJECT"),Panel(cell(4)))
    t.add_row(Panel(cell(10)),"","",Panel(cell(5)))
    t.add_row(Panel(cell(9)),Panel(cell(8)),Panel(cell(7)),Panel(cell(6)))
    return t

def get_details_panel():
    # Table for Degrees
    table = Table(title="Natal Analysis", show_header=True, header_style="bold cyan", expand=True)
    table.add_column("Planet")
    table.add_column("House")
    for p, v in engine.natal_planets.items():
        h = engine.get_house(v['lon'])
        table.add_row(p, f"H{h}")

    # Pulippani Insights
    insights = engine.analyze_pulippani_full()
    insight_text = "\n".join(insights) if insights else "No major yogas found in Batch 1."
    
    # Using a sub-layout to show both table and insights
    side_layout = Layout()
    side_layout.split_column(
        Layout(Panel(table, title="Planet Positions")),
        Layout(Panel(insight_text, title="Pulippani Batch 1 Insights"))
    )
    return side_layout

def make_layout():
    layout = Layout()
    layout.split_column(
        Layout(Panel(f"Name: {name} | Transit: {engine.view_date:%d-%b-%Y} | Mode: Whole Sign"), size=3),
        Layout(name="body")
    )
    layout["body"].split_row(
        Layout(Panel(get_chart_table(), title="Chart (Green: Natal | Red: Transit)"), ratio=2),
        Layout(get_details_panel(), ratio=1)
    )
    return layout

# ---------------- CONTROLS & RUN ----------------
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