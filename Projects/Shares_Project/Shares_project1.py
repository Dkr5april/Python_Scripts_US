import swisseph as swe
import datetime
import pandas as pd
from fpdf import FPDF
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.align import Align
from rich import box

# --- GLOBAL CONFIGURATION ---
PLANET_MAP = {0: "Su", 1: "Mo", 2: "Ma", 3: "Me", 4: "Ju", 5: "Ve", 6: "Sa", 10: "Ra", 11: "Ke"}
RASHI_NAMES = ["Ar", "Ta", "Ge", "Cn", "Le", "Vi", "Li", "Sc", "Sg", "Cp", "Aq", "Pi"]
DASHA_ORDER = ["Ke", "Ve", "Su", "Mo", "Ma", "Ra", "Ju", "Sa", "Me"]

# 6-Hour Dasha Compression (360 Minutes Total)
DASHA_6HR_MAP = {
    "Ke": 21, "Ve": 60, "Su": 18, "Mo": 30,
    "Ma": 21, "Ra": 54, "Ju": 48, "Sa": 57, "Me": 51
}

class MasterStandaloneEngine:
    def __init__(self, lat=16.1176, lon=80.9314, tz_offset=5.5):
        """Initializes with default location."""
        self.lat = lat
        self.lon = lon
        self.tz_offset = tz_offset
        swe.set_ephe_path('./ephe') 
        
        self.BULL_PLANETS = ["Ju", "Ra"]
        self.BEAR_PLANETS = ["Ma", "Sa"]
        self.birth_pos = {}

    def calculate_birth_data(self, dob, tob):
        """Calculates KP data using sidereal mode 5."""
        d, m, y = map(int, dob.split("/"))
        hh, mm, ss = map(int, tob.split(":"))
        jd_ut = swe.julday(y, m, d, hh + mm/60 + ss/3600 - self.tz_offset)
        
        # Fixed: SIDM_KP is index 5 in pyswisseph
        swe.set_sid_mode(5, 0, 0)
        ayanamsa = swe.get_ayanamsa_ut(jd_ut)
        
        self.birth_pos = self.get_planetary_positions(jd_ut, ayanamsa)
        return jd_ut

    def get_planetary_positions(self, jd, ayanamsa):
        """Calculates Star Lords for Stellar Rule 4."""
        p_data = {}
        flags = swe.FLG_SWIEPH | swe.FLG_SIDEREAL
        
        for p_id, name in PLANET_MAP.items():
            res, _ = swe.calc_ut(jd, p_id, flags)
            lon = (res[0] - ayanamsa) % 360
            
            # KP Stellar Logic
            nak_idx = int((lon * 60) // 800)
            star_lord = DASHA_ORDER[nak_idx % 9]
            
            p_data[name] = {'lon': lon, 'star_lord': star_lord, 'speed': res[3]}
        return p_data

    def apply_rule_4_logic(self, p_data, key_p="Mo"):
        """Rule 4: Power Shift Detection (X1 analysis)."""
        x = p_data[key_p]['star_lord']
        y = p_data[x]['star_lord']
        
        # Check for Power Shift
        x1 = [p for p in p_data if p_data[p]['star_lord'] == x and p != key_p]
        
        score = 0
        if x1:
            score -= 5 # Bearish Penalty
        elif x in self.BULL_PLANETS or y in self.BULL_PLANETS:
            score += 3 # Bullish Bonus
            
        return score

    def generate_market_pdf(self, days=5):
        """Generates report based on 09:30 AM market opening."""
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", 'B', 14)
        pdf.cell(200, 10, "KP 6-Hour Market Forecast", ln=True, align='C')
        
        results = []
        start_date = datetime.datetime.now()
        
        for i in range(days):
            date_obj = start_date + datetime.timedelta(days=i)
            # Market Open at 09:30 AM
            jd = swe.julday(date_obj.year, date_obj.month, date_obj.day, 9.5 - self.tz_offset)
            
            ayanamsa = swe.get_ayanamsa_ut(jd)
            p_data = self.get_planetary_positions(jd, ayanamsa)
            score = self.apply_rule_4_logic(p_data)
            
            results.append({'Date': date_obj.date(), 'Score': score})
            pdf.set_font("Arial", size=10)
            pdf.cell(0, 10, f"Date: {date_obj.date()} | Score: {score} | Moon Star: {p_data['Mo']['star_lord']}", ln=True)

        pdf.output(f"Market_Report_{datetime.date.today()}.pdf")
        return results

def render_dashboard(engine):
    """Visualizes the D-1 South Indian Chart."""
    console = Console()
    console.print(Panel(f"[bold green]KP MASTER CONSOLE[/] | Lat: {engine.lat} Lon: {engine.lon}", border_style="bright_blue"))

    sign_boxes = {i: [] for i in range(12)}
    for p, data in engine.birth_pos.items():
        if p in PLANET_MAP.values():
            s_idx = int(data['lon'] / 30)
            sign_boxes[s_idx].append(f"{p} {int(data['lon']%30)}°")

    grid = Table.grid(expand=True)
    for _ in range(4): grid.add_column(ratio=1)
    
    def make_box(idx): 
        return Panel("\n".join(sign_boxes[idx]), title=f"[cyan]{RASHI_NAMES[idx]}[/]", border_style="white")

    center_label = Panel(Align.center("[bold yellow]D-1\nCHART[/]", vertical="middle"), box=box.SIMPLE)

    grid.add_row(make_box(11), make_box(0), make_box(1), make_box(2))
    grid.add_row(make_box(10), center_label, "", make_box(3))
    grid.add_row(make_box(9), "", "", make_box(4))
    grid.add_row(make_box(8), make_box(7), make_box(6), make_box(5))
    
    console.print(grid)

# --- EXECUTION ---
if __name__ == "__main__":
    engine = MasterStandaloneEngine()
    # Loading your birth profile
    engine.calculate_birth_data(dob="05/04/1979", tob="12:00:00")
    render_dashboard(engine)
    engine.generate_market_pdf(days=7)
    print("\nSuccess: Dashboard rendered and 6-hour Market PDF generated.")