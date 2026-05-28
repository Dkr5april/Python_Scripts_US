import swisseph as swe
import os, sys, time
from datetime import datetime, timedelta
from pynput import keyboard
from geopy.geocoders import Nominatim
from rich.live import Live
from rich.table import Table
from rich.console import Console
from rich.layout import Layout
from rich.panel import Panel
from rich.align import Align

# ---------------- CONFIGURATION ----------------
if sys.platform == "win32":
    os.system("color")

swe.set_ephe_path("./ephe") 
console = Console()
geolocator = Nominatim(user_agent="pulippani_final_master_engine")

# ---------------- INPUT DATA ----------------
console.clear()
console.print("[bold yellow]=== PULIPPANI SIDDHAR 300: COMPLETE MASTER ENGINE ===[/bold yellow]\n")

name = input("Enter Name: ")
dob = input("Enter DOB (DD/MM/YYYY): ")
tob = input("Enter TOB (HH:MM:SS): ")
birth_city = input("Enter Birth City: ")

def fetch_coords(city):
    try:
        loc = geolocator.geocode(city, timeout=5)
        if loc: return loc.latitude, loc.longitude, 5.5
    except: pass
    return 33.4942, -111.9261, -7.0 # Default Scottsdale per user preference

b_lat, b_lon, tz = fetch_coords(birth_city)
d, m, y = map(int, dob.split("/"))
hh, mm, ss = map(int, tob.split(":"))
birth_hour_utc = (hh + mm/60 + ss/3600) - tz

