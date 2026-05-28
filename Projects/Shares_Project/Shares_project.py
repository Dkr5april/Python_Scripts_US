import swisseph as swe
import datetime
import pandas as pd
import matplotlib.pyplot as plt
from fpdf import FPDF
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.layout import Layout
from rich.columns import Columns
from rich import box

# --- GLOBAL CONFIGURATION & MAPPING ---
# Standard KP and Market Constants[cite: 1, 9]
PLANET_LIT = ["Ke", "Ve", "Su", "Mo", "Ma", "Ra", "Ju", "Sa", "Me", "Ur", "Ne", "Pl"]
RASHI_NAMES = ["Ar", "Ta", "Ge", "Cn", "Le", "Vi", "Li", "Sc", "Sg", "Cp", "Aq", "Pi"]
DASHA_ORDER = ["Ke", "Ve", "Su", "Mo", "Ma", "Ra", "Ju", "Sa", "Me"]
PLANET_MAP = {0: "Su", 1: "Mo", 2: "Ma", 3: "Me", 4: "Ju", 5: "Ve", 6: "Sa", 10: "Ra", 11: "Ke"}

class MasterStandaloneEngine:
    def __init__(self, lat=None, lon=None, tz_offset=5.5):
        """
        Initializes with your specific default location logic.
        If no lat/lon is provided at runtime, it uses 16.1176 / 80.9314.
        """
        self.lat = lat if lat is not None else 16.1176
        self.lon = lon if lon is not None else 80.9314
        self.tz_offset = tz_offset
        
        # Initialize Ephemeris
        # Note: Ensure the 'ephe' folder containing .se1 files is in the same directory
        swe.set_ephe_path('./ephe') 
        
        # Market Rules Constants[cite: 1]
        self.BULL_PLANETS = ["Ju", "Ra"]
        self.BEAR_PLANETS = ["Ma", "Sa"]
        self.OUTER_PLANETS = [swe.URANUS, swe.NEPTUNE, swe.PLUTO]
        
        # Internal Data Storage
        self.birth_pos = {}
        self.birth_cusps = []
        self.ayanamsa = 0

    def calculate_birth_data(self, dob, tob):
        """Calculates precise KP Birth Chart data using your default location[cite: 1, 18]."""
        d, m, y = map(int, dob.split("/"))
        hh, mm, ss = map(int, tob.split(":"))
        # Convert to Universal Time for Swisseph[cite: 18]
        jd_ut = swe.julday(y, m, d, hh + mm/60 + ss/3600 - self.tz_offset)
        
        # Set Sidereal Mode to KP (Khullar/Newcomb)[cite: 18]
        swe.set_sid_mode(5, 0, 0)
        self.ayanamsa = swe.get_ayanamsa_ut(jd_ut)
        
        # Get Positions and Cusps[cite: 18]
        self.birth_pos = self.get_planetary_positions(jd_ut)
        res = swe.houses_ex(jd_ut, self.lat, self.lon, b'P', 0)
        self.birth_cusps = [(c - self.ayanamsa) % 360 for c in res[0]]
        return jd_ut

    def get_planetary_positions(self, jd):
        """Calculates Sidereal lon, Star Lord, and Speed for any given Julian Day[cite: 9, 18]."""
        p_data = {}
        flags = swe.FLG_SWIEPH | swe.FLG_SIDEREAL
        
        for p_id in list(PLANET_MAP.keys()) + self.OUTER_PLANETS:
            res, _ = swe.calc_ut(jd, p_id, flags)
            lon, speed = res[0], res[3]
            
            # KP Stellar Logic: Calculate Nakshatra and Star Lord[cite: 9]
            total_minutes = lon * 60
            nak_idx = int(total_minutes // 800)
            star_lord = DASHA_ORDER[nak_idx % 9]
            
            name = PLANET_MAP.get(p_id, str(p_id))
            p_data[name] = {
                'lon': lon, 
                'speed': speed, 
                'star_lord': star_lord,
                'is_retro': speed < 0 and p_id not in [10, 11]
            }
        return p_data

    def apply_rule_4_logic(self, p_data, key_p="Mo"):
        """
        Analyzes Stellar Rule 4: Power Shifts[cite: 1].
        If other planets share the Star Lord of the key planet, it is a bearish 'Shift'[cite: 1].
        """
        x = p_data[key_p]['star_lord']
        y = p_data[x]['star_lord']
        
        # Detect X1/Y1 (Other planets occupying the same Star Lord)[cite: 1]
        x1 = [p for p in p_data if p in PLANET_MAP.values() and p_data[p]['star_lord'] == x and p != key_p]
        y1 = [p for p in p_data if p in PLANET_MAP.values() and p_data[p]['star_lord'] == y and p != x]
        
        score = 0
        if x1 or y1:
            score -= 5  # Power shift penalty[cite: 1]
        else:
            if x in self.BULL_PLANETS or y in self.BULL_PLANETS:
                score += 3  # Bullish logic[cite: 1]
        
        return score

    def generate_market_pdf(self, days=5, mode="Moon"):
        """Generates a formal trend report PDF with data and graphs[cite: 1]."""
        start_date = datetime.datetime.now()
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", 'B', 16)
        pdf.cell(200, 10, f"KP Financial Forecast: {mode}-Centric", ln=True, align='C')
        
        results = []
        for i in range(days):
            date_obj = start_date + datetime.timedelta(days=i)
            # Standard Market Calculation Time: 09:30 AM[cite: 1]
            jd = swe.julday(date_obj.year, date_obj.month, date_obj.day, 9.5 - self.tz_offset)
            
            p_data = self.get_planetary_positions(jd)
            score = self.apply_rule_4_logic(p_data, key_p=mode[:2]) # Handles "Moon", "Sun", "Jup"
            
            results.append({'Date': date_obj.date(), 'Score': score})
            pdf.set_font("Arial", size=10)
            pdf.cell(0, 8, f"Date: {date_obj.date()} | Forecast Score: {score} | Moon Star: {p_data['Mo']['star_lord']}", ln=True)

        # Create Trend Graph[cite: 1]
        df = pd.DataFrame(results)
        plt.figure(figsize=(8, 4))
        plt.plot(df['Date'], df['Score'], marker='o', linestyle='-', color='blue')
        plt.title(f"Predicted Market Trend ({mode})")
        plt.grid(True)
        graph_path = "market_trend_temp.png"
        plt.savefig(graph_path)
        pdf.image(graph_path, x=10, y=pdf.get_y() + 5, w=180)
        
        filename = f"Market_Forecast_{datetime.date.today()}.pdf"
        pdf.output(filename)
        return filename

# --- UI VISUALIZATION ---

def render_dashboard(engine):
    """Prints a high-fidelity KP Dashboard to the terminal[cite: 16, 17]."""
    console = Console()
    console.print(Panel(f"[bold green]KP MASTER CONSOLE[/] | Lat: {engine.lat} Lon: {engine.lon}", border_style="bright_blue"))

    # South Indian Chart Grid[cite: 17]
    sign_boxes = {i: [] for i in range(12)}
    for p, data in engine.birth_pos.items():
        if p in PLANET_MAP.values():
            s_idx = int(data['lon'] / 30)
            sign_boxes[s_idx].append(f"{p} {int(data['lon']%30)}°")

    grid = Table.grid(expand=True)
    for _ in range(4): grid.add_column(ratio=1)
    def make_box(idx): return Panel("\n".join(sign_boxes[idx]), title=f"[cyan]{RASHI_NAMES[idx]}[/]", border_style="white")

    grid.add_row(make_box(11), make_box(0), make_box(1), make_box(2))
    grid.add_row(make_box(10), Panel("[bold yellow]D-1\nCHART[/]", box=box.SIMPLE, justify="center"), "", make_box(3))
    grid.add_row(make_box(9), "", "", make_box(4))
    grid.add_row(make_box(8), make_box(7), make_box(6), make_box(5))
    
    console.print(grid)

# --- READY-TO-RUN EXECUTION ---

if __name__ == "__main__":
    # 1. Initialize with your default location[cite: 1]
    engine = MasterStandaloneEngine()
    
    # 2. Process Birth Data for Dashboard[cite: 18]
    # Example values: Your DOB and a neutral time
    engine.calculate_birth_data(dob="05/04/1979", tob="12:00:00")
    render_dashboard(engine)
    
    # 3. Generate Market Forecast PDF[cite: 1]
    report_name = engine.generate_market_pdf(days=7, mode="Moon")
    print(f"\n[SYSTEM] Standalone Run Complete. PDF Generated: {report_name}")