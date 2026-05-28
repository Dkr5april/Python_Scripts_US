import swisseph as swe
import datetime
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

# --- GLOBAL CONFIGURATION ---
PLANET_MAP = {0: "Su", 1: "Mo", 2: "Ma", 3: "Me", 4: "Ju", 5: "Ve", 6: "Sa", 10: "Ra", 11: "Ke"}
DASHA_ORDER = ["Ke", "Ve", "Su", "Mo", "Ma", "Ra", "Ju", "Sa", "Me"]

class KPMasterEngine:
    def __init__(self, lat, lon, tz_offset):
        self.lat = lat
        self.lon = lon
        self.tz_offset = tz_offset
        swe.set_ephe_path('./ephe') 
        # KP Standard Bull/Bear Houses
        self.BULL_HOUSES = [2, 6, 10, 11]
        self.BEAR_HOUSES = [5, 8, 12]

    def get_sidereal_data(self, date_str, time_str):
        console = Console()
        d, m, y = map(int, date_str.split("/"))
        hh, mm = map(int, time_str.split(":"))
        
        # Convert Local Time to UTC
        jd_ut = swe.julday(y, m, d, (hh + mm/60) - self.tz_offset)
        
        # [DEBUG] Ayanamsa Verification
        swe.set_sid_mode(5, 0, 0) # KP New Ayanamsa
        ayanamsa = swe.get_ayanamsa_ut(jd_ut)
        console.print(f"[DEBUG] Julian Day: {jd_ut:.4f} | Ayanamsa: {ayanamsa:.6f}")
        
        # [DEBUG] Cuspal Boundaries
        cusps, ascmc = swe.houses_ex(jd_ut, self.lat, self.lon, b'P')
        console.print(f"[DEBUG] House 1 (Asc) Start: {cusps[0]:.4f}°")
        
        p_data = {}
        flags = swe.FLG_SWIEPH | swe.FLG_SIDEREAL
        
        for p_id, name in PLANET_MAP.items():
            res, _ = swe.calc_ut(jd_ut, p_id, flags)
            # Apply Ayanamsa for True Sidereal Longitude
            lon = (res[0] - ayanamsa) % 360
            
            # Star Lord Calculation (13°20' increments)
            nak_idx = int((lon * 60) // 800)
            star_lord = DASHA_ORDER[nak_idx % 9]
            
            # House Determination
            house = self.find_house(lon, cusps)
            
            p_data[name] = {
                'lon': lon, 
                'star_lord': star_lord, 
                'house': house
            }
            # [DEBUG] Individual Planet Calc
            console.print(f"[DEBUG] Planet: {name:<3} | Lon: {lon:>8.4f} | Star: {star_lord:<2} | House: {house}")

        return p_data, ayanamsa, jd_ut

    def find_house(self, lon, cusps):
        for i in range(12):
            h_start = cusps[i]
            h_end = cusps[(i + 1) % 12]
            if h_start < h_end:
                if h_start <= lon < h_end: return i + 1
            elif lon >= h_start or lon < h_end: return i + 1
        return 1

    def display_analysis(self, date_str, time_str, city_name):
        console = Console()
        
        # Capture data with internal debug prints
        p_data, aya, jd = self.get_sidereal_data(date_str, time_str)
        
        # 1. Main Header
        console.print("\n" + "="*60)
        console.print(Panel(
            f"[bold cyan]KP FINAL REPORT FOR: {city_name.upper()}[/]\n"
            f"INPUT DATE: {date_str} | TIME: {time_str}\n"
            f"LAT/LON: {self.lat}, {self.lon} | TZ: {self.tz_offset}",
            style="bright_blue"
        ))

        # 2. Planetary Results Table
        table = Table(title="Calculated Planetary Positions (Sidereal)")
        table.add_column("Planet", style="yellow")
        table.add_column("DMS Longitude", justify="right")
        table.add_column("House", justify="center")
        table.add_column("Star Lord (X)", style="magenta")
        table.add_column("X-Lord House", justify="center")
        
        for p, d in p_data.items():
            deg = int(d['lon'])
            m_full = (d['lon'] % 1) * 60
            mnt = int(m_full)
            sec = int((m_full % 1) * 60)
            dms = f"{deg:03}° {mnt:02}' {sec:02}\""
            
            x_lord = d['star_lord']
            table.add_row(p, dms, str(d['house']), x_lord, str(p_data[x_lord]['house']))
        
        console.print(table)

        # 3. Rule 4 "Counting" Debug
        mo = p_data['Mo']
        x_lord = mo['star_lord']
        x_house = p_data[x_lord]['house']
        
        # Counting from Moon to Star Lord's House
        dist = (x_house - mo['house'] + 12) % 12
        if dist == 0: dist = 12

        console.print(Panel(
            f"[bold yellow]RULE 4 HOUSE COUNTING LOGIC[/]\n"
            f"Step 1: Locate Moon's House -> [bold]{mo['house']}[/]\n"
            f"Step 2: Locate Moon's Star Lord ({x_lord}) House -> [bold]{x_house}[/]\n"
            f"Step 3: Count (Bhavat Bhavam) -> [bold]{dist} Houses Away[/]",
            title="Logic Check", border_style="green"
        ))

        # 4. Final Result
        score = 0
        if x_house in self.BULL_HOUSES: 
            score = 3
            result_txt = "[bold green]BULLISH SIGNAL[/] (Star Lord in House of Gain)"
        elif x_house in self.BEAR_HOUSES: 
            score = -5
            result_txt = "[bold red]BEARISH SIGNAL[/] (Star Lord in House of Loss)"
        else:
            result_txt = "[bold white]NEUTRAL[/]"

        console.print(f"\n[bold inverse] FINAL MARKET SCORE: {score} [/]")
        console.print(f"Outcome: {result_txt}\n")

# --- EXECUTION BLOCK ---
if __name__ == "__main__":
    # Using your saved default values
    DEFAULT_LAT = 16.1176 
    DEFAULT_LON = 80.9314

    print("--- KP Market Analysis Terminal ---")
    city = input("Enter City Name: ")
    lat_in = input(f"Enter Latitude (default {DEFAULT_LAT}): ") or str(DEFAULT_LAT)
    lon_in = input(f"Enter Longitude (default {DEFAULT_LON}): ") or str(DEFAULT_LON)
    date_in = input("Enter Date (DD/MM/YYYY): ")
    time_in = input("Enter Time (HH:MM): ")
    tz_in = input("Enter Timezone Offset (default 5.5): ") or "5.5"

    engine = KPMasterEngine(float(lat_in), float(lon_in), float(tz_in))
    engine.display_analysis(date_in, time_in, city)