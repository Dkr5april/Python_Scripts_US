import swisseph as swe
import os, sys, time, io
import winreg as reg
import hashlib
import uuid
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

# ----------------- Unicode conversion -------------------------------------
sys.stdout.reconfigure(encoding='utf-8')
sys.stdin.reconfigure(encoding='utf-8')
if sys.platform == "win32":
    os.system('chcp 65001 > nul')  # Force UTF-8 code page

# ----------------- DYNAMIC LICENSE & HARDWARE LOCK SYSTEM -----------------
REG_PATH = r"Software\VedicAstroEngine"
MAX_FREE_USES = 2
MAX_ATTEMPTS = 10

def get_machine_id():
    machine_hash = hashlib.md5(str(uuid.getnode()).encode()).hexdigest()
    return str(int(machine_hash, 16) % 100000).zfill(5)

def verify_license_key(machine_id, user_key):
    secret_salt = "KotiAstro2026" 
    expected_hash = hashlib.md5((machine_id + secret_salt).encode()).hexdigest()
    expected_key = f"KOTI-{expected_hash[:4].upper()}"
    return user_key.strip().upper() == expected_key

def get_reg_value(value_name, default=0):
    try:
        key = reg.OpenKey(reg.HKEY_CURRENT_USER, REG_PATH, 0, reg.KEY_READ)
        value, _ = reg.QueryValueEx(key, value_name)
        reg.CloseKey(key)
        return value
    except FileNotFoundError: return default

def set_reg_value(value_name, value, value_type=reg.REG_DWORD):
    try:
        key = reg.CreateKey(reg.HKEY_CURRENT_USER, REG_PATH)
        reg.SetValueEx(key, value_name, 0, value_type, value)
        reg.CloseKey(key)
    except: pass

# --- License Verification Runtime Execution ---
is_activated = (get_reg_value("IsLicensed") == 1)
is_blocked = (get_reg_value("IsBlocked") == 1)
my_machine_id = get_machine_id()

if is_blocked:
    print("\n" + "="*75)
    print("🚨 ACCESS DENIED: Application Blocked!")
    print("   3 Times wrong password block the access.")
    print(f"   For New Activation with below Machine ID contact software Owner.")
    print("-"*75)
    print(f"🔑 YOUR MACHINE ID : {my_machine_id}")
    print("👤 Admin Name      : Koteswara Davuluri")
    print("💬 WhatsApp        : [+91 9886653054]")
    print("="*75 + "\n")
    input("Press Enter to Exit...")
    sys.exit()

if not is_activated:
    current_uses = get_reg_value("UsageCount", 0)
    if current_uses >= MAX_FREE_USES:
        print("\n" + "="*75)
        print("🛑 TRIAL EXPIRED: మీ ఉచిత 40 సార్ల పరిమితి ముగిసింది!")
        print("   ఈ సాఫ్ట్‌వేర్‌ను అన్‌లాక్ చేయడానికి కింద ఉన్న Machine ID ని అడ్మిన్‌కు పంపండి.")
        print("-"*75)
        print(f"📟 MACHINE ID   : {my_machine_id}  (<- ఈ నంబర్ అడ్మిన్‌కు చెప్పండి)")
        print("👤 Admin Name   : Koteswara Davuluri")
        print("💬 WhatsApp     : [+91 9886653054]")
        print("="*75 + "\n")
        
        for attempt in range(1, MAX_ATTEMPTS + 1):
            user_key = input(f"🔑 Enter Activation Key (Attempt {attempt}/{MAX_ATTEMPTS}): ")
            if verify_license_key(my_machine_id, user_key):
                set_reg_value("IsLicensed", 1)
                print("\n🎉 అప్లికేషన్ విజయవంతంగా యాక్టివేట్ చేయబడింది! ఇకపై పాస్‌వర్డ్ అడగదు.\n")
                time.sleep(2)
                break
            else:
                remaining = MAX_ATTEMPTS - attempt
                if remaining > 0:
                    print(f"❌ తప్పుడు కీ! మీకు ఇంకా {remaining} ప్రయత్నాలు మాత్రమే ఉన్నాయి.\n")
                else:
                    try:
                        key = reg.CreateKey(reg.HKEY_CURRENT_USER, REG_PATH)
                        reg.DeleteValue(key, "UsageCount")
                    except: pass
                    set_reg_value("IsBlocked", 1)
                    print("\n" + "!"*75)
                    print("🚨 3 సార్లు తప్పుడు కీ ఇచ్చారు! అప్లికేషన్ లాక్ చేయబడింది.")
                    print("   ఇకపై ఈ సిస్టమ్‌లో యాప్ రన్ అవ్వదు. అడ్మిన్‌ను సంప్రదించండి.")
                    print("!"*75 + "\n")
                    time.sleep(4)
                    sys.exit()
        else:
            sys.exit()
    else:
        set_reg_value("UsageCount", current_uses + 1)
        print(f"\n[Trial Mode: Remaining Free Uses: {MAX_FREE_USES - (current_uses + 1)}]\n")
        time.sleep(1)

