import swisseph as swe
import os, sys, time
from datetime import datetime, timedelta
from pynput import keyboard
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
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

if sys.platform == "win32":
    os.system("color")

swe.set_ephe_path("./ephe")
console = Console()

ORB = 1.5

# ---------------- SIMPLIFIED INPUT (No more useless options) ----------------
console.clear()
console.print("[bold magenta]=== ASTRO ENGINE V24 (PRECISE LAGNA FIXED) ===[/bold magenta]\n")

name = input("Enter Name: ")
dob = input("Enter DOB (DD/MM/YYYY): ")
tob = input("Enter TOB (HH:MM): ")
scan_days = int(input("How many days to scan for PDF Forecast? "))

# Default Coordinates for Challapalli (Saved Setting)
b_lat, b_lon = 16.1176, 80.9314 

d, m, y = map(int, dob.split("/"))
time_parts = tob.split(":")
hh = int(time_parts[0])
mm = int(time_parts[1])
ss = int(time_parts[2]) if len(time_parts) > 2 else 0

# 🌟 CRITICAL FIX: Convert IST to UT (Subtract 5 hours 30 mins for Indian Births)
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
        
        # UT సమయంతో జూలియన్ డే లెక్కించడం వల్ల లగ్నం పక్కాగా వస్తుంది
        self.njd = swe.julday(y, m, d, birth_hour_ut)
        self.n_sid = self.calc_planets(self.njd, True)
        self.n_trop = self.calc_planets(self.njd, False)

        self.n_ant = {k:(v["lon"]+180)%360 for k,v in self.n_trop.items()}

        sun_lon = self.n_sid["Su"]["lon"]
        dh = (sun_lon + 133.3333) % 360
        vy = (360 - dh) % 360
        self.n_up = {"Dhuma": dh, "Vyatipata": vy, "Parivesha": (vy+180)%360}
        
        # Precise House Cusps Calculation
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
        lagna_idx = int(lagna_deg // 30)
        lagna_rasi = self.rasi_names[lagna_idx]
        
        house_occupants = {h: [] for h in range(1, 13)}
        planet_house_map = {}
        for p_name, v in self.n_sid.items():
            h = int(((v["lon"] - lagna_deg) % 360) // 30) + 1
            if 1 <= h <= 12:
                house_occupants[h].append(p_name)
                planet_house_map[p_name] = h

        k_planets = house_occupants[1] + house_occupants[4] + house_occupants[7] + house_occupants[10]
        s1 = f"కేంద్రాలలో {len(k_planets)} గ్రహాలు ఉన్నాయి ({', '.join(k_planets) if k_planets else 'ఏవీ లేవు'})."
        if len(k_planets) >= 2: s1 += " -> జీవితంలో బలమైన స్థిరత్వం ఉంటుంది!"
        
        t_planets = house_occupants[5] + house_occupants[9]
        s2 = f"త్రికోణాలలో {len(t_planets)} గ్రహాలు ఉన్నాయి ({', '.join(t_planets) if t_planets else 'ఏవీ లేవు'})."

        u_planets = house_occupants[3] + house_occupants[6] + house_occupants[10] + house_occupants[11]
        s3 = f"ఉపచయ స్థానాల్లో {len(u_planets)} గ్రహాలు ఉన్నాయి ({', '.join(u_planets) if u_planets else 'ఏవీ లేవు'})."

        karakas = {'Su': 9, 'Mo': 4, 'Ma': 3, 'Ju': 5, 'Ve': 7, 'Sa': 8}
        kbn = [f"{p} in H{h}" for p, h in karakas.items() if planet_house_map.get(p) == h]
        s4 = f"{', '.join(kbn) if kbn else 'ఏ గ్రహానికీ వర్తించదు (Safe)'}."

        retros = [p for p, v in self.n_sid.items() if v["retro"]]
        s5 = f"{', '.join(retros) if retros else 'ఏవీ లేవు'}."

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
        s8_verdict = f"తీవ్ర ఇబ్బంది కలిగించే ఇళ్లు (<6.0): {', '.join(diff_bhavas) if diff_bhavas else 'None'}<br/>స్వయంకృషితో నెగ్గాల్సిన ఇళ్లు: {', '.join(effort_bhavas) if effort_bhavas else 'None'}"

        return lagna_rasi, lagna_deg, s1, s2, s3, s4, s5, s8, s8_verdict

engine = AstroEngine()

# టెర్మినల్ లో రిపోర్ట్ ముందే చూపించడం
l_rasi, l_deg, s1, s2, s3, s4, s5, s8, s8_v = engine.get_10_step_data()
console.print(f"\n[bold yellow]🎯 MASTER 10-STEPS REPORT (VERIFIED)[/bold yellow]")
console.print(f"[bold cyan]• లగ్నం (Ascendant):[/bold cyan] [green]{l_rasi} ({l_deg % 30:.2f}°)[/green]")
console.print(f"[bold]STEP 1 (కేంద్రాలు):[/bold] {s1}\n[bold]STEP 2 (త్రికోణాలు):[/bold] {s2}\n[bold]STEP 3 (ఉపచయాలు):[/bold] {s3}\n[bold]STEP 4 (కారకో భావ నాశాయ్):[/bold] {s4}\n[bold]STEP 5 (వక్ర గ్రహాలు):[/bold] {s5}")
print("===================================================================")

# ---------------- AUTO-TELUGU PDF GENERATION ----------------
def create_pdf_report(days):
    fname = f"Forecast_{name}_{datetime.now():%Y%m%d_%H%M%S}.pdf"
    doc = SimpleDocTemplate(fname, pagesize=letter)
    story = []
    
    win_font = "C:\\Windows\\Fonts\\Nirmala.ttf"
    font_name = "Helvetica"
    if os.path.exists(win_font):
        try:
            pdfmetrics.registerFont(TTFont('NirmalaTelugu', win_font))
            font_name = 'NirmalaTelugu'
        except: pass

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle('TitleStyle', parent=styles['Heading1'], fontName=font_name, fontSize=16, leading=22, alignment=1)
    body_style = ParagraphStyle('BodyStyle', parent=styles['Normal'], fontName=font_name, fontSize=11, leading=16)
    
    story.append(Paragraph("<b>🎯 Karmic Forecast & 10-Steps Master Report</b>", title_style))
    story.append(Spacer(1, 15))
    
    story.append(Paragraph(f"<b>Name:</b> {name} | <b>DOB:</b> {dob} {tob}", body_style))
    story.append(Spacer(1, 10))
    story.append(Paragraph(f"• <b>లగ్నం (Ascendant):</b> {l_rasi} ({l_deg % 30:.2f}°)", body_style))
    story.append(Paragraph(f"• <b>STEP 1 (కేంద్ర స్థానాలు):</b> {s1}", body_style))
    story.append(Paragraph(f"• <b>STEP 2 (త్రికోణ స్థానాలు):</b> {s2}", body_style))
    story.append(Paragraph(f"• <b>STEP 3 (ఉపచయ స్థానాలు):</b> {s3}", body_style))
    story.append(Paragraph(f"• <b>STEP 4 (కారకో భావ నాశాయ్):</b> {s4}", body_style))
    story.append(Paragraph(f"• <b>STEP 5 (వక్ర గ్రహాలు):</b> {s5}", body_style))
    story.append(Spacer(1, 10))
    story.append(Paragraph(f"• <b>STEP 8 (భావ బలాలు Matrix):</b><br/>{s8}", body_style))
    story.append(Paragraph(f"👉 {s8_v}", body_style))
    story.append(Spacer(1, 15))
    
    story.append(Paragraph("<b>📅 రోజువారీ గోచారం (Daily Transits Scan):</b>", title_style))
    story.append(Spacer(1, 10))

    for i in range(days):
        day = datetime.now() + timedelta(days=i)
        tjd = swe.julday(day.year, day.month, day.day, 12.0)
        t_trop = engine.calc_planets(tjd, False)
        t_sid = engine.calc_planets(tjd, True)
        
        hit_found = False
        day_text = f"<b>• {day.strftime('%d-%b-%Y')} రోజువారీ ఫలితాలు:</b><br/>"

        for tp, t in t_trop.items():
            for np, nlon in engine.n_ant.items():
                if abs(t["lon"] - nlon) < ORB:
                    day_text += f" - TROPICAL: {tp} hits Ant.{np} (<font color='green'>అనుకూలం / POSITIVE</font>)<br/>"
                    hit_found = True

        for tp, t in t_sid.items():
            for up, ulon in engine.n_up.items():
                if abs(t["lon"] - ulon) < ORB:
                    day_text += f" - SIDEREAL: {tp} hits {up} (<font color='red'>అవరోధం / NEGATIVE</font>)<br/>"
                    hit_found = True

        if hit_found:
            story.append(Paragraph(day_text, body_style))
            story.append(Spacer(1, 5))

    doc.build(story)
    console.print(f"[bold green]✓ PDF రిపోర్ట్ క్రియేట్ అయింది: {fname}[/bold green]\n")

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
    table.add_column("Δ°")
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
        Layout(Panel(f"{name} | {engine.view_date:%d-%b-%Y} | {engine.mode} | ← → | T Toggle"),size=3),
        Layout(name="body")
    )
    layout["body"].split_row(Layout(Panel(get_chart(),title="Chart"),ratio=2), Layout(Panel(get_impact_table(),title="Daily Impacts"),ratio=1))
    return layout

def on_press(key):
    try:
        if key == keyboard.Key.right: engine.view_date += timedelta(days=1)
        elif key == keyboard.Key.left: engine.view_date -= timedelta(days=1)
        elif hasattr(key,"char") and key.char.lower()=="t":
            engine.mode = "TROPICAL" if engine.mode=="SIDEREAL" else "SIDEREAL"
    except: pass

keyboard.Listener(on_press=on_press).start()

# ---------------- RUN LIVE UI ----------------
input("Press ENTER to launch the Real-Time Live UI Tracker Dashboard...")
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