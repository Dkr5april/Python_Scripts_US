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
    os.system("mode con: cols=140 lines=35")
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

swe.set_ephe_path("./ephe")
console = Console()
geolocator = Nominatim(user_agent="astro_engine_v39")

exit_to_report = False  
selected_planet_idx = 0  
current_screen = "CHART"  # టోగుల్ స్టేట్ మేనేజ్‌మెంట్ ("CHART" లేదా "DETAILS")

# ---------------- INPUT MECHANISM ----------------
console.clear()
console.print("[bold magenta]=== ASTRO ENGINE V39 (FIXED MULTI-SCREEN) ===[/bold magenta]\n")

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
    "Sun": "ఆత్మకారకుడు, తండ్రి, అధికారం, ప్రభుత్వ గౌరవం",
    "Moon": "మనఃకారకుడు, తల్లి, భావోద్వేగాలు, మానసిక ప్రశాంతత",
    "Mars": "ధైర్యకారకుడు, సోదరులు, భూమి/రియల్ ఎస్టేట్, సాంకేతికత",
    "Mercury": "బుద్ధికారకుడు, వాక్కు, వ్యాపారం, విద్య, జ్యోతిష్య నాలెడ్జ్",
    "Jupiter": "జ్ఞానకారకుడు, సంపద, దైవభక్తి, గురువులు, అదృష్టం",
    "Venus": "కళాకారకుడు, వివాహం/భార్య, లగ్జరీ వాహనాలు, సుఖాలు",
    "Saturn": "ఆయుష్కారకుడు, కష్టపడే తత్వం, క్రమశిక్షణ, ఆలస్యాలు",
    "Rahu": "భ్రమలు, విదేశీ అంశాలు, సాంకేతికత, అకస్మాత్తు మార్పులు",
    "Ketu": "మోక్షకారకుడు, వైరాగ్యం, ఆధ్యాత్మికత, గూఢ శాస్త్రాలు"
}

BHAVA_KARAKATWAS = {
    1: "తను భావం (వ్యక్తిత్వం, ఆరోగ్యం, రూపం, జీవన ఆరంభం)",
    2: "ధన భావం (ఆర్థిక స్థితి, వాక్కు, కుటుంబం, స్థిరాస్తులు)",
    3: "భ్రాతృ భావం (ధైర్యం, చిన్న ప్రయాణాలు, కమ్యూనికేషన్)",
    4: "మాతృ భావం (తల్లి, గృహం, వాహన సుఖం, మనఃశాంతి)",
    5: "పుత్ర భావం (సంతానం, పూర్వపుణ్యం, తెలివితేటలు, షేర్ మార్కెట్)",
    6: "శత్రు భావం (రోగాలు, రుణాలు, శత్రుత్వాలు, దైనందిన ఉద్యోగం)",
    7: "కళత్ర భావం (భార్య/భర్త, వివాహ బంధం, పబ్లిక్ ఇమేజ్)",
    8: "ఆయు భావం (ఆయుష్షు, అకస్మాత్తు సంఘటనలు, పరిశోధన)",
    9: "భాగ్య భావం (తండ్రి, సుదూర ప్రయాణాలు, ఉన్నత విద్య, అదృష్టం)",
    10: "కర్మ భావం (వృత్తి, కీర్తి ప్రతిష్టలు, సమాజంలో హోదా)",
    11: "లాభ భావం (ఆదాయం, కోరికల నెరవేరుట, స్నేహితులు)",
    12: "వ్యయ భావం (ఖర్చులు, మోక్షం, విదేశీ ప్రయాణాలు, ఏకాంతం)"
}

