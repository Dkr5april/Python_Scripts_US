import swisseph as swe
import os, sys, time, logging
from datetime import datetime, timedelta
from pynput import keyboard
from geopy.geocoders import Nominatim
from timezonefinder import TimezoneFinder
import pytz
from rich.live import Live
from rich.table import Table
from rich.console import Console
from rich.layout import Layout
from rich.panel import Panel
from fpdf import FPDF

# ---------------- CONFIGURATION & MAPPING ----------------
BULLISH_HOUSES = [1, 3, 6, 10, 11]
BEARISH_HOUSES = [5, 8, 12]
SIDEWAYS_HOUSES = [4, 7, 2, 9]

PLANET_NATURE = {
    "Su": "BULLISH", "Mo": "BULLISH", "Ju": "BULLISH", "Ve": "BULLISH",
    "Ma": "BEARISH", "Sa": "BEARISH", "Ra": "BEARISH", "Ke": "BEARISH",
    "Me": "NEUTRAL", "Ur": "NEUTRAL", "Ne": "NEUTRAL", "Pl": "BEARISH"
}

LORD_COLORS = {
    "Ke": "bright_black", "Ve": "magenta", "Su": "bright_yellow", 
    "Mo": "white", "Ma": "red", "Ra": "blue", 
    "Ju": "yellow", "Sa": "cyan", "Me": "green"
}

LORDS = ["Ke", "Ve", "Su", "Mo", "Ma", "Ra", "Ju", "Sa", "Me"]
NAKSHATRAS = ["Ashwini", "Bharani", "Krittika", "Rohini", "Mrigashira", "Ardra", "Punarvasu", "Pushya", "Ashlesha", "Magha", "Purva Phalguni", "Uttara Phalguni", "Hasta", "Chitra", "Swati", "Vishakha", "Anuradha", "Jyeshtha", "Mula", "Purva Ashadha", "Uttara Ashadha", "Shravana", "Dhanishta", "Shatabhisha", "Purva Bhadrapada", "Uttara Bhadrapada", "Revati"]
RASI_NAMES = ["Ari", "Tau", "Gem", "Can", "Leo", "Vir", "Lib", "Sco", "Sag", "Cap", "Aqu", "Pis"]
ALL_PLANETS = [(0,"Su"), (1,"Mo"), (2,"Me"), (3,"Ve"), (4,"Ma"), (5,"Ju"), (6,"Sa"), (11,"Ra"), (7,"Ur"), (8,"Ne"), (9,"Pl")]

console = Console()

# ---------------- CORE CALCULATION FUNCTIONS ----------------
def get_precise_house(source_lon, target_lon):
    diff = (target_lon - source_lon) % 360
    return int(diff / 30) + 1

