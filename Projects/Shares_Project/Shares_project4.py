import swisseph as swe
import datetime
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

# --- GLOBAL CONFIGURATION ---
# Mapping Swiss Ephemeris constants to KP nomenclature
PLANET_MAP = {
    0: "Su", 1: "Mo", 2: "Ma", 3: "Me", 
    4: "Ju", 5: "Ve", 6: "Sa", 10: "Ra", 11: "Ke"
}

# The standard Vimshottari order used for Star Lord determination
DASHA_ORDER = ["Ke", "Ve", "Su", "Mo", "Ma", "Ra", "Ju", "Sa", "Me"]

class KPMasterEngine:
    """
    Advanced KP Astrology Engine with specialized logic for 
    Nifty/Market prediction based on Moon's Star Lord house placement.
    """
    def __init__(self, lat, lon, tz_offset):
        self.lat = lat
        self.lon = lon
        self.tz_offset = tz_offset
        # Setting ephemeris path for high-precision calculations
        swe.set_ephe_path('./ephe') 
        
        # KP Significators for Market Analysis
        self.BULL_HOUSES = [2, 6, 10, 11]
        self.BEAR_HOUSES = [5, 8, 12]

    def get_sidereal_data(self, date_str, time_str):
        console = Console()
        d, m, y = map(int, date_str.split("/"))
        hh, mm = map(int, time_str.split(":"))
        
        # --- DEBUG BLOCK: TEMPORAL CONVERSION ---
        local_time_decimal = hh + (mm / 60.0)
        utc_time_decimal = local_time_decimal - self.tz_offset
        jd_ut = swe.julday(y, m, d, utc_time_decimal)
        
        console.print(f"\n[bold yellow]--- STEP 1: TEMPORAL & AYANAMSA CALCULATION ---[/]")
        console.print(f"[DEBUG] Input Local Time  : {hh:02}:{mm:02} (IST/Local)")
        console.print(f"[DEBUG] GMT/UTC Decimal   : {utc_time_decimal:.4f}")
        console.print(f"[DEBUG] Julian Day (UT)   : {jd_ut:.6f}")
        
        # --- DEBUG BLOCK: AYANAMSA EXTRACTION ---
        # Mode 5 is KP New (Newcomb) - The standard for KP Astrology
        swe.set_sid_mode(5, 0, 0) 
        ayanamsa_val = swe.get_ayanamsa_ut(jd_ut)
        
        aya_deg = int(ayanamsa_val)
        aya_min = int((ayanamsa_val % 1) * 60)
        aya_sec = int(((ayanamsa_val * 60) % 1) * 60)
        
        console.print(f"[DEBUG] Selected Mode     : KP New Ayanamsa")
        console.print(f"[DEBUG] Raw Ayanamsa Val  : {ayanamsa_val:.8f}")
        console.print(f"[DEBUG] Ayanamsa (DMS)    : {aya_deg}° {aya_min}' {aya_sec}\"")
        
        # --- DEBUG BLOCK: CUSPAL BOUNDARIES ---
        # 'P' denotes Placidus, strictly required for KP
        cusps, ascmc = swe.houses_ex(jd_ut, self.lat, self.lon, b'P')
        console.print(f"[DEBUG] Sayana Ascendant  : {ascmc[0]:.4f}°")
        sid_asc = (ascmc[0] - ayanamsa_val) % 360
        console.print(f"[DEBUG] Sidereal Ascendant: {sid_asc:.4f}°")
        
        # --- DEBUG BLOCK: PLANETARY MATH ---
        console.print(f"\n[bold yellow]--- STEP 2: PLANETARY NIRAYANA SUBTRACTION ---[/]")
        p_data = {}
        flags = swe.FLG_SWIEPH 
        
        for p_id, name in PLANET_MAP.items():
            # 1. Get Sayana (Tropical) Position
            res_sayana, _ = swe.calc_ut(jd_ut, p_id, flags)
            sayana_lon = res_sayana[0]
            
            # 2. Subtract Ayanamsa for Nirayana (Sidereal)
            nirayana_lon = (sayana_lon - ayanamsa_val) % 360
            
            # 3. Calculate Star Lord (1 Nakshatra = 13°20' = 800')
            nak_idx = int((nirayana_lon * 60) // 800)
            star_lord = DASHA_ORDER[nak_idx % 9]
            
            # 4. Find House Occupancy based on Placidus Cusps
            house = self.find_house(nirayana_lon, cusps)
            
            p_data[name] = {
                'lon': nirayana_lon, 
                'star_lord': star_lord, 
                'house': house,
                'sayana': sayana_lon
            }
            
            # Detailed debug per planet for verification
            console.print(f"[DEBUG] {name:<3} | Sayana: {sayana_lon:>8.4f} | - Aya: {ayanamsa_val:.4f} | = Nirayana: {nirayana_lon:>8.4f}")

        return p_data, ayanamsa_val

    def find_house(self, lon, cusps):
        """Calculates the house number based on Placidus boundaries"""
        for i in range(12):
            h_start = cusps[i]
            h_end = cusps[(i + 1) % 12]
            if h_start < h_end:
                if h_start <= lon < h_end: return i + 1
            else: # Handling the 360/0 degree transition
                if lon >= h_start or lon < h_end: return i + 1
        return 1

    def display_analysis(self, date_str, time_str, city_name):
        console = Console()
        p_data, aya = self.get_sidereal_data(date_str, time_str)
        
        console.print("\n" + "="*85)
        console.print(Panel(
            f"[bold cyan]KP STELLAR REPORT: {city_name.upper()}[/]\n"
            f"INPUT DATE : {date_str}  |  TIME: {time_str}\n"
            f"COORDINATES: {self.lat} N, {self.lon} E | TZ: {self.tz_offset}",
            subtitle=f"Ayanamsa Used: {aya:.6f}",
            style="bright_blue"
        ))

        # Main Data Table
        table = Table(title="Sidereal Longitudes and Stellar Links", header_style="bold white")
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

        # --- DEBUG BLOCK: RULE 4 LOGIC ---
        mo = p_data['Mo']
        x_lord = mo['star_lord']
        x_house = p_data[x_lord]['house']
        dist = (x_house - mo['house'] + 12) % 12
        if dist == 0: dist = 12

        console.print(Panel(
            f"[bold yellow]RULE 4 HOUSE COUNTING (Bhavat Bhavam)[/]\n"
            f"1. Moon's Position: House [bold]{mo['house']}[/]\n"
            f"2. Star Lord ({x_lord}) Position: House [bold]{x_house}[/]\n"
            f"3. Calculated Count: {dist} houses away",
            title="Market Logic Check", border_style="green"
        ))

        # --- TREND PREDICTION ---
        score = 0
        if x_house in self.BULL_HOUSES: 
            score = 3
            res_msg = "[bold green]BULLISH SIGNAL[/] (Star Lord in 2, 6, 10, or 11)"
        elif x_house in self.BEAR_HOUSES: 
            score = -5
            res_msg = "[bold red]BEARISH SIGNAL[/] (Star Lord in 5, 8, or 12)"
        else:
            res_msg = "[bold white]NEUTRAL[/]"

        console.print(f"\n[bold reverse] FINAL MARKET SCORE: {score} [/]")
        console.print(f"TREND: {res_msg}\n")
        console.print("="*85 + "\n")

if __name__ == "__main__":
    # Defaults from profile: Latitude 16.1176, Longitude 80.9314
    LAT, LON = 16.1176, 80.9314
    
    print("--- KP Prediction System (Debug Active) ---")
    city = input("Enter City Name: ")
    date_in = input("Enter Date (DD/MM/YYYY): ")
    time_in = input("Enter Time (HH:MM): ")
    
    engine = KPMasterEngine(LAT, LON, 5.5)
    engine.display_analysis(date_in, time_in, city)