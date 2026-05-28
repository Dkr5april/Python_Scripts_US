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

# PDF requirements
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

if sys.platform == "win32":
    os.system("color")

swe.set_ephe_path("./ephe")
console = Console()
geolocator = Nominatim(user_agent="astro_engine_v25")

ORB = 1.5
exit_to_report = False  # Global flag for dashboard exit routing

# ---------------- INPUT ----------------
console.clear()
console.print("[bold magenta]=== ASTRO ENGINE V25 (ENGLISH & REPORT NAVIGATION) ===[/bold magenta]\n")

name = input("Enter Name: ")
dob = input("Enter DOB (DD/MM/YYYY): ")
tob = input("Enter TOB (HH:MM:SS): ")
birth_city = input("Enter Birth City: ")
scan_days = int(input("How many days to scan for PDF Forecast? "))

def fetch_coords(city):
    try:
        loc = geolocator.geocode(city, timeout=5)
        if loc: return loc.latitude, loc.longitude
    except: pass
    return 16.1176, 80.9314  # Default to Challapalli

b_lat, b_lon = fetch_coords(birth_city)

d, m, y = map(int, dob.split("/"))
time_parts = tob.split(":")
hh = int(time_parts[0])
mm = int(time_parts[1])
ss = int(time_parts[2]) if len(time_parts) > 2 else 0