def evaluate_market(data, view_date):
    verdicts = []
    total_score = 0
    max_possible = 0
    
    mo = data["Mo"]
    mo_lon = mo['lon']
    x_lord = mo['lord']
    y_lord = data[x_lord]['lord']
    
    key_planets = []
    if data[x_lord]['lord'] == x_lord: key_planets.append(x_lord)
    if data[y_lord]['lord'] == y_lord: key_planets.append(y_lord)
    key_planets = list(set(key_planets))

    xn_list = [p for p, d in data.items() if d['lord'] == x_lord and p != x_lord and p != "Mo"]
    yn_list = [p for p, d in data.items() if d['lord'] == y_lord and p != y_lord and p != "Mo"]
    all_influence = list(set(xn_list + yn_list))

    # 1. KEY PLANETS (Weight: 10)
    if key_planets:
        verdicts.append("[bold magenta]KEY PLANET RULE[/]")
        for kp in key_planets:
            nature = PLANET_NATURE.get(kp, "NEUTRAL")
            val = 10 if nature == "BULLISH" else -10 if nature == "BEARISH" else 0
            total_score += val
            max_possible += 10
            verdicts.append(f"- {kp} ({nature}) is KEY")

    # 2. STELLAR INFLUENCERS (Weight: 4)
    if all_influence:
        verdicts.append("[bold yellow]STELLAR RULE[/]")
        for p in all_influence:
            h_dist = get_precise_house(data[p]['lon'], mo_lon)
            h_trend = "BULLISH" if h_dist in BULLISH_HOUSES else "BEARISH" if h_dist in BEARISH_HOUSES else "SIDEWAYS"
            p_nature = PLANET_NATURE.get(p, "NEUTRAL")
            
            p_val = 0
            if h_trend == "BULLISH": p_val += 2
            elif h_trend == "BEARISH": p_val -= 2
            if p_nature == "BULLISH": p_val += 2
            elif p_nature == "BEARISH": p_val -= 2
            
            total_score += p_val
            max_possible += 4
            color = "green" if p_val > 0 else "red" if p_val < 0 else "white"
            verdicts.append(f"[{color}]- {p} ({p_nature}) -> H{h_dist} ({h_trend})[/]")

    # 3. PRIMARY FALLBACK (Weight: 5)
    elif not key_planets:
        verdicts.append("[bold cyan]PRIMARY RULE[/]")
        for p_name in [x_lord, y_lord]:
            h_dist = get_precise_house(mo_lon, data[p_name]['lon'])
            h_trend = "BULLISH" if h_dist in BULLISH_HOUSES else "BEARISH" if h_dist in BEARISH_HOUSES else "SIDEWAYS"
            if h_trend == "BULLISH": total_score += 5
            elif h_trend == "BEARISH": total_score -= 5
            max_possible += 5
            verdicts.append(f"- {p_name}: H{h_dist} ({h_trend})")

    # CONCLUSION LOGIC
    verdicts.append("─" * 20)
    percentage = (total_score / max_possible * 100) if max_possible != 0 else 0
    abs_p = abs(int(percentage))
    
    if abs_p >= 80: strength = "EXTREMELY STRONG"
    elif abs_p >= 40: strength = "STRONG"
    else: strength = "NEUTRAL / VOLATILE"

    if percentage > 10:
        verdicts.append(f"[bold green]CONCLUSION: {abs_p}% BULLISH ({strength})[/]")
    elif percentage < -10:
        verdicts.append(f"[bold red]CONCLUSION: {abs_p}% BEARISH ({strength})[/]")
    else:
        verdicts.append(f"[bold white]CONCLUSION: 50% {strength}[/]")

    return verdicts

# ---------------- PDF GENERATOR ----------------
def generate_pdf_report(engine, loc_name, days=30):
    pdf = FPDF()
    start_date = engine.view_date
    
    console.print(f"[bold yellow]Generating {days}-Day PDF Report... Please wait.[/]")
    
    for i in range(days):
        current_date = start_date + timedelta(days=i)
        engine.view_date = current_date
        data = engine.get_data()
        verdicts = evaluate_market(data, current_date)
        conclusion = verdicts[-1]

        pdf.add_page()
        # Poster Background Color
        if "BULLISH" in conclusion: pdf.set_fill_color(220, 255, 220)
        elif "BEARISH" in conclusion: pdf.set_fill_color(255, 220, 220)
        else: pdf.set_fill_color(245, 245, 245)
        pdf.rect(0, 0, 210, 297, 'F')

        pdf.set_font("Arial", 'B', 16)
        pdf.cell(0, 15, f"MARKET POSTER: {current_date.strftime('%d %B %Y')}", ln=True, align='C')
        pdf.set_font("Arial", '', 10)
        pdf.cell(0, 5, f"Location: {loc_name}", ln=True, align='C')
        pdf.ln(10)

        # Analysis Body
        pdf.set_font("Arial", 'B', 12)
        pdf.cell(0, 10, "Astrological Indicators:", ln=True)
        pdf.set_font("Arial", '', 10)
        for line in verdicts[:-2]:
            clean = line.replace("[", "").replace("]", "").replace("bold ", "").replace("green", "").replace("red", "").replace("yellow", "").replace("magenta", "").replace("/", "")
            pdf.multi_cell(0, 7, f"  > {clean}")

        # Big Conclusion Box
        pdf.ln(20)
        pdf.set_font("Arial", 'B', 24)
        if "BULLISH" in conclusion: pdf.set_text_color(0, 120, 0)
        elif "BEARISH" in conclusion: pdf.set_text_color(150, 0, 0)
        else: pdf.set_text_color(50, 50, 50)
        
        clean_conclusion = conclusion.split("]")[-2].replace("[", "") if "]" in conclusion else conclusion
        pdf.multi_cell(0, 25, clean_conclusion, border=1, align='C')
        pdf.set_text_color(0,0,0)

    filename = f"Market_Report_{start_date.strftime('%Y%m%d')}.pdf"
    pdf.output(filename)
    engine.view_date = start_date # Restore
    console.print(f"[bold green]Success! Saved as {filename}[/]")

