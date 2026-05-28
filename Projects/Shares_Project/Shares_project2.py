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
        """Initializes with your default location logic."""
        self.lat = lat
        self.lon = lon
        self.tz_offset = tz_offset
        swe.set_ephe_path('./ephe') 
        
        self.BULL_PLANETS = ["Ju", "Ra"]
        self.BEAR_PLANETS = ["Ma", "Sa"]
        self.birth_pos = {}

    def calculate_birth_data(self, dob, tob):
        """Calculates birth chart using Sidereal Mode 5."""
        d, m, y = map(int, dob.split("/"))
        hh, mm, ss = map(int, tob.split(":"))
        jd_ut = swe.julday(y, m, d, hh + mm/60 + ss/3600 - self.tz_offset)
        
        swe.set_sid_mode(5, 0, 0)
        ayanamsa = swe.get_ayanamsa_ut(jd_ut)
        
        self.birth_pos = self.get_planetary_positions(jd_ut, ayanamsa, debug=True)
        return jd_ut

    def get_planetary_positions(self, jd, ayanamsa, debug=False):
        """Calculates precise longitudes and Star Lords."""
        p_data = {}
        flags = swe.FLG_SWIEPH | swe.FLG_SIDEREAL
        
        if debug:
            print(f"\n[DEBUG] Calculating Positions for JD: {jd}")
            print(f"{'Planet':<7} | {'Longitude':<12} | {'Star Lord':<10}")
            print("-" * 35)

        for p_id, name in PLANET_MAP.items():
            res, _ = swe.calc_ut(jd, p_id, flags)
            # Apply Ayanamsa correction manually for clarity
            lon = (res[0] - ayanamsa) % 360
            
            # KP Stellar Logic (800' divisions)
            nak_idx = int((lon * 60) // 800)
            star_lord = DASHA_ORDER[nak_idx % 9]
            
            p_data[name] = {'lon': lon, 'star_lord': star_lord, 'speed': res[3]}
            
            if debug:
                print(f"{name:<7} | {lon:<12.4f} | {star_lord:<10}")
        
        return p_data

    def apply_rule_4_logic(self, p_data, key_p="Mo", debug=False):
        """Rule 4: Counting power shifts (X1 analysis)."""
        x = p_data[key_p]['star_lord']
        y = p_data[x]['star_lord']
        
        # Counting: How many planets share the Moon's Star Lord?
        x1_list = [p for p in p_data if p_data[p]['star_lord'] == x and p != key_p]
        
        if debug:
            print(f"\n[RULE 4 DEBUG] Key Planet: {key_p} (Star: {x})")
            print(f"-> Other planets in {x}: {x1_list if x1_list else 'None'}")

        score = 0
        if x1_list:
            score -= 5 # Power Shift Penalty
            if debug: print(f"-> Result: Penalty Applied (-5) due to X1 shift.")
        elif x in self.BULL_PLANETS or y in self.BULL_PLANETS:
            score += 3 # Bullish Bonus
            if debug: print(f"-> Result: Bullish Alignment (+3) found in Star {x} or Sub-Star {y}.")
        else:
            if debug: print(f"-> Result: Neutral (0).")
            
        return score

    def generate_market_pdf(self, days=7):
        """Calculates 7-day forecast with full step-by-step debug prints."""
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", 'B', 14)
        pdf.cell(200, 10, "KP 6-Hour Market Forecast (Debug Mode)", ln=True, align='C')
        
        results = []
        start_date = datetime.datetime.now()
        
        for i in range(days):
            date_obj = start_date + datetime.timedelta(days=i)
            print(f"\n{'-'*50}\nFORECAST FOR DATE: {date_obj.date()}\n{'-'*50}")
            
            # Start at market open (09:30 AM)
            jd = swe.julday(date_obj.year, date_obj.month, date_obj.day, 9.5 - self.tz_offset)
            ayanamsa = swe.get_ayanamsa_ut(jd)
            
            p_data = self.get_planetary_positions(jd, ayanamsa, debug=True)
            score = self.apply_rule_4_logic(p_data, debug=True)
            
            results.append({'Date': date_obj.date(), 'Score': score})
            pdf.set_font("Arial", size=10)
            pdf.cell(0, 10, f"Date: {date_obj.date()} | Score: {score} | Moon Star: {p_data['Mo']['star_lord']}", ln=True)

        pdf.output(f"Market_Debug_Report_{datetime.date.today()}.pdf")
        return results

def render_dashboard(engine):
    """Draws the South Indian Chart."""
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
    # 1. Show the Birth Dashboard first
    engine.calculate_birth_data(dob="05/04/1979", tob="12:00:00")
    render_dashboard(engine)
    
    # 2. Run the Market Forecast with full printing for every calculation
    engine.generate_market_pdf(days=7)
    print("\nSuccess: PDF Generated. Review the terminal output above for the step-by-step counting.")