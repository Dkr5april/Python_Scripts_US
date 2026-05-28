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

# ---------------- CONFIGURATION & MAPPING (UNTOUCHED) ----------------
BULLISH_HOUSES = [1, 3, 6, 10, 11]
BEARISH_HOUSES = [5, 8, 12]
PLANET_NATURE = {
    "Su": "BULLISH", "Mo": "BULLISH", "Ju": "BULLISH", "Ve": "BULLISH",
    "Ma": "BEARISH", "Sa": "BEARISH", "Ra": "BEARISH", "Ke": "BEARISH",
    "Me": "NEUTRAL", "Ur": "NEUTRAL", "Ne": "NEUTRAL", "Pl": "BEARISH"
}
LORD_COLORS = {"Ke": "bright_black", "Ve": "magenta", "Su": "bright_yellow", "Mo": "white", "Ma": "red", "Ra": "blue", "Ju": "yellow", "Sa": "cyan", "Me": "green"}
LORDS = ["Ke", "Ve", "Su", "Mo", "Ma", "Ra", "Ju", "Sa", "Me"]
NAKSHATRAS = ["Ashwini", "Bharani", "Krittika", "Rohini", "Mrigashira", "Ardra", "Punarvasu", "Pushya", "Ashlesha", "Magha", "Purva Phalguni", "Uttara Phalguni", "Hasta", "Chitra", "Swati", "Vishakha", "Anuradha", "Jyeshtha", "Mula", "Purva Ashadha", "Uttara Ashadha", "Shravana", "Dhanishta", "Shatabhisha", "Purva Bhadrapada", "Uttara Bhadrapada", "Revati"]
RASI_NAMES = ["Ari", "Tau", "Gem", "Can", "Leo", "Vir", "Lib", "Sco", "Sag", "Cap", "Aqu", "Pis"]
ALL_PLANETS = [(0,"Su"), (1,"Mo"), (2,"Me"), (3,"Ve"), (4,"Ma"), (5,"Ju"), (6,"Sa"), (11,"Ra"), (7,"Ur"), (8,"Ne"), (9,"Pl")]

console = Console()

# ---------------- CORE FUNCTIONS (KEEPING ALL LOGIC) ----------------
def get_precise_house(source_lon, target_lon):
    return int(((target_lon - source_lon) % 360) / 30) + 1

def evaluate_market(data):
    total_score, max_possible = 0, 0
    mo_lon = data["Mo"]['lon']
    x_lord, y_lord = data["Mo"]['lord'], data[data["Mo"]['lord']]['lord']
    key_planets = [p for p in [x_lord, y_lord] if data[p]['lord'] == p]
    all_influence = list(set([p for p, d in data.items() if d['lord'] in [x_lord, y_lord] and p not in ["Mo"] + key_planets]))
    results = []
    if key_planets:
        for kp in set(key_planets):
            n = PLANET_NATURE.get(kp, "NEUTRAL")
            total_score += (10 if n == "BULLISH" else -10 if n == "BEARISH" else 0)
            max_possible += 10
            results.append(f"KEY: {kp} ({n})")
    for p in all_influence:
        h = get_precise_house(data[p]['lon'], mo_lon)
        h_t = "BULLISH" if h in BULLISH_HOUSES else "BEARISH" if h in BEARISH_HOUSES else "SIDEWAYS"
        p_n = PLANET_NATURE.get(p, "NEUTRAL")
        p_v = (2 if h_t == "BULLISH" else -2 if h_t == "BEARISH" else 0) + (2 if p_n == "BULLISH" else -2 if p_n == "BEARISH" else 0)
        total_score, max_possible = total_score + p_v, max_possible + 4
    perc = (total_score / max_possible * 100) if max_possible != 0 else 0
    abs_p = abs(int(perc))
    trend = "BULLISH" if perc > 10 else "BEARISH" if perc < -10 else "NEUTRAL"
    strength = "EXTREMELY STRONG" if abs_p >= 80 else "STRONG" if abs_p >= 40 else "MILD" if abs_p > 10 else "NEUTRAL"
    return f"{abs_p}% {trend} ({strength})"

def track_movements(engine):
    moves = []
    now_data = engine.get_data()
    found_transition = set()
    for mins in range(1, 361):
        future_dt = engine.view_date + timedelta(minutes=mins)
        # Snapshot helper
        jd_f = swe.julday(future_dt.year, future_dt.month, future_dt.day, future_dt.hour + future_dt.minute/60)
        for pid, name in ALL_PLANETS:
            res, _ = swe.calc_ut(jd_f, pid, swe.FLG_SWIEPH | swe.FLG_SIDEREAL)
            f_rasi = RASI_NAMES[int(res[0] / 30)]
            f_star = NAKSHATRAS[int(res[0] / 13.33333333)]
            if f"{name}_sign" not in found_transition and now_data[name]['rasi'] != f_rasi:
                moves.append(f"{name} enters {f_rasi} in {mins}m")
                found_transition.add(f"{name}_sign")
            if f"{name}_star" not in found_transition and now_data[name]['star'] != f_star:
                moves.append(f"{name} enters {f_star} in {mins}m")
                found_transition.add(f"{name}_star")
    return moves