# ---------------- THE ENGINE ----------------
class PulippaniEngine:
    def __init__(self):
        swe.set_sid_mode(swe.SIDM_LAHIRI)
        self.view_date = datetime.now()
        self.njd = swe.julday(y, m, d, birth_hour_utc)
        self.natal_planets = self.calc_planets(self.njd)
        self.lagna_lon = self.calc_lagna(self.njd, b_lat, b_lon)
        self.rasi_lords = ["Ma", "Ve", "Me", "Mo", "Su", "Me", "Ve", "Ma", "Ju", "Sa", "Sa", "Ju"]
        
    def calc_planets(self, jd):
        flags = swe.FLG_SWIEPH | swe.FLG_SPEED | swe.FLG_SIDEREAL
        planets = [(0,"Su"), (1,"Mo"), (2,"Me"), (3,"Ve"), (4,"Ma"), (5,"Ju"), (6,"Sa"), (11,"Ra")]
        data = {}
        for pid, p_name in planets:
            res = swe.calc_ut(jd, pid, flags)[0]
            data[p_name] = {"lon": res[0], "speed": res[3]}
            if p_name == "Ra":
                data["Ke"] = {"lon": (res[0]+180)%360, "speed": res[3]}
        return data

    def calc_lagna(self, jd, lat, lon):
        res = swe.houses_ex(jd, lat, lon, b'W')[0] 
        return res[0] 

    def get_house(self, planet_lon):
        lagna_rasi = int(self.lagna_lon / 30)
        planet_rasi = int(planet_lon / 30)
        return (planet_rasi - lagna_rasi + 12) % 12 + 1

    def get_analysis(self):
        results = []
        
        # 1. PLACEMENT DB (Slokas 61-150 & 280-300)
        placements = {
            "Su": {1:(61,"Sun H1: Bold, Status"), 2:(62,"Sun H2: Wealth"), 3:(63,"Sun H3: Brave"), 4:(64,"Sun H4: Philosophy"), 5:(65,"Sun H5: Intellect"), 6:(66,"Sun H6: Victory"), 7:(67,"Sun H7: Late Marriage"), 8:(68,"Sun H8: Occult"), 9:(69,"Sun H9: Religious"), 10:(70,"Sun H10: Peak Power"), 11:(71,"Sun H11: Income"), 12:(72,"Sun H12: Foreign")},
            "Mo": {1:(73,"Moon H1: Moody"), 2:(74,"Moon H2: Sweet Speech"), 3:(75,"Moon H3: Arts"), 4:(76,"Moon H4: Maternal Comfort"), 5:(77,"Moon H5: Creative"), 6:(78,"Moon H6: Health Risk"), 7:(79,"Moon H7: PR Success"), 8:(80,"Moon H8: Anxiety"), 9:(81,"Moon H9: Fortune"), 10:(82,"Moon H10: Fame"), 11:(83,"Moon H11: Popularity"), 12:(84,"Moon H12: Secrets")},
            "Ma": {1:(85,"Mars H1: Scar/Leader"), 2:(86,"Mars H2: Land Wealth"), 3:(87,"Mars H3: Tech Skill"), 4:(88,"Mars H4: Property Conflict"), 5:(89,"Mars H5: Risk Taker"), 6:(90,"Mars H6: Shatru-Hanta"), 7:(91,"Mars H7: Conflict"), 8:(92,"Mars H8: Sudden Crisis"), 9:(93,"Mars H9: Foreign Luck"), 10:(94,"Mars H10: Great Status"), 11:(95,"Mars H11: Sibling Gain"), 12:(96,"Mars H12: Expenditure")},
            "Me": {1:(97,"Merc H1: Genius"), 2:(98,"Merc H2: Education"), 3:(99,"Merc H3: Writing"), 4:(100,"Merc H4: scholar"), 5:(101,"Merc H5: Astrology"), 6:(102,"Merc H6: Debates"), 7:(103,"Merc H7: Commerce"), 8:(104,"Merc H8: Long Life"), 9:(105,"Merc H9: Philosophy"), 10:(106,"Merc H10: Data/Admin"), 11:(107,"Merc H11: Networks"), 12:(108,"Merc H12: Isolation")},
            "Ju": {1:(109,"Jup H1: Divine Wisdom"), 2:(110,"Jup H2: Family Honor"), 3:(111,"Jup H3: Respected"), 4:(112,"Jup H4: Land/Peace"), 5:(113,"Jup H5: Creativity"), 6:(114,"Jup H6: No Enemies"), 7:(115,"Jup H7: Pious Partner"), 8:(116,"Jup H8: Occult Depth"), 9:(117,"Jup H9: Supreme Luck"), 10:(118,"Jup H10: Ministry"), 11:(119,"Jup H11: Gold/Gains"), 12:(120,"Jup H12: Charity/Moksha")},
            "Ve": {1:(121,"Ven H1: Art/Beauty"), 2:(122,"Ven H2: Jewels"), 3:(123,"Ven H3: Sisters"), 4:(124,"Ven H4: Palace"), 5:(125,"Ven H5: Romance"), 6:(126,"Ven H6: Service"), 7:(127,"Ven H7: Passion"), 8:(128,"Ven H8: Hidden Wealth"), 9:(129,"Ven H9: Luxury Luck"), 10:(130,"Ven H10: Fame"), 11:(131,"Ven H11: Income"), 12:(132,"Ven H12: Maximum Comfort")},
            "Sa": {1:(133,"Sat H1: Serious"), 2:(134,"Sat H2: Late Wealth"), 3:(135,"Sat H3: Hard Work"), 4:(136,"Sat H4: Away Home"), 5:(137,"Sat H5: Late Children"), 6:(138,"Sat H6: Destroyer Enemies"), 7:(139,"Sat H7: Stable Trade"), 8:(140,"Sat H8: Longevity"), 9:(141,"Sat H9: Spiritual"), 10:(142,"Sat H10: Responsibility"), 11:(143,"Sat H11: Industry Wealth"), 12:(144,"Sat H12: Solitude")},
            "Ra": {1:(280,"Rahu H1: Eccentric"), 2:(281,"Rahu H2: Foreign Wealth"), 3:(282,"Rahu H3: Great Hero"), 6:(285,"Rahu H6: Massive Success"), 10:(290,"Rahu H10: Tech Fame"), 11:(291,"Rahu H11: Windfall")},
            "Ke": {12:(299,"Ketu H12: Moksha Karaka")}
        }

        # 2. COMBINATION & YOGA SCANNER (Slokas 150-250)
        h_occ = {i: set() for i in range(1, 13)}
        planet_house_map = {}
        for p, v in self.natal_planets.items():
            h = self.get_house(v['lon'])
            h_occ[h].add(p)
            planet_house_map[p] = h
            if p in placements and h in placements[p]:
                sid, txt = placements[p][h]
                results.append(f"[*] Sloka {sid}: {txt}")

        for h, pts in h_occ.items():
            if {"Su", "Me"}.issubset(pts): results.append(f"[+] Sloka 140: Budha-Aditya in H{h}")
            if {"Mo", "Ju"}.issubset(pts): results.append(f"[+] Sloka 110: Gaja Kesari in H{h}")
            if {"Mo", "Ma"}.issubset(pts): results.append(f"[+] Sloka 182: Chandra Mangala in H{h}")
            if {"Ma", "Sa"}.issubset(pts): results.append(f"[!] Sloka 205: Agni-Maruta (Injury Risk) H{h}")
            if {"Su", "Sa"}.issubset(pts): results.append(f"[!] Sloka 157: Pithru-Dosha (Father Conflict) H{h}")
            if {"Ju", "Ra"}.issubset(pts): results.append(f"[!] Sloka 210: Guru-Chandala in H{h}")

        # 3. LORDSHIP EXCHANGE (Parivartana - Sloka 265+)
        lagna_rasi = int(self.lagna_lon / 30)
        for h1 in range(1, 13):
            rasi1 = (lagna_rasi + h1 - 1) % 12
            lord1 = self.rasi_lords[rasi1]
            pos_of_lord1 = planet_house_map.get(lord1)
            
            if pos_of_lord1:
                rasi_target = (lagna_rasi + pos_of_lord1 - 1) % 12
                lord_of_target = self.rasi_lords[rasi_target]
                if planet_house_map.get(lord_of_target) == h1 and h1 != pos_of_lord1:
                    results.append(f"[+] Sloka 265: Parivartana Yoga between H{h1} and H{pos_of_lord1}")

        return results if results else ["Scanning for Pulippani combinations..."]