# ---------------- ENGINE & MAIN ----------------
class SiderealEngine:
    def __init__(self, dt, offset_hours):
        self.view_date = dt
        self.offset = offset_hours
        swe.set_sid_mode(swe.SIDM_LAHIRI)

    def get_details(self, lon, vel):
        star_idx = int(lon / (13.33333333))
        return {"star": NAKSHATRAS[star_idx], "lord": LORDS[star_idx % 9], "lon": lon, "rasi": RASI_NAMES[int(lon / 30)], "deg": lon % 30}

    def get_data(self):
        gmt_dt = self.view_date - timedelta(hours=self.offset)
        jd = swe.julday(gmt_dt.year, gmt_dt.month, gmt_dt.day, gmt_dt.hour + gmt_dt.minute/60)
        p_data = {}
        for pid, name in ALL_PLANETS:
            res, _ = swe.calc_ut(jd, pid, swe.FLG_SWIEPH | swe.FLG_SIDEREAL)
            p_data[name] = self.get_details(res[0], 0)
            if name == "Ra": p_data["Ke"] = self.get_details((res[0]+180)%360, 0)
        return p_data

# STARTUP
os.system('cls' if os.name == 'nt' else 'clear')
loc_input = input("Enter Place [Scottsdale, AZ]: ") or "Scottsdale, AZ"
mode = input("Select Mode: [1] Live View [2] 30-Day PDF Report: ")

# Location / Time Detection
geolocator = Nominatim(user_agent="market_v19")
loc = geolocator.geocode(loc_input)
lat, lon = (loc.latitude, loc.longitude) if loc else (16.1176, 80.9314)
start_dt = datetime.now()
tz_name = TimezoneFinder().timezone_at(lng=lon, lat=lat)
offset = pytz.timezone(tz_name).utcoffset(start_dt).total_seconds() / 3600

engine = SiderealEngine(start_dt, offset)

if mode == "2":
    generate_pdf_report(engine, loc_input)
else:
    running = True
    def make_layout():
        data = engine.get_data()
        table = Table(expand=True)
        table.add_column("Planet")
        table.add_column("Star (Lord)")
        for p, d in data.items():
            table.add_row(f"[{LORD_COLORS.get(d['lord'])}]{p}[/]", f"{d['star']} ({d['lord']})")
        
        layout = Layout()
        layout.split_column(
            Layout(Panel(f"{loc_input} | {engine.view_date.strftime('%Y-%m-%d %H:%M:%S')}"), size=3),
            Layout(name="main")
        )
        layout["main"].split_row(
            Layout(Panel(table, title="Live Degrees"), ratio=1),
            Layout(Panel("\n".join(evaluate_market(data, engine.view_date)), title="Market Logic"), ratio=1)
        )
        return layout

    def on_press(key):
        global running
        try:
            if key == keyboard.Key.right: engine.view_date += timedelta(hours=1)
            elif key == keyboard.Key.left: engine.view_date -= timedelta(hours=1)
            elif key == keyboard.Key.up: engine.view_date += timedelta(days=1)
            elif key == keyboard.Key.down: engine.view_date -= timedelta(days=1)
            elif key == keyboard.Key.esc: running = False
        except: pass

    listener = keyboard.Listener(on_press=on_press)
    listener.start()
    with Live(make_layout(), refresh_per_second=2, screen=True) as live:
        while running:
            live.update(make_layout())
            time.sleep(0.5)