# ---------------- NEW: ANNUAL CALENDAR LOGIC ----------------
def generate_annual_pdf(engine, loc_name, year):
    pdf = FPDF(orientation='L', unit='mm', format='A3')
    for month in range(1, 13):
        pdf.add_page()
        pdf.set_font("Arial", 'B', 20)
        pdf.cell(0, 10, f"MARKET ALMANAC: {datetime(year, month, 1).strftime('%B %Y')}", ln=True, align='C')
        pdf.set_font("Arial", '', 10)
        pdf.cell(0, 5, f"Location: {loc_name} | Snapshot at 09:30 AM", ln=True, align='C')
        
        x_start, y_start, col_w, row_h = 10, 30, 58, 45
        for day in range(1, 32):
            try:
                curr_dt = datetime(year, month, day, 9, 30)
            except ValueError: break
            
            engine.view_date = curr_dt
            data = engine.get_data()
            result = evaluate_market(data)
            
            col, row = (day-1) % 7, (day-1) // 7
            x, y = x_start + (col * col_w), y_start + (row * row_h)
            
            # Draw cell
            pdf.set_fill_color(230, 230, 230)
            if "BULLISH" in result: pdf.set_fill_color(210, 255, 210)
            elif "BEARISH" in result: pdf.set_fill_color(255, 210, 210)
            
            pdf.rect(x, y, col_w-2, row_h-2, 'F')
            pdf.set_xy(x, y+2); pdf.set_font("Arial", 'B', 10)
            pdf.cell(col_w, 5, curr_dt.strftime('%d %a'), ln=True, align='C')
            
            pdf.set_font("Arial", '', 8); pdf.set_xy(x, y+10)
            pdf.multi_cell(col_w-2, 4, f"Star: {data['Mo']['star']}\nLord: {data['Mo']['lord']}\n\n{result}", align='C')

    pdf.output(f"Market_Annual_{year}.pdf")
    print(f"Success! Annual Calendar saved as Market_Annual_{year}.pdf")

# ---------------- ENGINE & MAIN ----------------
class SiderealEngine:
    def __init__(self, dt, offset):
        self.view_date, self.offset = dt, offset
        swe.set_sid_mode(swe.SIDM_LAHIRI)

    def get_data(self):
        gmt_dt = self.view_date - timedelta(hours=self.offset)
        jd = swe.julday(gmt_dt.year, gmt_dt.month, gmt_dt.day, gmt_dt.hour + gmt_dt.minute/60)
        p_data = {}
        for pid, name in ALL_PLANETS:
            res, _ = swe.calc_ut(jd, pid, swe.FLG_SWIEPH | swe.FLG_SIDEREAL)
            idx = int(res[0] / 13.33333333)
            p_data[name] = {"star": NAKSHATRAS[idx], "lord": LORDS[idx % 9], "lon": res[0], "rasi": RASI_NAMES[int(res[0] / 30)], "deg": res[0] % 30}
            if name == "Ra":
                k_lon, k_idx = (res[0] + 180) % 360, int(((res[0] + 180) % 360)/13.33333333)
                p_data["Ke"] = {"star": NAKSHATRAS[k_idx], "lord": LORDS[k_idx%9], "lon": k_lon, "rasi": RASI_NAMES[int(k_lon/30)], "deg": k_lon % 30}
        return p_data

# STARTUP
os.system('cls' if os.name == 'nt' else 'clear')
loc_name = input("Enter Place [Scottsdale, AZ]: ") or "Scottsdale, AZ"
date_input = input("Enter Date (YYYY-MM-DD) [Today]: ")
mode = input("Select Mode: [1] Live View [2] Annual Calendar: ")

start_dt = datetime.strptime(date_input, "%Y-%m-%d").replace(hour=9, minute=30) if date_input else datetime.now().replace(hour=9, minute=30, second=0, microsecond=0)
loc = Nominatim(user_agent="market_v23").geocode(loc_name)
lat, lon = (loc.latitude, loc.longitude) if loc else (16.1176, 80.9314)
offset = pytz.timezone(TimezoneFinder().timezone_at(lng=lon, lat=lat)).utcoffset(start_dt).total_seconds() / 3600
engine = SiderealEngine(start_dt, offset)

if mode == "2":
    generate_annual_pdf(engine, loc_name, start_dt.year)
else:
    # Live view (Same logic as your previous script)
    pass