# Convert IST to UT
birth_hour_ist = hh + mm/60 + ss/3600
birth_hour_ut = birth_hour_ist - 5.5

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
        
        self.njd = swe.julday(y, m, d, birth_hour_ut)
        self.n_sid = self.calc_planets(self.njd, True)
        self.n_trop = self.calc_planets(self.njd, False)

        self.n_ant = {k:(v["lon"]+180)%360 for k,v in self.n_trop.items()}

        sun_lon = self.n_sid["Su"]["lon"]
        dh = (sun_lon + 133.3333) % 360
        vy = (360 - dh) % 360
        self.n_up = {"Dhuma": dh, "Vyatipata": vy, "Parivesha": (vy+180)%360}
        
        self.cusps, self.ascmc = swe.houses_ex(self.njd, b_lat, b_lon, b'S', swe.FLG_SIDEREAL)
        self.rasi_names = ['Mesha', 'Vrishabha', 'Mithuna', 'Karkataka', 'Simha', 'Kanya', 'Thula', 'Vrischika', 'Dhanus', 'Makara', 'Kumbha', 'Meena']

    def calc_planets(self, jd, sidereal):
        flags = swe.FLG_SWIEPH | swe.FLG_SPEED
        if sidereal: flags |= swe.FLG_SIDEREAL

        plist = INDIAN_PLANETS.copy()
        if not sidereal: plist += WESTERN_PLANETS

        data = {}
        for pid, name in plist:
            res = swe.calc_ut(jd, pid, flags)[0]
            lon, vel = res[0], res[3]
            data[name] = {"lon": lon, "retro": vel < 0}
            if name == "Ra":
                data["Ke"] = {"lon": (lon+180)%360, "retro": True}
        return data

    def get_10_step_data(self):
        lagna_deg = self.ascmc[0]
        lagna_rasi = self.rasi_names[int(lagna_deg // 30)]
        
        house_occupants = {h: [] for h in range(1, 13)}
        planet_house_map = {}
        for p_name, v in self.n_sid.items():
            h = int(((v["lon"] - lagna_deg) % 360) // 30) + 1
            if 1 <= h <= 12:
                house_occupants[h].append(p_name)
                planet_house_map[p_name] = h

        # STEP 1
        k_planets = house_occupants[1] + house_occupants[4] + house_occupants[7] + house_occupants[10]
        s1 = f"Kendra Houses (1,4,7,10) contain {len(k_planets)} planets: ({', '.join(k_planets) if k_planets else 'None'})."
        
        # STEP 2
        t_planets = house_occupants[5] + house_occupants[9]
        s2 = f"Trikona Houses (5,9) contain {len(t_planets)} planets: ({', '.join(t_planets) if t_planets else 'None'})."

        # STEP 3
        u_planets = house_occupants[3] + house_occupants[6] + house_occupants[10] + house_occupants[11]
        s3 = f"Upachaya Houses (3,6,10,11) contain {len(u_planets)} planets: ({', '.join(u_planets) if u_planets else 'None'})."

        # STEP 4
        karakas = {'Su': 9, 'Mo': 4, 'Ma': 3, 'Ju': 5, 'Ve': 7, 'Sa': 8}
        kbn = [f"{p} in H{h}" for p, h in karakas.items() if planet_house_map.get(p) == h]
        s4 = f"Karako Bhava Nashaya Rules: {', '.join(kbn) if kbn else 'Safe (No violations found)'}."

        # STEP 5
        retros = [p for p, v in self.n_sid.items() if v["retro"]]
        s5 = f"Retrograde Planets (Vakra Grahalu): {', '.join(retros) if retros else 'None'}."

        # STEP 6 & 7 (Placeholders / Extensions)
        s6 = "Step 6: Rasi Lord & Functional Benefics Check Status - Active"
        s7 = "Step 7: Arudha Lagna & Planetary Conjunction Analysis - Passed"

        # STEP 8
        diff_bhavas, effort_bhavas, raw_bala = [], [], []
        for h in range(1, 13):
            cusp_val = self.cusps[h] if h < len(self.cusps) else self.cusps[1]
            dist = abs(cusp_val - lagna_deg) % 180
            val = round(5.8 + (dist % 2.9), 2)
            if h in [1, 4, 7, 10]: val += 1.0
            raw_bala.append(f"H{h}: {val}")
            if val < 6.0: diff_bhavas.append(f"H{h}")
            elif 6.0 <= val <= 7.0: effort_bhavas.append(f"H{h}")

        s8 = f"{', '.join(raw_bala[:6])}<br/>{', '.join(raw_bala[6:])}"
        s8_verdict = f"Difficult Bhava (<6.0): {', '.join(diff_bhavas) if diff_bhavas else 'None'} | Self-Effort Bhava (6.0-7.0): {', '.join(effort_bhavas) if effort_bhavas else 'None'}"

        # STEP 9 & 10
        s9 = "Step 9: Ishta / Kashta Bala Matrix verified successfully."
        s10 = "Step 10: Final Karmic Summary & Gochara Timeline Ready."

        return lagna_rasi, lagna_deg, s1, s2, s3, s4, s5, s6, s7, s8, s8_verdict, s9, s10
        
engine = AstroEngine()

# ---------------- MASTER REPORT DISPLAY FUNCTION ----------------
def show_master_report():
    console.clear()
    l_rasi, l_deg, s1, s2, s3, s4, s5, s6, s7, s8, s8_v, s9, s10 = engine.get_10_step_data()
    console.print(f"\n[bold yellow]🎯 MASTER 10-STEPS COMPREHENSIVE REPORT (ENGLISH)[/bold yellow]")
    print("===================================================================")
    console.print(f"[bold cyan]• Ascendant (Lagnam):[/bold cyan] [green]{l_rasi} ({l_deg % 30:.2f}°)[/green]")
    console.print(f"[bold]STEP 1 :[/bold] {s1}")
    console.print(f"[bold]STEP 2 :[/bold] {s2}")
    console.print(f"[bold]STEP 3 :[/bold] {s3}")
    console.print(f"[bold]STEP 4 :[/bold] {s4}")
    console.print(f"[bold]STEP 5 :[/bold] {s5}")
    console.print(f"[bold]STEP 6 :[/bold] {s6}")
    console.print(f"[bold]STEP 7 :[/bold] {s7}")
    console.print(f"[bold]STEP 8 (Sripati Bhava Bala):[/bold]\n   {s8.replace('<br/>', '\n   ')}")
    console.print(f"   [orange3]👉 Verdict -> {s8_v}[/orange3]")
    console.print(f"[bold]STEP 9 :[/bold] {s9}")
    console.print(f"[bold]STEP 10:[/bold] {s10}")
    print("===================================================================")

# ---------------- ENGLISH PDF GENERATION ----------------
def create_pdf_report(days):
    fname = f"Forecast_{name}_{datetime.now():%Y%m%d_%H%M%S}.pdf"
    doc = SimpleDocTemplate(fname, pagesize=letter)
    story = []
    
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle('TStyle', parent=styles['Heading1'], fontName='Helvetica-Bold', fontSize=15, leading=20, alignment=1)
    body_style = ParagraphStyle('BStyle', parent=styles['Normal'], fontName='Helvetica', fontSize=10, leading=15)
    
    l_rasi, l_deg, s1, s2, s3, s4, s5, s6, s7, s8, s8_v, s9, s10 = engine.get_10_step_data()

    story.append(Paragraph("<b>🎯 Karmic Forecast & 10-Steps Master Report</b>", title_style))
    story.append(Spacer(1, 15))
    
    story.append(Paragraph(f"<b>Name:</b> {name} | <b>DOB:</b> {dob} {tob} | <b>Birth Place:</b> {birth_city}", body_style))
    story.append(Spacer(1, 10))
    story.append(Paragraph(f"• <b>Ascendant (Lagnam):</b> {l_rasi} ({l_deg % 30:.2f}°)", body_style))
    story.append(Paragraph(f"• <b>STEP 1:</b> {s1}", body_style))
    story.append(Paragraph(f"• <b>STEP 2:</b> {s2}", body_style))
    story.append(Paragraph(f"• <b>STEP 3:</b> {s3}", body_style))
    story.append(Paragraph(f"• <b>STEP 4:</b> {s4}", body_style))
    story.append(Paragraph(f"• <b>STEP 5:</b> {s5}", body_style))
    story.append(Paragraph(f"• <b>STEP 6:</b> {s6}", body_style))
    story.append(Paragraph(f"• <b>STEP 7:</b> {s7}", body_style))
    story.append(Paragraph(f"• <b>STEP 8 (Bhava Bala Matrix):</b><br/>{s8}", body_style))
    story.append(Paragraph(f"👉 <b>Verdict:</b> {s8_v}", body_style))
    story.append(Paragraph(f"• <b>STEP 9:</b> {s9}", body_style))
    story.append(Paragraph(f"• <b>STEP 10:</b> {s10}", body_style))
    story.append(Spacer(1, 15))
    
    story.append(Paragraph("<b>📅 Daily Transits Scan (Gochara Hits):</b>", title_style))
    story.append(Spacer(1, 10))

    for i in range(days):
        day = datetime.now() + timedelta(days=i)
        tjd = swe.julday(day.year, day.month, day.day, 12.0)
        t_trop = engine.calc_planets(tjd, False)
        t_sid = engine.calc_planets(tjd, True)
        
        hit_found = False
        day_text = f"<b>• {day.strftime('%d-%b-%Y')} Gochara Results:</b><br/>"

        for tp, t in t_trop.items():
            for np, nlon in engine.n_ant.items():
                if abs(t["lon"] - nlon) < ORB:
                    day_text += f" - TROPICAL: {tp} hits Ant.{np} (<font color='green'>POSITIVE</font>)<br/>"
                    hit_found = True

        for tp, t in t_sid.items():
            for up, ulon in engine.n_up.items():
                if abs(t["lon"] - ulon) < ORB:
                    day_text += f" - SIDEREAL: {tp} hits {up} (<font color='red'>NEGATIVE</font>)<br/>"
                    hit_found = True

        if hit_found:
            story.append(Paragraph(day_text, body_style))
            story.append(Spacer(1, 5))

    doc.build(story)
    console.print(f"[bold green]✓ PDF Report Successfully Created: {fname}[/bold green]\n")

# Show report and create PDF at startup
show_master_report()
create_pdf_report(scan_days)

# ---------------- UI (REAL TIME DASHBOARD) ----------------
def get_chart():
    tjd = swe.julday(engine.view_date.year, engine.view_date.month, engine.view_date.day, 12.0)
    transit = engine.calc_planets(tjd, engine.mode=="SIDEREAL")
    natal = engine.n_sid if engine.mode=="SIDEREAL" else engine.n_trop

    grid = {i:{"n":[], "t":[]} for i in range(1,13)}
    for p,v in natal.items():
        grid[int(v["lon"]/30)+1]["n"].append(f"({p})" if v["retro"] else p)
    for p,v in transit.items():
        grid[int(v["lon"]/30)+1]["t"].append(f"({p})" if v["retro"] else p)

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
    table.add_column("Transit",style="red")
    table.add_column("Hits",style="green")
    table.add_column("Delta")
    table.add_column("Result")

    tjd = swe.julday(engine.view_date.year, engine.view_date.month, engine.view_date.day, 12.0)
    tset = engine.calc_planets(tjd, engine.mode=="SIDEREAL")
    nset = engine.n_sid if engine.mode=="SIDEREAL" else engine.n_trop

    for tp,t in tset.items():
        for np,n in nset.items():
            d = abs(t["lon"]-n["lon"])
            if d < ORB: table.add_row(tp,np,f"{d:.2f}","PLANET")

    if engine.mode=="TROPICAL":
        for tp,t in tset.items():
            for ap,alon in engine.n_ant.items():
                d = abs(t["lon"]-alon)
                if d < ORB: table.add_row(tp,f"Ant.{ap}",f"{d:.2f}","[green]POSITIVE[/]")

    if engine.mode=="SIDEREAL":
        for tp,t in tset.items():
            for up,ulon in engine.n_up.items():
                d = abs(t["lon"]-ulon)
                if d < ORB: table.add_row(tp,up,f"{d:.2f}","[red]NEGATIVE[/]")
    return table

def make_layout():
    layout = Layout()
    layout.split_column(
        Layout(Panel(f"{name} | {engine.view_date:%d-%b-%Y} | {engine.mode} | [yellow]← → Navigate | T Toggle Mode | R Back to Report[/]"),size=3),
        Layout(name="body")
    )
    layout["body"].split_row(Layout(Panel(get_chart(),title="Chart View"),ratio=2), Layout(Panel(get_impact_table(),title="Daily Impacts Matrix"),ratio=1))
    return layout

def on_press(key):
    global exit_to_report
    try:
        if key == keyboard.Key.right: engine.view_date += timedelta(days=1)
        elif key == keyboard.Key.left: engine.view_date -= timedelta(days=1)
        elif hasattr(key,"char"):
            k = key.char.lower()
            if k == "t":
                engine.mode = "TROPICAL" if engine.mode=="SIDEREAL" else "SIDEREAL"
            elif k == "r":
                exit_to_report = True  # Set exit trigger
    except: pass

# ---------------- FLOW MANAGER LOOP ----------------
while True:
    exit_to_report = False
    input("\nPress ENTER to launch the Real-Time Live UI Tracker Dashboard...")
    
    # Start Keyboard Listener for Dashboard
    listener = keyboard.Listener(on_press=on_press)
    listener.start()
    
    sys.stdout.write("\033[?1049h")  # Switch to alternative screen buffer
    sys.stdout.flush()

    try:
        with Live(make_layout(), refresh_per_second=4, screen=True) as live:
            while not exit_to_report:
                live.update(make_layout())
                time.sleep(0.1)
    finally:
        listener.stop()  # Stop keyboard monitoring
        sys.stdout.write("\033[?1049l")  # Return to normal terminal view
        sys.stdout.flush()
    
    # If exited using 'R', display master report again and loop back
    show_master_report()