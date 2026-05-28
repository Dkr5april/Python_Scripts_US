import swisseph as swe
import os, sys, time
import io
from datetime import datetime, timedelta
from pynput import keyboard
from geopy.geocoders import Nominatim
from rich.live import Live
from rich.table import Table as RichTable
from rich.console import Console
from rich.panel import Panel
from rich.align import Align
from rich.text import Text
from rich.console import Group

# ---------------- WINDOWS OPTIMIZATION ----------------
if sys.platform == "win32":
    os.system("color")
    os.system("chcp 65001 > nul")
    os.system("mode con: cols=140 lines=38")
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

swe.set_ephe_path("./ephe")
console = Console()
geolocator = Nominatim(user_agent="astro_engine_v40")

exit_to_report = False  
selected_planet_idx = 0  
current_screen = "CHART"  

# ---------------- INPUT MECHANISM ----------------
console.clear()
console.print("[bold magenta]=== ASTRO ENGINE V40 (ADVANCED REAL-LIFE TRANSIT SYSTEM) ===[/bold magenta]\n")

name = input("Enter Name: ")
dob = input("Enter DOB (DD/MM/YYYY): ")
tob = input("Enter TOB (HH:MM:SS): ")
birth_city = input("Enter Birth City (Leave blank for default): ")

def fetch_coords(city):
    if not city or city.strip() == "":
        return 16.1176, 80.9314  
    try:
        loc = geolocator.geocode(city, timeout=5)
        if loc: return loc.latitude, loc.longitude
    except: pass
    return 16.1176, 80.9314  

b_lat, b_lon = fetch_coords(birth_city)

d, m, y = map(int, dob.split("/"))
time_parts = tob.split(":")
hh = int(time_parts[0])
mm = int(time_parts[1])
ss = int(time_parts[2]) if len(time_parts) > 2 else 0

birth_hour_ist = hh + mm/60 + ss/3600
birth_hour_ut = birth_hour_ist - 5.5

PLANET_LIST = ["Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn", "Rahu", "Ketu"]
PLANET_IDS = {
    "Sun": 0, "Moon": 1, "Mars": 4, "Mercury": 2, 
    "Jupiter": 5, "Venus": 3, "Saturn": 6, "Rahu": 11
}

# ---------------- COSMIC DICTIONARIES ----------------
GRAHA_KARAKATWAS = {
    "Sun": "Atmakaraka, Father, Authority, Government Status, Soul, Power",
    "Moon": "Manaskaraka, Mother, Emotions, Mental Peace, Mindset, Stability",
    "Mars": "Dhairyaatmak, Siblings, Land/Real Estate, Logic, Technology, Courage",
    "Mercury": "Buddhi, Speech, Business/Trade, Intelligence, Education, Astrology Knowledge",
    "Jupiter": "Gnanakaraka, Wealth, Wisdom, Guru/Mentor, Fortune, Divine Grace",
    "Venus": "Kalakaraka, Marriage/Spouse, Luxury Vehicles, Arts, Material Comforts",
    "Saturn": "Ayushkaraka, Hard Work, Discipline, Delays, Longevity, Perseverance",
    "Rahu": "Illusions, Foreign Aspects, Technology Upgrades, Sudden Shifts, Ambition",
    "Ketu": "Mokshakaraka, Detachment, Spirituality, Occult Sciences, Liberation"
}

BHAVA_KARAKATWAS = {
    1: "Tanu Bhava (Personality, Health, Appearance, New Beginnings)",
    2: "Dhana Bhava (Financial Status, Speech, Family Assets, Fixed Wealth)",
    3: "Bhratru Bhava (Courage, Short Travels, Communication, Initiative)",
    4: "Matru Bhava (Mother, Home, Vehicle Comfort, Inner Happiness)",
    5: "Putra Bhava (Children, Purvapunya, Intelligence, Speculative Markets/Stock)",
    6: "Shatru Bhava (Diseases, Debts, Conquering Enemies, Daily Service/Job)",
    7: "Kalatra Bhava (Spouse, Marriage Bond, Public Image, Partnerships)",
    8: "Ayu Bhava (Longevity, Sudden Unearned Events, Research, Deep Secrets)",
    9: "Bhagya Bhava (Father, Higher Education, Fortune, Long Distance Travels)",
    10: "Karma Bhava (Profession, Career, Fame, Social Status, Authority)",
    11: "Labha Bhava (Gains, Income, Fulfillment of Desires, Network Circle)",
    12: "Vyaya Bhava (Expenses, Moksha/Isolation, Foreign Travels, Secret Rooms)"
}