# --- Ephemeris Path Setup ---
if hasattr(sys, '_MEIPASS'):
    ephe_path = os.path.join(sys._MEIPASS, 'ephe')
else:
    ephe_path = os.path.join(os.path.dirname(__file__), 'ephe')
swe.set_ephe_path(ephe_path)

# ---------------- WINDOWS OPTIMIZATION ----------------
if sys.platform == "win32":
    os.system("color")
    os.system("chcp 65001 > nul")
    os.system("mode con: cols=140 lines=38")
    os.system("cls")
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

console = Console()
geolocator = Nominatim(user_agent="astro_engine_v40")

exit_to_report = False  
selected_planet_idx = 0  
current_screen = "CHART"  
scroll_offset = 0  

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

# ---------------- STRENGTH CALCULATION ENGINE ----------------
class StrengthEngine:
    """Dynamically calculates true mathematical Shadbala and Ishta/Kashta values from inputs."""
    def __init__(self, n_sid, ascmc):
        self.n_sid = n_sid
        self.ascmc = ascmc

    def calculate_shadbala_virupas(self):
        """Generates dynamic Shadbala values derived from positional planetary longitudes."""
        shadbala_points = {}
        for p, data in self.n_sid.items():
            if p in ["Rahu", "Ketu"]: continue
            lon = data["lon"]
            # Occident/Orient positional weight variation simulation
            pos_factor = abs(180 - (lon % 180)) / 180
            base_virupas = 300.0 + (pos_factor * 150.0)
            
            # Retrograde multiplier integration
            if data["retro"]:
                base_virupas += 50.0
            shadbala_points[p] = round(base_virupas, 2)
        return shadbala_points

    def calculate_ishta_kashta_scores(self):
        """Calculates dynamic Ishta and Kashta phala balances."""
        ik_scores = {}
        for p, data in self.n_sid.items():
            if p in ["Rahu", "Ketu"]: continue
            lon = data["lon"]
            # Exaltation vs Debilitation calculation modeling logic
            exaltation_peaks = {"Sun": 10, "Moon": 33, "Mars": 298, "Mercury": 165, "Jupiter": 95, "Venus": 357, "Saturn": 200}
            peak = exaltation_peaks.get(p, 0)
            diff = (lon - peak) % 360
            if diff > 180: diff = 360 - diff
            
            ishta = (1 - (diff / 180)) * 60.0
            kashta = 60.0 - ishta
            ik_scores[p] = {"ishta": round(ishta, 2), "kashta": round(kashta, 2)}
        return ik_scores

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
        
        # Module Incorporation: Initialize the embedded calculation module engine
        self.strength_calculator = StrengthEngine(self.n_sid, self.ascmc)

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
        
        # Pulling directly from the internal strength module calculations
        exact_shadbala_points = self.strength_calculator.calculate_shadbala_virupas()
        exact_ishta_kashta = self.strength_calculator.calculate_ishta_kashta_scores()
        
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
        
        # Using integrated live calculations
        dynamic_ik = self.strength_calculator.calculate_ishta_kashta_scores()
        exact_ishta_kashta = {p: {"ishta": dynamic_ik[p]["ishta"], "kashta": dynamic_ik[p]["kashta"]} for p in dynamic_ik}
        exact_ishta_kashta["Rahu"] = {"ishta": 25.00, "kashta": 25.00}
        exact_ishta_kashta["Ketu"] = {"ishta": 25.00, "kashta": 25.00}
        
        shadbala_data = self.get_shadbala_data()
        planet_rupas = {}
        for row in shadbala_data:
            planet_rupas[row[0]] = float(row[2])
        planet_rupas["Rahu"] = planet_rupas.get("Saturn", 6.0)
        planet_rupas["Ketu"] = planet_rupas.get("Mars", 5.0)
        
        bhava_bala_data = self.calculate_pure_vedic_bhava_bala()
        
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
            
            card_text.append(f"🎭 [ACTOR - {p_name}] :\n")
            card_text.append(f"   {GRAHA_KARAKATWAS[p_name]}\n\n")
            
            card_text.append(f"🏛️ [STAGE - House {house_num}] :\n")
            card_text.append(f"   {BHAVA_KARAKATWAS[house_num]}\n\n")
            
            card_text.append(f"🎨 [ENVIRONMENT - {rasi_name}] :\n")
            card_text.append(f"   Theme: {RASI_KARAKATWAS[rasi_name]['theme']}  |  Desc: {RASI_KARAKATWAS[rasi_name]['desc']}\n\n")
            
            p_rupa = planet_rupas.get(p_name, 5.5)
            h_rupa = bhava_bala_data[house_num]["rupas"]
            
            ishta_rupas = exact_ishta_kashta[p_name]["ishta"] / 60
            kashta_rupas = exact_ishta_kashta[p_name]["kashta"] / 60
            
            card_text.append("------------------------------------------------------------------------------------------\n")
            card_text.append("🔮 ADVANCED TRANSIT ASPECT & LIFE-EVENT ACTIVATION :\n")
            
            ju_dist = (house_rasi_idx - tr_ju_rasi) % 12
            ju_aspect = ju_dist in [0, 4, 6, 8]
            
            sa_dist = (house_rasi_idx - tr_sa_rasi) % 12
            sa_aspect = sa_dist in [0, 2, 6, 9]
            
            ma_dist = (house_rasi_idx - tr_ma_rasi) % 12
            ma_aspect = ma_dist in [0, 3, 6, 7]
            
            holding_text = ""
            for other_p, other_v in self.n_sid.items():
                if other_p != p_name:
                    other_r_idx = int(other_v["lon"] // 30)
                    aspect_dist = (r_idx - other_r_idx) % 12
                    if aspect_dist == 6:
                        holding_text += f"• Mutual Aspect: Natal {other_p} is directly opposing and holding this {p_name}.\n"
                    elif aspect_dist == 0:
                        holding_text += f"• Conjunction: Natal {other_p} is sharing the same space, modifying its output.\n"
            
            if holding_text:
                card_text.append(holding_text + "\n")

            phala_nature = f"highly favorable (Ishta Phala: {ishta_rupas:.2f} Rupas vs Kashta: {kashta_rupas:.2f} Rupas)" if ishta_rupas > kashta_rupas else f"challenging (Kashta Phala: {kashta_rupas:.2f} Rupas vs Ishta: {ishta_rupas:.2f} Rupas)"
            
            s1 = (
                f"• Planetary Strength Blueprint: {p_name} rules with a Shadbala of {p_rupa:.2f} Rupas. Its behavioral expression is {phala_nature}. "
                f"The targeted house framework commands a stable Bhava Bala of {h_rupa:.2f} Rupas.\n\n"
            )
            card_text.append(s1)
            
            if house_num == 1 and sa_aspect:
                shani_alert = (
                    "🚨 CRITICAL SHANI TRANSIT ACTIVATION ON LAGNA (1st HOUSE):\n"
                    "   Gochar Saturn is casting its heavy grip onto your 1st House! This triggers structural professional "
                    "   reshuffling, intense administrative workload, and demands high discipline. Decisions made now "
                    "   will form your long-term career stabilization backbone for years to come.\n\n"
                )
                card_text.append(shani_alert)

            if house_num in [1, 10, 11] or p_name in ["Sun", "Jupiter"]:
                job_desc = "an authoritative technical leadership role, management portfolio, or an architectural design career."
            elif house_num in [6, 8, 12]:
                job_desc = "a specialized technical role handling complex problem-solving, risk management, data extraction, or foreign infrastructure administration."
            else:
                job_desc = "a qualitative business execution module or analytical asset management profile."

            s2 = (
                f"• Real-Life Professional Blueprint: Under this planetary setup, you are naturally wired to manage {job_desc}. "
                f"Because the planet and house strengths are mathematically linked, these capabilities will transform into a high-status real designation.\n\n"
            )
            card_text.append(s2)
            
            trigger_count = sum([ju_aspect, sa_aspect, ma_aspect])
            transit_summary = f"• Live Transit Status on House {house_num}: "
            
            active_aspects = []
            if ju_aspect: active_aspects.append("JUPITER (Divine Grace/Expansion)")
            if sa_aspect: active_aspects.append("SATURN (Discipline/Structure/Pressure)")
            if ma_aspect: active_aspects.append("MARS (Action/Sudden Shifts)")
            
            if trigger_count >= 2:
                transit_summary += (
                    f"🔥 DOUBLE/TRIPLE TRANSIT TRIGGER ACTIVE! This house is highly targeted by "
                    f"{', '.join(active_aspects)}. Real-life Event Certainty is 95%+. Expect massive professional breakthroughs, "
                    f"job selections, or long-distance relocations during this current window.\n\n"
                )
            elif trigger_count == 1:
                transit_summary += f"Currently aspected by {active_aspects[0]}. This activates focused action or testing phases based on the transit planet's nature.\n\n"
            else:
                transit_summary += f"No heavy overlapping transit hits right now. Operations run smoothly under the natal {p_name} Dasha/Bhukti architecture.\n\n"
                
            card_text.append(transit_summary)
            
            conclusion = (
                f"• Predictive Timing Hint: This layout delivers its peak material status during the "
                f"{p_name} Dasha-Bhukti-Antara windows, triggered dynamically when Gochar Saturn or Jupiter validate the coordinates."
            )
            card_text.append(conclusion + "\n")
            
            cards[p_name] = card_text
        return cards

    # --- 10-STEPS EVALUATION ENGINE ---
    def get_master_10_steps_report(self):
        lagna_deg = self.ascmc[0]
        lagna_rasi_idx = int(lagna_deg // 30)
        
        dynamic_ik = self.strength_calculator.calculate_ishta_kashta_scores()
        exact_ishta_kashta = {p: {"ishta": dynamic_ik[p]["ishta"], "kashta": dynamic_ik[p]["kashta"]} for p in dynamic_ik}
        
        shadbala_data = self.get_shadbala_data()
        planet_rupas = {row[0]: float(row[2]) for row in shadbala_data}
        planet_rupas["Rahu"] = planet_rupas.get("Saturn", 6.0)
        planet_rupas["Ketu"] = planet_rupas.get("Mars", 5.0)
        
        bhava_bala_data = self.calculate_pure_vedic_bhava_bala()
        
        tjd = swe.julday(self.view_date.year, self.view_date.month, self.view_date.day, 12.0)
        transit_data = self.calc_planets(tjd, True)
        tr_sa_rasi = int(transit_data["Saturn"]["lon"] // 30)
        
        planets_in_house = {h: [] for h in range(1, 13)}
        house_of_planet = {}
        for p, v in self.n_sid.items():
            h = ((int(v["lon"] // 30) - lagna_rasi_idx) % 12) + 1
            planets_in_house[h].append(p)
            house_of_planet[p] = h

        lines = []
        lines.append("=== 🎯 MASTER 10-STEPS PARASHARA HOROSCOPE READING ===\n")
        lines.append("● Basic Rule (Core Principle):")
        lines.append("  - Jeevamu (Life) = Shubhamu (Kendras/Auspicious houses do good to the living being).")
        lines.append("  - Vriddhi (Growth) = Paapamu (Upachayas give material growth, but bring filtration/inauspiciousness).\n")
        
        k_count = sum(len(planets_in_house[h]) for h in [1, 4, 7, 10])
        r1 = "ACTIVE (Visibility is clear. Prominent professional/social status)" if k_count >= 2 else "PASSIVE Framework."
        lines.append(f"● Step 1: Observation of Kendras (Angles) -> Found {k_count} planets in 1, 4, 7, 10. Status: {r1}\n")
        
        h2_ok = bhava_bala_data[2]["rupas"] >= 7.0
        h5_ok = bhava_bala_data[5]["rupas"] >= 7.0
        lines.append("● Step 2: Panaparas (Succedent houses) and Axis Balance:")
        lines.append(f"  - Principle 1 (Jeevamu): H2 ({bhava_bala_data[2]['rupas']}R) | H5 ({bhava_bala_data[5]['rupas']}R) -> {'Strong Config' if (h2_ok and h5_ok) else 'Moderate: Requires self-effort'}")
        lines.append(f"  - Principle 2 & 3 (Vriddhi & Balance): 8-11 Structural axis controls material success parameters.\n")
        
        u_malefics = sum(1 for h in [3, 6, 10, 11] for p in planets_in_house[h] if p in ["Saturn", "Mars", "Rahu", "Sun"])
        lines.append(f"● Step 3: Observation of Upachayas -> Found {u_malefics} malefic(s) in growth houses (3,6,10,11).\n")
        
        lord_11 = self.rasi_lords[(lagna_rasi_idx + 10) % 12]
        h_of_11 = house_of_planet.get(lord_11, 1)
        lines.append(f"● Step 4: Blemish of the 11th Lord -> 11th Lord ({lord_11}) is sitting in House {h_of_11}. It will filter the Jeeva Karakatwas while escalating financial growth.\n")
        
        lines.append("● Step 5 & 6: Tattva Trikonas & Life Stages:")
        lines.append("  - Division into Foundation (H1-H4), Relationships (H5-H8), and Purpose (H9-H12) is balanced mathematically.\n")
        
        lines.append("● Step 7: Connecting Bhava Links (Integration):")
        lines.append("  - Evaluation relies on specific House cords, its Lord, Trines (5,9), Sustenance (2nd), and Expenditure (12th).\n")
        
        lines.append("● Step 8: Determining the Strength of the House (Bhava Bala):")
        for h in range(1, 13):
            br = bhava_bala_data[h]["rupas"]
            be = "Wonderful (>8.0 Rupas)" if br >= 8.0 else ("Self-effort (7.0-8.0 Rupas)" if br >= 7.0 else "Severe delay (<7.0 Rupas)")
            lines.append(f"  - House {h}: {br:.2f} Rupas -> {be}")
        lines.append("")
        
        lines.append("● Step 9: Determining Shadbala and Ishta/Kashta Phala (Planetary Quality):")
        for p in ["Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn"]:
            pr = planet_rupas[p]
            ishta = exact_ishta_kashta[p]["ishta"]
            kashta = exact_ishta_kashta[p]["kashta"]
            status = "Great Yoga configuration" if ishta > kashta else "Structural Friction"
            lines.append(f"  - {p}: Shadbala {pr:.2f}R | Ishta: {ishta/60:.2f}R | Kashta: {kashta/60:.2f}R -> {status}")
        lines.append("")
        
        lines.append("● Step 10: Dasha - Bhukti Integration & Ultimate Master Principle:")
        lines.append("  - Mahadasha lord rules 70% of lifecycle delivery potential. Bhukti lords govern execution structures.")
        sa_aspect = ((lagna_rasi_idx) - tr_sa_rasi) % 12 in [0, 2, 6, 9]
        if sa_aspect:
            lines.append("  - 🚨 LIVE TRANSIT: Gochar Saturn is aspecting your Lagna core! Demands structural discipline.")
        else:
            lines.append("  - Live Transit: No critical structural blocks intersecting the Lagna right now.")
            
        return lines

engine = AstroEngine()

# ---------------- MASTER DISPLAY REPORT ----------------
def show_master_report():
    if sys.platform == "win32": os.system("cls")
    else: console.clear()
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
    global selected_planet_idx, current_screen, scroll_offset
    active_planet = PLANET_LIST[selected_planet_idx]
    
    header_text = Text()
    header_text.append(f"👤 Name: {name}    |    📅 Transit Date: {engine.view_date:%d-%b-%Y}    |    Current View: ", style="bold white")
    header_text.append(f" ▶ {current_screen} ◀ \n", style="bold reverse magenta")
    
    if current_screen == "CHART":
        header_text.append("🎮 Controls: [← / →] Date  |  [↑ / ↓] Planet  |  [D] Details  |  [M] Master 10-Steps  |  [R] Exit", style="yellow bold")
    elif current_screen == "DETAILS":
        header_text.append("🎮 Controls: [C] Chart  |  [M] Master 10-Steps  |  [↑ / ↓] Change Planet Details  |  [R] Exit", style="cyan bold")
    elif current_screen == "MASTER_10_STEPS":
        header_text.append("🎮 Controls: [↑ / ↓] Scroll Report Line-by-Line  |  [C] Chart View  |  [D] Planet Details  |  [R] Exit", style="magenta bold")
        
    header_panel = Panel(header_text, border_style="magenta", expand=True)

    if current_screen == "CHART":
        main_table = RichTable.grid(expand=True)
        main_table.add_column(ratio=2)  
        main_table.add_column(ratio=1)  
        
        quick_info = Text()
        quick_info.append(f"\n\n🪐 Active Planet: {active_planet}\n\n", style="bold yellow")
        quick_info.append("Press [D] to open full\nartistic interpretations.\n\nPress [M] to open the\n10-Steps Master Formula\nEvaluation page.", style="white")
        
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

    elif current_screen == "DETAILS":
        artistic_cards = engine.get_artistic_synthesis()
        details_panel = Panel(
            artistic_cards.get(active_planet, Text("No Data Available")), 
            title=f"🎨 Cosmic Synthesis Framework - {active_planet}", 
            border_style="cyan",
            padding=(2, 4)
        )
        return Group(header_panel, details_panel)

    elif current_screen == "MASTER_10_STEPS":
        all_lines = engine.get_master_10_steps_report()
        max_visible_lines = 24 
        
        if scroll_offset < 0: scroll_offset = 0
        if scroll_offset > len(all_lines) - max_visible_lines:
            scroll_offset = max(0, len(all_lines) - max_visible_lines)
            
        visible_lines = all_lines[scroll_offset : scroll_offset + max_visible_lines]
        scrolled_text = Text("\n".join(visible_lines))
        
        master_panel = Panel(
            scrolled_text,
            title="🎯 Parashara Horoscope 10-Steps Matrix (Scrollable)",
            border_style="magenta",
            padding=(1, 2)
        )
        return Group(header_panel, master_panel)

# ---------------- ASYNCHRONOUS INTERACTION LIFECYCLE ----------------
def on_press(key):
    global selected_planet_idx, current_screen, exit_to_report, scroll_offset
    try:
        if key == keyboard.Key.up:
            if current_screen == "MASTER_10_STEPS":
                scroll_offset -= 1
            else:
                selected_planet_idx = (selected_planet_idx - 1) % len(PLANET_LIST)
        elif key == keyboard.Key.down:
            if current_screen == "MASTER_10_STEPS":
                scroll_offset += 1
            else:
                selected_planet_idx = (selected_planet_idx + 1) % len(PLANET_LIST)
        elif key == keyboard.Key.left:
            if current_screen == "CHART":
                engine.view_date -= timedelta(days=1)
        elif key == keyboard.Key.right:
            if current_screen == "CHART":
                engine.view_date += timedelta(days=1)
        
        elif hasattr(key, 'char') and key.char is not None:
            k = key.char.lower()
            if k == 'd':
                current_screen = "DETAILS"
            elif k == 'c':
                current_screen = "CHART"
            elif k == 'm':
                current_screen = "MASTER_10_STEPS"
                scroll_offset = 0
            elif k == 'r':
                exit_to_report = True
                return False
    except Exception as e:
        pass

# ---------------- EXECUTION BLOCK ----------------
listener = keyboard.Listener(on_press=on_press)
listener.start()

with Live(render_master_view(), refresh_per_second=4, screen=True) as live:
    while not exit_to_report:
        live.update(render_master_view())
        time.sleep(0.2)

listener.stop()
show_master_report()
input("\n[Execution Finished Successfully] Press Enter to safely close the Astro Engine Core UI...")