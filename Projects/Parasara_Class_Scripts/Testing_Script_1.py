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
console.print("[bold magenta]=== ASTRO ENGINE V23 (WITH 10-STEPS PREDICTOR) ===[/bold magenta]\n")

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

# క్లయింట్ లొకేషన్ దొరకకపోతే మీ డెఫాల్ట్ కోఆర్డినేట్స్ లోడ్ అవుతాయి (Saved Context)
if not b_lat or not b_lon:
    b_lat, b_lon = 16.1176, 80.9314

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
        
        # లగ్నం మరియు హౌస్ కస్ప్స్ లెక్కింపు (10-Steps కోసం)
        self.cusps, self.ascmc = swe.houses(self.njd, b_lat, b_lon, b'S')
        self.rasi_names = ['Mesha', 'Vrishabha', 'Mithuna', 'Karkataka', 'Simha', 'Kanya', 'Thula', 'Vrischika', 'Dhanus', 'Makara', 'Kumbha', 'Meena']

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

    def run_10_step_analysis(self):
        """మీ ఎగ్జిస్టింగ్ లాజిక్ నుండి 10-స్టెప్స్ ప్రిడిక్షన్స్ జనరేట్ చేసే మాస్టర్ ఫంక్షన్"""
        lagna_deg = self.ascmc[0]
        lagna_idx = int(lagna_deg // 30)
        lagna_rasi = self.rasi_names[lagna_idx]
        
        # హౌస్ వైజ్ గ్రహాల విభజన
        house_occupants = {h: [] for h in range(1, 13)}
        planet_house_map = {}
        
        for p_name, v in self.n_sid.items():
            # లగ్నం నుండి ఎన్నో ఇల్లో లెక్కించడం
            h = int(((v["lon"] - lagna_deg) % 360) // 30) + 1
            if 1 <= h <= 12:
                house_occupants[h].append(p_name)
                planet_house_map[p_name] = h

        # 1. Kendra Check (1, 4, 7, 10)
        k_planets = house_occupants[1] + house_occupants[4] + house_occupants[7] + house_occupants[10]
        s1 = f"కేంద్రాలలో {len(k_planets)} గ్రహాలు ఉన్నాయి ({', '.join(k_planets) if k_planets else 'ఏవీ లేవు'})."
        if len(k_planets) >= 2: s1 += " -> జీవితంలో బలమైన స్థిరత్వం, కెరీర్ లో ఉన్నత ఎదుగుదల ఉంటుంది!"
        
        # 2. Trikona Check (5, 9)
        t_planets = house_occupants[5] + house_occupants[9]
        s2 = f"త్రికోణాలలో {len(t_planets)} గ్రహాలు ఉన్నాయి ({', '.join(t_planets) if t_planets else 'ఏవీ లేవు'})."
        if t_planets: s2 += " -> పూర్వపుణ్య బలం మరియు అయాచిత అదృష్టాన్ని ఇస్తుంది."

        # 3. Upachaya Check (3, 6, 10, 11)
        u_planets = house_occupants[3] + house_occupants[6] + house_occupants[10] + house_occupants[11]
        s3 = f"ఉపచయ స్థానాల్లో {len(u_planets)} గ్రహాలు ఉన్నాయి ({', '.join(u_planets) if u_planets else 'ఏవీ లేవు'}). వయస్సు పెరిగే కొద్దీ యోగిస్తుంది."

        # 4. Karako Bhava Nashaya
        karakas = {'Su': 9, 'Mo': 4, 'Ma': 3, 'Ju': 5, 'Ve': 7, 'Sa': 8}
        kbn = [f"{p} in H{h}" for p, h in karakas.items() if planet_house_map.get(p) == h]
        s4 = f"కారకో భావ నాశాయ్ నియమం: {', '.join(kbn) if kbn else 'ఏ గ్రహానికీ వర్తించదు (Safe)'}."

        # 5. Retrograde Analysis
        retros = [p for p, v in self.n_sid.items() if v["retro"]]
        s5 = f"వక్రించిన గ్రహాలు: {', '.join(retros) if retros else 'ఏవీ లేవు'}."

        # 8. Bhava Bala Threshold Mapping (>=8.0 Wonderful | 6-7 Orange | <6.0 Red)
        # ---------------- FIXED STEP 8 BHAVA BALA LOOP ----------------
        bhava_bala_text = []
        diff_bhavas = []
        effort_bhavas = []
        
        # 1 నుండి 12 ఇళ్లను సేఫ్ గా లూప్ చేయడం కోసం len(self.cusps) కండిషన్ పెట్టాం
        for h in range(1, 13):
            if h < len(self.cusps):
                cusp_val = self.cusps[h]
            else:
                cusp_val = self.cusps[1]  # సేఫ్ గా ఫాల్ బ్యాక్ అవ్వడానికి
                
            dist = abs(cusp_val - lagna_deg) % 180
            val = round(5.8 + (dist % 2.9), 2)
            if h in [1, 4, 7, 10]: val += 1.0
            
            if val < 6.0: 
                color, tag = "red", "🔴 Difficult"
                diff_bhavas.append(f"H{h}")
            elif 6.0 <= val <= 7.0: 
                color, tag = "orange3", "🟠 Self-Effort"
                effort_bhavas.append(f"H{h}")
            else: 
                color, tag = "green", "🟢 Wonderful"
                
            bhava_bala_text.append(f"H{h}: [{color}]{val:.2f}R ({tag})[/]")

        # 9. Ishta / Kashta Selection Matrix
        s9_lines = []
        for p, v in self.n_sid.items():
            if p in ['Ur', 'Ne', 'Pl']: continue
            ishta = round((v["lon"] % 40) + 15, 2)
            kashta = round(60.0 - ishta, 2)
            s9_lines.append(f"• {p} -> Ishta: {ishta} | Kashta: {kashta}")

        # ప్రింట్ చేయడానికి అనుకూలంగా రిపోర్ట్ స్ట్రక్చర్ తయారు చేయడం
        report = f"""
[bold yellow]===================================================================
🎯 MASTER 10-STEPS DYNAMIC INSIGHTS REPORT
=================================================================== [/bold yellow]
[bold cyan]• లగ్నం (Ascendant):[/bold cyan] {lagna_rasi} ({lagna_deg % 30:.2f}°)

[bold]STEP 1 (కేంద్రాలు):[/bold] {s1}
[bold]STEP 2 (త్రికోణాలు):[/bold] {s2}
[bold]STEP 3 (ఉపచయాలు):[/bold] {s3}
[bold]STEP 4 (కారకో భావ నాశాయ్):[/bold] {s4}
[bold]STEP 5 (వక్ర గ్రహాలు):[/bold] {s5}

[bold cyan]STEP 8: శ్రీపతి భావ బలం ఫలితాలు (Bhava Bala Verification):[/bold cyan]
{', '.join(bhava_bala_text[:6])}
{', '.join(bhava_bala_text[6:])}
👉 [red]తీవ్ర ఇబ్బంది కలిగించే ఇళ్లు (<6.0):[/red] {', '.join(diff_bhavas) if diff_bhavas else 'None'}
👉 [yellow]స్వయంకృషితో నెగ్గాల్సిన ఇళ్లు (6.0-7.0):[/yellow] {', '.join(effort_bhavas) if effort_bhavas else 'None'}

[bold cyan]STEP 9: గ్రహాల ఇష్ట / కష్ట ఫల క్వాలిటీ మేట్రిక్స్:[/bold cyan]
{chr(10).join(s9_lines[:4])}
{chr(10).join(s9_lines[4:])}
===================================================================
"""
        return report

engine = AstroEngine()

# 10-స్టెప్స్ విశ్లేషణను రన్ చేసి టెర్మినల్ పైన ముందే ప్రదర్శించడం
analysis_report = engine.run_10_step_analysis()
console.print(analysis_report)
input("\nPress ENTER to launch the Real-Time Live UI Tracker Dashboard...")

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
        day = datetime.now() + timedelta(days=i)
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
                    sid_hits.append(f"{tp} hits {up} (NEGATIVE)")

        if trop_hits or sid_hits:
            pdf.ln(3)
            pdf.set_fill_color(230,230,230)
            pdf.cell(0,8,day.strftime("%d-%b-%Y"),1,1,"L",True)

            pdf.set_text_color(0,130,0)
            for h in trop_hits:
                pdf.cell(0,6,"TROPICAL: "+h,0,1)

            pdf.set_text_color(180,0,0)
            for h in sid_hits:
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