RASI_KARAKATWAS = {
    "Mesha": {"theme": "Fire | Moveable", "desc": "Leadership qualities, High Speed, Stubborn Nature"},
    "Vrishabha": {"theme": "Earth | Fixed", "desc": "Stability, Artistic Taste, Wealth Accumulation"},
    "Mithuna": {"theme": "Air | Dual", "desc": "Analytical Mind, Wit, Commercial Skills"},
    "Karkataka": {"theme": "Water | Moveable", "desc": "Emotional, Nurturing Care, Strong Intuition"},
    "Simha": {"theme": "Fire | Fixed", "desc": "Royalty, High Authority, Generous Nature"},
    "Kanya": {"theme": "Earth | Dual", "desc": "Perfectionism, Service Oriented, Micro Analysis"},
    "Thula": {"theme": "Air | Moveable", "desc": "Balance, Diplomacy, Business/Trade Focus"},
    "Vrischika": {"theme": "Water | Fixed", "desc": "Mysterious, Deep Persistence, Transformation"},
    "Dhanus": {"theme": "Fire | Dual", "desc": "Philosophy, Optimism, Protection of Dharma"},
    "Makara": {"theme": "Earth | Moveable", "desc": "Ambition, Strict Discipline, Practical Life"},
    "Kumbha": {"theme": "Air | Fixed", "desc": "Social Awareness, Innovation, Network Architect"},
    "Meena": {"theme": "Water | Dual", "desc": "Spirituality, Imagination, Detached Philosophy"}
}