RASI_KARAKATWAS = {
    "Mesha": {"theme": "అగ్ని | చర", "desc": "నాయకత్వ లక్షణాలు, వేగం, మొండి పట్టుదల"},
    "Vrishabha": {"theme": "భూ | స్థిర", "desc": "స్థిరత్వం, కళాభిరుచి, సంపద సేకరణ"},
    "Mithuna": {"theme": "వాయు | ద్విస్వభావ", "desc": "విశ్లేషణ, చతురత, వాణిజ్య నైపుణ్యం"},
    "Karkataka": {"theme": "జల | చర", "desc": "భావోద్వేగాలు, దయాగుణం, అంతర్జ్ఞానం"},
    "Simha": {"theme": "అగ్ని | స్థిర", "desc": "రాజసం, అథారిటీ, ఉదార స్వభావం"},
    "Kanya": {"theme": "భూ | ద్విస్వభావ", "desc": "పర్ఫెక్షనిజం, సేవా దృక్పథం, సూక్ష్మ పరిశీలన"},
    "Thula": {"theme": "వాయు | చర", "desc": "సమతుల్యత, దౌత్యం, వ్యాపార దృష్టి"},
    "Vrischika": {"theme": "జల | స్థిర", "desc": "రహస్యాలు, లోతైన పట్టుదల, ట్రాన్స్‌ఫార్మేషన్"},
    "Dhanus": {"theme": "అగ్ని | ద్విస్వభావ", "desc": "తత్వజ్ఞానం, ఆశావాదం, ధర్మ రక్షణ"},
    "Makara": {"theme": "భూ | చర", "desc": "ఆంబిషన్, క్రమశిక్షణ, ప్రాక్టికల్ లైఫ్"},
    "Kumbha": {"theme": "వాయు | స్థిర", "desc": "సామాజిక స్పృహ, ఆవిష్కరణలు, నెట్‌వర్కింగ్"},
    "Meena": {"theme": "జల | ద్విస్వభావ", "desc": "ఆధ్యాత్మికత, ఊహాశక్తి, వైరాగ్య భావన"}
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
        cards = {}
        for p_name, v in self.n_sid.items():
            r_idx = int(v["lon"] // 30)
            rasi_name = self.rasi_names[r_idx]
            house_num = ((r_idx - lagna_rasi_idx) % 12) + 1
            
            card_text = Text()
            
            # 1. నటుడు (Planet)
            card_text.append(f"🎭  [ న టు డు   -   {p_name} ] :\n", style="bold cyan")
            spaced_graha = " ".join(list(GRAHA_KARAKATWAS[p_name])) # ఆటోమేటిక్ స్పేసింగ్ ట్వీక్
            card_text.append(f"      {spaced_graha}\n\n")
            
            # 2. వేదిక (House)
            card_text.append(f"🏛️  [ వే ది క   -   H o u s e   {house_num} ] :\n", style="bold yellow")
            spaced_bhava = " ".join(list(BHAVA_KARAKATWAS[house_num])) # ఆటోమేటిక్ స్పేసింగ్ ట్వీక్
            card_text.append(f"      {spaced_bhava}\n\n")
            
            # 3. వాతావరణం (Rasi)
            card_text.append(f"🎨  [ వా తా వ ర ణం   -   {rasi_name} ] :\n", style="bold green")
            spaced_theme = " ".join(list(RASI_KARAKATWAS[rasi_name]['theme']))
            spaced_desc = " ".join(list(RASI_KARAKATWAS[rasi_name]['desc']))
            card_text.append(f"      {spaced_theme}   ->   {spaced_desc}\n")
            
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
    
    # 1. హెడర్ ప్యానెల్ (డేట్ మరియు అన్నీ ఇక్కడ స్పష్టంగా కనిపిస్తాయి)
    header_text = Text()
    header_text.append(f"👤 Name: {name}  |  📅 Transit Date: {engine.view_date:%d-%b-%Y}  |  Selected Planet: ", style="bold white")
    header_text.append(f"▶ {active_planet} ◀\n", style="bold reverse magenta")
    
    if current_screen == "CHART":
        header_text.append("🎮 Controls: [← / →] Change Date | [↑ / ↓] Select Planet | [D] View Planet Details | [R] Exit", style="yellow bold")
    else:
        header_text.append("🎮 Controls: [C] Back to Kundali Chart | [↑ / ↓] Change Planet Details | [R] Exit", style="cyan bold")
        
    header_panel = Panel(header_text, border_style="magenta", expand=True)

    # 2. స్క్రీన్ 1: కేవలం కుండలి చార్ట్ వ్యూ
    if current_screen == "CHART":
        main_table = RichTable.grid(expand=True)
        main_table.add_column(ratio=2)  
        main_table.add_column(ratio=1)  
        
        quick_info = Text()
        quick_info.append(f"\n\n🪐 Active Planet: {active_planet}\n\n", style="bold yellow")
        quick_info.append("Press [D] to open full\nartistic interpretations\nof this planet in another\nclean screen without grid blocks.", style="dim white")
        
        main_table.add_row(
            Panel(get_chart(), title="🏆 Rasi Kundali Map (Natal: Green | Transit: Red)", border_style="green"),
            Panel(quick_info, title="ℹ️ Quick Panel", border_style="blue")
        )
        
        menu_string = Text("🎯 Planet Matrix: ")
        for idx, p in enumerate(PLANET_LIST):
            if idx == selected_planet_idx:
                menu_string.append(f" [{p}] ", style="bold black on cyan")
            else:
                menu_string.append(f" {p} ", style="dim")
        
        return Group(header_panel, main_table, Panel(menu_string, border_style="dim"))

    # 3. స్క్రీన్ 2: కేవలం ప్లానెట్ కారకత్వాల వివరణ వ్యూ (No Chart)
    else:
        artistic_cards = engine.get_artistic_synthesis()
        details_panel = Panel(
            artistic_cards.get(active_planet, Text("నో డేటా")), 
            title=f"🎨 Cosmic Synthesis Framework - {active_planet} Comprehensive Insights", 
            border_style="cyan"
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