# ---------------- UI ENGINE ----------------
engine = PulippaniEngine()

def get_chart_table():
    tjd = swe.julday(engine.view_date.year, engine.view_date.month, engine.view_date.day, 12.0 - 5.5)
    transit = engine.calc_planets(tjd)
    grid = {i:{"n":[], "t":[]} for i in range(1,13)}
    for p,v in engine.natal_planets.items(): grid[int(v["lon"]/30)+1]["n"].append(p)
    grid[int(engine.lagna_lon/30)+1]["n"].append("[bold yellow]Lagn[/]")
    for p,v in transit.items(): grid[int(v["lon"]/30)+1]["t"].append(p)

    def cell(n): return f"[green]{' '.join(grid[n]['n'])}[/]\n[red]{' '.join(grid[n]['t'])}[/]"
    t = Table.grid(expand=True)
    for _ in range(4): t.add_column()
    t.add_row(Panel(cell(12)),Panel(cell(1)),Panel(cell(2)),Panel(cell(3)))
    t.add_row(Panel(cell(11)),Align.center("PULIPPANI"),Align.center("300 ENGINE"),Panel(cell(4)))
    t.add_row(Panel(cell(10)),"","",Panel(cell(5)))
    t.add_row(Panel(cell(9)),Panel(cell(8)),Panel(cell(7)),Panel(cell(6)))
    return t

def get_details_panel():
    insights = engine.get_analysis()
    side_layout = Layout()
    side_layout.split_column(
        Layout(Panel("\n".join(insights), title="Sloka Insights (1-300)")),
        Layout(Panel(f"Name: {name}\nLocation: {birth_city}\nDate: {dob}", title="Native Profile"), size=6)
    )
    return side_layout

def make_layout():
    layout = Layout()
    layout.split_column(
        Layout(Panel(f"Pulippani Siddhar Master Engine | Transit: {engine.view_date:%d-%b-%Y}"), size=3),
        Layout(name="body")
    )
    layout["body"].split_row(
        Layout(Panel(get_chart_table(), title="Chart (Green=Natal, Red=Transit)"), ratio=2),
        Layout(get_details_panel(), ratio=1)
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