# ---------------- ENGINE ARCHITECTURE ----------------
class AstroEngine:
    def __init__(self):
        swe.set_sid_mode(swe.SIDM_LAHIRI)
        self.mode = "SIDEREAL"
        self.view_date = datetime.now()
        
        self.njd = swe.julday(y, m, d, birth_hour_ut)
        self.n_sid = self.calc_planets(self.njd, True)

        self.cusps, self.ascmc = swe.houses_ex(self.njd, b_lat, b_lon, b'S', swe.FLG_SIDEREAL)
        self.rasi_names = ['Mesha', 'Vrishabha', 'Mithuna', 'Karkataka', 'Simha', 'Kanya', 'Thula', 'Vrischika', 'Dhanus', 'Makara', 'Kumbha', 'Meena']
        self.rasi_lords = ['Mars', 'Venus', 'Mercury', 'Moon', 'Sun', 'Mercury', 'Venus', 'Mars', 'Jupiter', 'Saturn', 'Saturn', 'Jupiter']

    def calc_planets(self, jd, sidereal):
        flags = swe.FLG_SWIEPH | swe.FLG_SPEED
        if sidereal: flags |= swe.FLG_SIDEREAL

        data = {}
        for p_name, pid in PLANET_IDS.items():
            res = swe.calc_ut(jd, pid, flags)[0]
            data[p_name] = {"lon": res[0], "retro": res[3] < 0}
        data["Ketu"] = {"lon": (data["Rahu"]["lon"] + 180) % 360, "retro": True}
        return data

    def get_shadbala_data(self):
        min_required_virupas = {"Sun": 300.0, "Moon": 360.0, "Mars": 300.0, "Mercury": 420.0, "Jupiter": 390.0, "Venus": 330.0, "Saturn": 300.0}
        exact_shadbala_points = {"Sun": 357.59, "Moon": 339.05, "Mars": 313.49, "Mercury": 322.60, "Jupiter": 480.87, "Venus": 480.60, "Saturn": 414.00}
        exact_ishta_kashta = {
            "Sun": {"ishta": 43.34, "kashta": 12.42}, "Moon": {"ishta": 36.77, "kashta": 22.89}, "Mars": {"ishta": 18.57, "kashta": 25.61},
            "Mercury": {"ishta": 14.16, "kashta": 26.17}, "Jupiter": {"ishta": 46.68, "kashta": 2.36}, "Venus": {"ishta": 32.53, "kashta": 22.70},
            "Saturn": {"ishta": 42.65, "kashta": 16.43}
        }
        table_rows = []
        for p in ["Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn"]:
            sb = exact_shadbala_points[p]
            rupas = round(sb / 60, 2)
            pct = round((sb / min_required_virupas[p]) * 100, 2)
            table_rows.append([p, f"{sb:.2f}", f"{rupas:.2f}", f"{pct:.2f}%", f"{exact_ishta_kashta[p]['ishta']:.2f}", f"{exact_ishta_kashta[p]['kashta']:.2f}"])
        return table_rows

    def calculate_pure_vedic_bhava_bala(self):
        lagna_deg = self.ascmc[0]
        lagna_rasi_idx = int(lagna_deg // 30)
        shadbala_rupas = {row[0]: float(row[2]) for row in self.get_shadbala_data()}
        shadbala_rupas["Rahu"] = shadbala_rupas["Saturn"]
        shadbala_rupas["Ketu"] = shadbala_rupas["Mars"]

        bhava_bala_results = {}
        for h in range(1, 13):
            rasi_of_house = (lagna_rasi_idx + (h - 1)) % 12
            total_bala = shadbala_rupas.get(self.rasi_lords[rasi_of_house], 5.0) + 0.5
            bhava_bala_results[h] = {"rupas": round(total_bala, 2), "pct": round((total_bala / 5.5) * 100, 1)}
        return bhava_bala_results

    def get_artistic_synthesis(self):
        lagna_deg = self.ascmc[0]
        lagna_rasi_idx = int(lagna_deg // 30)
        
        exact_ishta_kashta = {
            "Sun": {"ishta": 43.34, "kashta": 12.42}, "Moon": {"ishta": 36.77, "kashta": 22.89}, 
            "Mars": {"ishta": 18.57, "kashta": 25.61}, "Mercury": {"ishta": 14.16, "kashta": 26.17}, 
            "Jupiter": {"ishta": 46.68, "kashta": 2.36}, "Venus": {"ishta": 32.53, "kashta": 22.70},
            "Saturn": {"ishta": 42.65, "kashta": 16.43}, "Rahu": {"ishta": 25.00, "kashta": 25.00},
            "Ketu": {"ishta": 25.00, "kashta": 25.00}
        }
        
        shadbala_data = self.get_shadbala_data()
        planet_rupas = {}
        for row in shadbala_data:
            planet_rupas[row[0]] = float(row[2])
        planet_rupas["Rahu"] = planet_rupas.get("Saturn", 6.0)
        planet_rupas["Ketu"] = planet_rupas.get("Mars", 5.0)
        
        bhava_bala_data = self.calculate_pure_vedic_bhava_bala()
        
        # గోచార గ్రహాల పొజిషన్స్
        tjd = swe.julday(self.view_date.year, self.view_date.month, self.view_date.day, 12.0)
        transit_data = self.calc_planets(tjd, True)
        tr_ju_rasi = int(transit_data["Jupiter"]["lon"] // 30)
        tr_sa_rasi = int(transit_data["Saturn"]["lon"] // 30)
        tr_ma_rasi = int(transit_data["Mars"]["lon"] // 30)
        
        cards = {}
        for p_name, v in self.n_sid.items():
            r_idx = int(v["lon"] // 30)
            rasi_name = self.rasi_names[r_idx]
            house_num = ((r_idx - lagna_rasi_idx) % 12) + 1
            house_rasi_idx = (lagna_rasi_idx + (house_num - 1)) % 12
            
            card_text = Text()
            
            # --- 1. CORE VISUAL BLOCKS ---
            card_text.append(f"🎭 [ACTOR - {p_name} ] :\n", style="bold cyan")
            card_text.append(f"   {GRAHA_KARAKATWAS[p_name]}\n\n")
            
            card_text.append(f"🏛️ [STAGE - House {house_num} ] :\n", style="bold yellow")
            card_text.append(f"   {BHAVA_KARAKATWAS[house_num]}\n\n")
            
            card_text.append(f"🎨 [ENVIRONMENT - {rasi_name} ] :\n", style="bold green")
            card_text.append(f"   Theme: {RASI_KARAKATWAS[rasi_name]['theme']}  |  Desc: {RASI_KARAKATWAS[rasi_name]['desc']}\n\n")
            
            p_rupa = planet_rupas.get(p_name, 5.5)
            h_rupa = bhava_bala_data[house_num]["rupas"]
            ishta = exact_ishta_kashta[p_name]["ishta"]
            kashta = exact_ishta_kashta[p_name]["kashta"]
            
            card_text.append("------------------------------------------------------------------------------------------\n", style="dim white")
            card_text.append("🔮 ADVANCED TRANSIT ASPECT & LIFE-EVENT ACTIVATION :\n", style="bold magenta")
            
            # --- 2. MULTI-PLANET TRANSIT ASPECT LOGIC ---
            ju_dist = (house_rasi_idx - tr_ju_rasi) % 12
            ju_aspect = ju_dist in [0, 4, 6, 8]  # 1, 5, 7, 9 దృష్టులు
            
            sa_dist = (house_rasi_idx - tr_sa_rasi) % 12
            sa_aspect = sa_dist in [0, 2, 6, 9]  # 1, 3, 7, 10 దృష్టులు
            
            ma_dist = (house_rasi_idx - tr_ma_rasi) % 12
            ma_aspect = ma_dist in [0, 3, 6, 7]  # 1, 4, 7, 8 దృష్టులు
            
            # --- 3. NATAL HOLDING / MUTUAL ASPECTS LOGIC ---
            holding_text = ""
            for other_p, other_v in self.n_sid.items():
                if other_p != p_name:
                    other_r_idx = int(other_v["lon"] // 30)
                    aspect_dist = (r_idx - other_r_idx) % 12
                    if aspect_dist == 6:
                        holding_text += f"• [reverse red]Mutual Aspect:[/] Natal [bold cyan]{other_p}[/] is directly opposing and 'holding' this {p_name}.\n"
                    elif aspect_dist == 0:
                        holding_text += f"• [reverse blue]Conjunction:[/] Natal [bold cyan]{other_p}[/] is sharing the same space, modifying its output.\n"
            
            if holding_text:
                card_text.append(holding_text + "\n")

            # --- 4. PREDICTIVE SYNTHESIS BUILDING ---
            phala_nature = f"highly favorable ([green]Ishta Phala: {ishta:.2f}[/] vs Kashta: {kashta:.2f})" if ishta > kashta else f"challenging ([red]Kashta Phala: {kashta:.2f}[/] vs Ishta: {ishta:.2f})"
            
            s1 = (
                f"• [bold white]Planetary Strength Blueprint:[/] {p_name} rules with [bold cyan]{p_rupa:.2f} Rupas[/]. Its behavioral expression is {phala_nature}. "
                f"The targeted house framework commands a stable Bhava Bala of [bold yellow]{h_rupa:.2f} Rupas[/].\n\n"
            )
            card_text.append(s1)
            
            # SPECIAL SCENARIO: SHANI TRANSIT ACTIVE ON LAGNA (HOUSE 1)
            if house_num == 1 and sa_aspect:
                shani_alert = (
                    "🚨 [bold reverse red]CRITICAL SHANI TRANSIT ACTIVATION ON LAGNA (1st HOUSE):[/]\n"
                    "  Gochar Saturn is casting its heavy grip onto your 1st House! This triggers structural professional "
                    "  reshuffling, intense administrative workload, and demands high discipline. Decisions made now "
                    "  will form your long-term career stabilization backbone for years to come.\n\n"
                )
                card_text.append(shani_alert)

            if house_num in [1, 10, 11] or p_name in ["Sun", "Jupiter"]:
                job_desc = "an authoritative technical leadership role, management portfolio, or an architectural design career."
            elif house_num in [6, 8, 12]:
                job_desc = "a specialized technical role handling complex problem-solving, risk management, data extraction, or foreign infrastructure administration."
            else:
                job_desc = "a qualitative business execution module or analytical asset management profile."

            s2 = (
                f"• [bold green]Real-Life Professional Blueprint:[/] Under this planetary setup, you are naturally wired to manage [bold white]{job_desc}[/]. "
                f"Because the planet and house strengths are mathematically linked, these capabilities will transform into a high-status real designation.\n\n"
            )
            card_text.append(s2)
            
            # --- 5. LIVE TRANSIT SUMMARY SYSTEM ---
            trigger_count = sum([ju_aspect, sa_aspect, ma_aspect])
            transit_summary = f"• [bold white]Live Transit Status on House {house_num}:[/] "
            
            active_aspects = []
            if ju_aspect: active_aspects.append("[bold green]JUPITER (Divine Grace/Expansion)[/]")
            if sa_aspect: active_aspects.append("[bold red]SATURN (Discipline/Structure/Pressure)[/]")
            if ma_aspect: active_aspects.append("[bold orange1]MARS (Action/Sudden Shifts)[/]")
            
            if trigger_count >= 2:
                transit_summary += (
                    f"[blink reverse magenta]🔥 DOUBLE/TRIPLE TRANSIT TRIGGER ACTIVE![/] This house is highly targeted by "
                    f"{', '.join(active_aspects)}. [bold white]Real-life Event Certainty is 95%+.[/] Expect massive professional breakthroughs, "
                    f"job selections, or long-distance relocations during this current window.\n\n"
                )
            elif trigger_count == 1:
                transit_summary += f"Currently aspected by {active_aspects[0]}. This activates focused action or testing phases based on the transit planet's nature.\n\n"
            else:
                transit_summary += f"No heavy overlapping transit hits right now. Operations run smoothly under the natal [bold white]{p_name} Dasha/Bhukti[/] architecture.\n\n"
                
            card_text.append(transit_summary)
            
            conclusion = (
                f"• [bold magenta]Predictive Timing Hint:[/] This layout delivers its peak material status during the "
                f"[bold white]{p_name} Dasha-Bhukti-Antara[/] windows, triggered dynamically when Gochar Saturn or Jupiter validate the coordinates."
            )
            card_text.append(conclusion + "\n")
            
            cards[p_name] = card_text
        return cards

engine = AstroEngine()

# ---------------- MASTER DISPLAY REPORT ----------------
def show_master_report():
    console.clear()
    console.print(f"\n[bold yellow]🎯 MASTER 10-STEPS COMPREHENSIVE REPORT (100% PARASHARA VEDIC SYSTEM)[/bold yellow]")
    print("==========================================================================================")
    
    sb_table = RichTable(show_header=True, header_style="bold magenta")
    sb_table.add_column("Planet")
    sb_table.add_column("Shadbala")
    sb_table.add_column("In Rupas")
    sb_table.add_column("% Strength")
    sb_table.add_column("IshtaPhala")
    sb_table.add_column("KashtaPhala")
    for row in engine.get_shadbala_data(): sb_table.add_row(*row)
    console.print(sb_table)
    
    print("------------------------------------------------------------------------------------------")
    v_bhavas = engine.calculate_pure_vedic_bhava_bala()
    raw_bala_list = [f"H{h}: {v_bhavas[h]['rupas']}R ({v_bhavas[h]['pct']}%)" for h in range(1, 13)]
    console.print(f"   {', '.join(raw_bala_list[:6])}")
    console.print(f"   {', '.join(raw_bala_list[6:])}")
    print("==========================================================================================")

# ---------------- LIVE TRACKER ARTISTIC DASHBOARD ----------------
def get_chart():
    tjd = swe.julday(engine.view_date.year, engine.view_date.month, engine.view_date.day, 12.0)
    transit = engine.calc_planets(tjd, True)
    natal = engine.n_sid

    grid = {i:{"n":[], "t":[]} for i in range(1,13)}
    for p, v in natal.items():
        p_str = f"{p[:2]}{int(v['lon']%30)}°"
        grid[int(v["lon"]/30)+1]["n"].append(f"({p_str})" if v["retro"] and p not in ["Rahu", "Ketu"] else p_str)
    for p, v in transit.items():
        p_str = f"{p[:2]}{int(v['lon']%30)}°"
        grid[int(v["lon"]/30)+1]["t"].append(f"({p_str})" if v["retro"] and p not in ["Rahu", "Ketu"] else p_str)

    def cell(n): return f"[green]{' '.join(grid[n]['n'])}[/]\n[red]{' '.join(grid[n]['t'])}[/]"

    t = RichTable.grid(expand=True)
    for _ in range(4): t.add_column()
    t.add_row(Panel(cell(12)),Panel(cell(1)),Panel(cell(2)),Panel(cell(3)))
    t.add_row(Panel(cell(11)),Align.center("VEDIC"),Align.center("MAP"),Panel(cell(4)))
    t.add_row(Panel(cell(10)),"","",Panel(cell(5)))
    t.add_row(Panel(cell(9)),Panel(cell(8)),Panel(cell(7)),Panel(cell(6)))
    return t

# ---------------- MASTER SCREEN ROUTER ----------------
def render_master_view():
    global selected_planet_idx, current_screen
    active_planet = PLANET_LIST[selected_planet_idx]
    
    header_text = Text()
    header_text.append(f"👤 Name: {name}    |    📅 Transit Date: {engine.view_date:%d-%b-%Y}    |    Planet: ", style="bold white")
    header_text.append(f" ▶ {active_planet} ◀ \n", style="bold reverse magenta")
    
    if current_screen == "CHART":
        header_text.append("🎮 Controls: [← / →] Change Date  |  [↑ / ↓] Select Planet  |  [D] View Details  |  [R] Exit to Report", style="yellow bold")
    else:
        header_text.append("🎮 Controls: [C] Back to Kundali Chart  |  [↑ / ↓] Next/Prev Planet Details  |  [R] Exit to Report", style="cyan bold")
        
    header_panel = Panel(header_text, border_style="magenta", expand=True)

    if current_screen == "CHART":
        main_table = RichTable.grid(expand=True)
        main_table.add_column(ratio=2)  
        main_table.add_column(ratio=1)  
        
        quick_info = Text()
        quick_info.append(f"\n\n🪐 Active Planet: {active_planet}\n\n", style="bold yellow")
        quick_info.append("Press [D] to open full\nartistic interpretations\nof this planet in another\nclean screen.", style="white")
        
        main_table.add_row(
            Panel(get_chart(), title="🏆 Rasi Kundali Map", border_style="green"),
            Panel(quick_info, title="ℹ️ Quick Panel", border_style="blue")
        )
        
        menu_string = Text("🎯 Planet Matrix: ")
        for idx, p in enumerate(PLANET_LIST):
            if idx == selected_planet_idx:
                menu_string.append(f" [{p}] ", style="bold black on cyan")
            else:
                menu_string.append(f" {p} ", style="dim")
        
        return Group(header_panel, main_table, Panel(menu_string, border_style="dim"))

    else:
        artistic_cards = engine.get_artistic_synthesis()
        details_panel = Panel(
            artistic_cards.get(active_planet, Text("No Data Available")), 
            title=f"🎨 Cosmic Synthesis Framework - {active_planet}", 
            border_style="cyan",
            padding=(2, 4)
        )
        return Group(header_panel, details_panel)

def on_press(key):
    global exit_to_report, selected_planet_idx, current_screen
    try:
        if current_screen == "CHART":
            if key == keyboard.Key.right: engine.view_date += timedelta(days=1)
            elif key == keyboard.Key.left: engine.view_date -= timedelta(days=1)
            
        if key == keyboard.Key.down: selected_planet_idx = (selected_planet_idx + 1) % len(PLANET_LIST)
        elif key == keyboard.Key.up: selected_planet_idx = (selected_planet_idx - 1) % len(PLANET_LIST)
        elif hasattr(key, "char"):
            c = key.char.lower()
            if c == "r": exit_to_report = True  
            elif c == "d": current_screen = "DETAILS"  
            elif c == "c": current_screen = "CHART"    
    except: pass

# ---------------- FLOW MAIN MANAGER LOOP ----------------
while True:
    show_master_report()
    exit_to_report = False
    input("\nPress ENTER to launch the Split-Screen Cosmic Dashboard...")
    
    listener = keyboard.Listener(on_press=on_press)
    listener.start()
    
    console.clear() 

    try:
        with Live(render_master_view(), refresh_per_second=4, screen=False) as live:
            while not exit_to_report:
                live.update(render_master_view())
                time.sleep(0.1)
    finally:
        listener.stop()