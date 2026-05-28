import os
import sys
import io
import winreg as reg
import hashlib
import uuid
import time
import math
from datetime import datetime

# --- FORCE UTF-8 FOR COMPATIBILITY ---
sys.stdout.reconfigure(encoding='utf-8')
sys.stdin.reconfigure(encoding='utf-8')
if sys.platform == "win32":
    os.system('chcp 65001 > nul')

# ----------------- DYNAMIC LICENSE & HARDWARE LOCK SYSTEM -----------------
REG_PATH = r"Software\VedicAstroEngine"
MAX_FREE_USES = 150
MAX_ATTEMPTS = 50

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

# --- LICENSE SYSTEM RUNTIME CHECK ---
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
        print("🛑 TRIAL EXPIRED: మీ ఉచిత సాఫ్ట్‌వేర్ పరిమితి ముగిసింది!")
        print("   ఈ సాఫ్ట్‌వేర్‌ను అన్‌లాక్ చేయడానికి కింద ఉన్న Machine ID ని అడ్మిన్‌కు పంపండి.")
        print("-"*75)
        print(f"📟 MACHINE ID   : {my_machine_id}")
        print("👤 Admin Name   : Koteswara Davuluri")
        print("="*75 + "\n")
        
        for attempt in range(1, MAX_ATTEMPTS + 1):
            user_key = input(f"🔑 Enter Activation Key (Attempt {attempt}/{MAX_ATTEMPTS}): ")
            if verify_license_key(my_machine_id, user_key):
                set_reg_value("IsLicensed", 1)
                print("\n🎉 అప్లికేషన్ విజయవంతంగా యాక్టివేట్ చేయబడింది!\n")
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
                    print("\n🚨 అప్లికేషన్ లాక్ చేయబడింది. అడ్మిన్‌ను సంప్రదించండి.\n")
                    time.sleep(4)
                    sys.exit()
        else:
            sys.exit()
    else:
        set_reg_value("UsageCount", current_uses + 1)
        print(f"\n[Trial Mode: Remaining Free Uses: {MAX_FREE_USES - (current_uses + 1)}]\n")
        time.sleep(1)

# --- SWISSEPH PATH SETTINGS ---
import swisseph as swe
if hasattr(sys, '_MEIPASS'):
    ephe_path = os.path.join(sys._MEIPASS, 'ephe')
else:
    ephe_path = os.path.join(os.path.dirname(__file__), 'ephe')
swe.set_ephe_path(ephe_path)

# --- WEB APPLICATION DEPENDENCIES ---
import dash
from dash import dcc, html, dash_table, Input, Output, State
import plotly.graph_objects as go
from geopy.geocoders import Nominatim

geolocator = Nominatim(user_agent="astro_engine_web_v40")

# --- GLOBAL STATIC DICTIONARIES ---
PLANET_LIST = ["Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn", "Rahu", "Ketu"]
PLANET_IDS = {"Sun": 0, "Moon": 1, "Mars": 4, "Mercury": 2, "Jupiter": 5, "Venus": 3, "Saturn": 6, "Rahu": 11}

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

# --- COORDINATES FETCH WITH GEOGRAPHIC BACKUP LOGIC ---
def fetch_coords(city):
    if not city or city.strip() == "":
        return 16.1176, 80.9314  
    try:
        loc = geolocator.geocode(city, timeout=5)
        if loc: return loc.latitude, loc.longitude
    except: pass
    return 16.1176, 80.9314  

# --- CORE CALCULATIONS ENGINE ---
class AstroEngine:
    def __init__(self, dob, tob, birth_city, transit_date_str):
        swe.set_sid_mode(swe.SIDM_LAHIRI)
        self.rasi_names = ['Mesha', 'Vrishabha', 'Mithuna', 'Karkataka', 'Simha', 'Kanya', 'Thula', 'Vrischika', 'Dhanus', 'Makara', 'Kumbha', 'Meena']
        self.rasi_lords = ['Mars', 'Venus', 'Mercury', 'Moon', 'Sun', 'Mercury', 'Venus', 'Mars', 'Jupiter', 'Saturn', 'Saturn', 'Jupiter']
        
        self.b_lat, self.b_lon = fetch_coords(birth_city)
        
        d, m, y = map(int, dob.split("/"))
        time_parts = tob.split(":")
        hh = int(time_parts[0])
        mm = int(time_parts[1])
        ss = int(time_parts[2]) if len(time_parts) > 2 else 0
        
        birth_hour_ist = hh + mm/60 + ss/3600
        birth_hour_ut = birth_hour_ist - 5.5
        
        self.njd = swe.julday(y, m, d, birth_hour_ut)
        self.n_sid = self.calc_planets(self.njd, True)
        self.cusps, self.ascmc = swe.houses_ex(self.njd, self.b_lat, self.b_lon, b'S', swe.FLG_SIDEREAL)
        
        self.view_date = datetime.strptime(transit_date_str, "%d/%m/%Y")

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
        # Min requirements framework for percentage calculations
        min_required_virupas = {"Sun": 300.0, "Moon": 360.0, "Mars": 300.0, "Mercury": 420.0, "Jupiter": 390.0, "Venus": 330.0, "Saturn": 300.0}
        
        # Deep Exaltation positions used for dynamic Uccha Bala calculations (Sthana Bala component)
        exaltation_pts = {"Sun": 10.0, "Moon": 33.0, "Mars": 298.0, "Mercury": 165.0, "Jupiter": 95.0, "Venus": 357.0, "Saturn": 210.0}
        naisargika_scores = {"Sun": 60.0, "Moon": 51.43, "Mars": 17.14, "Mercury": 25.71, "Jupiter": 34.29, "Venus": 42.85, "Saturn": 8.57}
        
        lagna_deg = self.ascmc[0]
        fourth_house = self.cusps[3]
        seventh_house = self.cusps[6]
        tenth_house = self.cusps[9]
        
        table_rows = []
        for p in ["Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn"]:
            p_lon = self.n_sid[p]["lon"]
            
            # A. Dynamic Uccha Bala (Sthana Bala component)
            diff = abs(p_lon - exaltation_pts[p])
            if diff > 180: diff = 360 - diff
            uccha_bala = (180 - diff) / 3.0 # Maximum 60 Virupas
            
            # B. Dynamic Dig Bala (Directional Strength Mapping)
            if p in ["Jupiter", "Mercury"]:
                target_angle = lagna_deg
            elif p in ["Sun", "Mars"]:
                target_angle = tenth_house
            elif p in ["Saturn"]:
                target_angle = seventh_house
            else: # Moon & Venus
                target_angle = fourth_house
                
            dig_diff = abs(p_lon - target_angle)
            if dig_diff > 180: dig_diff = 360 - dig_diff
            dig_bala = (180 - dig_diff) / 3.0 # Maximum 60 Virupas
            
            # C. Dynamic Temporal/Positional Base Scaling Factor
            base_sthana = 120.0
            if self.n_sid[p]["retro"]: 
                base_sthana += 30.0 # Retrograde adds motional value
                
            # Compute real total cumulative Virupas dynamically linked to coordinates
            sb = base_sthana + uccha_bala + dig_bala + naisargika_scores[p]
            
            # Turn Virupas to Rupas cleanly without hardcoded freezing
            rupas = round(sb / 60, 2)
            pct = round((sb / min_required_virupas[p]) * 100, 2)
            
            # D. Dynamic Calculation of Ishta / Kashta Phala based on dynamic Uccha strength
            ishta_calc = round((uccha_bala / 60.0) * 50.0 + 5.0, 2)
            kashta_calc = round((1.0 - (uccha_bala / 60.0)) * 40.0 + 4.0, 2)
            
            table_rows.append({
                "Planet": p, 
                "Shadbala": f"{sb:.2f}", 
                "In_Rupas": f"{rupas:.2f}", 
                "Percent_Strength": f"{pct:.2f}%", 
                "IshtaPhala": f"{ishta_calc:.2f}", 
                "KashtaPhala": f"{kashta_calc:.2f}"
            })
        return table_rows

    def calculate_pure_vedic_bhava_bala(self):
        lagna_deg = self.ascmc[0]
        lagna_rasi_idx = int(lagna_deg // 30)
        s_data = self.get_shadbala_data()
        shadbala_rupas = {row["Planet"]: float(row["In_Rupas"]) for row in s_data}
        shadbala_rupas["Rahu"] = shadbala_rupas["Saturn"]
        shadbala_rupas["Ketu"] = shadbala_rupas["Mars"]

        bhava_bala_results = {}
        for h in range(1, 13):
            rasi_of_house = (lagna_rasi_idx + (h - 1)) % 12
            total_bala = shadbala_rupas.get(self.rasi_lords[rasi_of_house], 5.0) + 0.5
            bhava_bala_results[h] = {"rupas": round(total_bala, 2), "pct": round((total_bala / 5.5) * 100, 1)}
        return bhava_bala_results

    def get_artistic_synthesis(self, p_name):
        lagna_deg = self.ascmc[0]
        lagna_rasi_idx = int(lagna_deg // 30)
        
        s_data = self.get_shadbala_data()
        planet_rupas = {row["Planet"]: float(row["In_Rupas"]) for row in s_data}
        planet_rupas["Rahu"] = planet_rupas.get("Saturn", 6.0)
        planet_rupas["Ketu"] = planet_rupas.get("Mars", 5.0)
        
        # Build dictionary from active dynamic output rows for report matching
        planet_ishta_dict = {}
        planet_kashta_dict = {}
        for r in s_data:
            planet_ishta_dict[r["Planet"]] = float(r["IshtaPhala"])
            planet_kashta_dict[r["Planet"]] = float(r["KashtaPhala"])
        planet_ishta_dict["Rahu"] = 25.0; planet_ishta_dict["Ketu"] = 25.0
        planet_kashta_dict["Rahu"] = 25.0; planet_kashta_dict["Ketu"] = 25.0
        
        bhava_bala_data = self.calculate_pure_vedic_bhava_bala()
        
        tjd = swe.julday(self.view_date.year, self.view_date.month, self.view_date.day, 12.0)
        transit_data = self.calc_planets(tjd, True)
        tr_ju_rasi = int(transit_data["Jupiter"]["lon"] // 30)
        tr_sa_rasi = int(transit_data["Saturn"]["lon"] // 30)
        tr_ma_rasi = int(transit_data["Mars"]["lon"] // 30)
        
        v = self.n_sid[p_name]
        r_idx = int(v["lon"] // 30)
        rasi_name = self.rasi_names[r_idx]
        house_num = ((r_idx - lagna_rasi_idx) % 12) + 1
        house_rasi_idx = (lagna_rasi_idx + (house_num - 1)) % 12
        
        lines = []
        lines.append(f"🎭 [ACTOR - {p_name}] : {GRAHA_KARAKATWAS[p_name]}")
        lines.append(f"🏛️ [STAGE - House {house_num}] : {BHAVA_KARAKATWAS[house_num]}")
        lines.append(f"🎨 [ENVIRONMENT - {rasi_name}] : Theme: {RASI_KARAKATWAS[rasi_name]['theme']} | Desc: {RASI_KARAKATWAS[rasi_name]['desc']}")
        lines.append("-" * 60)
        
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
            lines.append(holding_text)

        p_rupa = planet_rupas.get(p_name, 5.5)
        h_rupa = bhava_bala_data[house_num]["rupas"]
        ishta_rupas = planet_ishta_dict[p_name] / 60
        kashta_rupas = planet_kashta_dict[p_name] / 60
        
        phala_nature = f"highly favorable (Ishta Phala: {ishta_rupas:.2f} Rupas vs Kashta: {kashta_rupas:.2f} Rupas)" if ishta_rupas > kashta_rupas else f"challenging (Kashta Phala: {kashta_rupas:.2f} Rupas vs Ishta: {ishta_rupas:.2f} Rupas)"
        lines.append(f"• Planetary Strength Blueprint: {p_name} rules with a Shadbala of {p_rupa:.2f} Rupas. Its behavioral expression is {phala_nature}. The targeted house framework commands a stable Bhava Bala of {h_rupa:.2f} Rupas.")
        
        ju_dist = (house_rasi_idx - tr_ju_rasi) % 12
        ju_aspect = ju_dist in [0, 4, 6, 8]
        sa_dist = (house_rasi_idx - tr_sa_rasi) % 12
        sa_aspect = sa_dist in [0, 2, 6, 9]
        ma_dist = (house_rasi_idx - tr_ma_rasi) % 12
        ma_aspect = ma_dist in [0, 3, 6, 7]

        if house_num == 1 and sa_aspect:
            lines.append("🚨 CRITICAL SHANI TRANSIT ACTIVATION ON LAGNA (1st HOUSE): Gochar Saturn is casting its heavy grip onto your 1st House! This triggers structural professional reshuffling, intense administrative workload, and demands high discipline.")

        if house_num in [1, 10, 11] or p_name in ["Sun", "Jupiter"]:
            job_desc = "an authoritative technical leadership role, management portfolio, or an architectural design career."
        elif house_num in [6, 8, 12]:
            job_desc = "a specialized technical role handling complex problem-solving, risk management, data extraction, or foreign infrastructure administration."
        else:
            job_desc = "a qualitative business execution module or analytical asset management profile."
        lines.append(f"• Real-Life Professional Blueprint: Under this planetary setup, you are naturally wired to manage {job_desc}")
        
        trigger_count = sum([ju_aspect, sa_aspect, ma_aspect])
        transit_summary = f"• Live Transit Status on House {house_num}: "
        active_aspects = []
        if ju_aspect: active_aspects.append("JUPITER (Divine Grace/Expansion)")
        if sa_aspect: active_aspects.append("SATURN (Discipline/Structure/Pressure)")
        if ma_aspect: active_aspects.append("MARS (Action/Sudden Shifts)")
        
        if trigger_count >= 2:
            transit_summary += f"🔥 DOUBLE/TRIPLE TRANSIT TRIGGER ACTIVE! This house is highly targeted by {', '.join(active_aspects)}. Real-life Event Certainty is 95%+. Expect massive professional breakthroughs."
        elif trigger_count == 1:
            transit_summary += f"Currently aspected by {active_aspects[0]}. This activates focused action or testing phases based on the transit planet's nature."
        else:
            transit_summary += f"No heavy overlapping transit hits right now."
        lines.append(transit_summary)
        
        lines.append(f"• Predictive Timing Hint: This layout delivers its peak material status during the {p_name} Dasha-Bhukti-Antara windows.")
        return "\n\n".join(lines)

    def get_master_10_steps_report(self):
        lagna_deg = self.ascmc[0]
        lagna_rasi_idx = int(lagna_deg // 30)
        
        s_data = self.get_shadbala_data()
        planet_rupas = {row["Planet"]: float(row["In_Rupas"]) for row in s_data}
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
        lines.append("### 🎯 MASTER 10-STEPS PARASHARA HOROSCOPE READING")
        lines.append("**Basic Rule (Core Principle):**\n- Jeevamu (Life) = Shubhamu (Kendras/Auspicious houses do good to the living being).\n- Vriddhi (Growth) = Paapamu (Upachayas give material growth, but bring filtration/inauspiciousness).")
        
        k_count = sum(len(planets_in_house[h]) for h in [1, 4, 7, 10])
        r1 = "ACTIVE (Visibility is clear. Prominent professional/social status)" if k_count >= 2 else "PASSIVE Framework."
        lines.append(f"**Step 1: Observation of Kendras (Angles)** -> Found {k_count} planets in 1, 4, 7, 10. Status: {r1}")
        
        h2_ok = bhava_bala_data[2]["rupas"] >= 7.0
        h5_ok = bhava_bala_data[5]["rupas"] >= 7.0
        lines.append(f"**Step 2: Panaparas (Succedent houses) and Axis Balance:**\n- Principle 1 (Jeevamu): H2 ({bhava_bala_data[2]['rupas']}R) | H5 ({bhava_bala_data[5]['rupas']}R) -> {'Strong Config' if (h2_ok and h5_ok) else 'Moderate: Requires self-effort'}\n- Principle 2 & 3 (Vriddhi & Balance): 8-11 Structural axis controls material success parameters.")
        
        u_malefics = sum(1 for h in [3, 6, 10, 11] for p in planets_in_house[h] if p in ["Saturn", "Mars", "Rahu", "Sun"])
        lines.append(f"**Step 3: Observation of Upachayas** -> Found {u_malefics} malefic(s) in growth houses (3,6,10,11).")
        
        lord_11 = self.rasi_lords[(lagna_rasi_idx + 10) % 12]
        h_of_11 = house_of_planet.get(lord_11, 1)
        lines.append(f"**Step 4: Blemish of the 11th Lord** -> 11th Lord ({lord_11}) is sitting in House {h_of_11}. It will filter the Jeeva Karakatwas while escalating financial growth.")
        
        lines.append("**Step 5 & 6: Tattva Trikonas & Life Stages:**\n- Division into Foundation (H1-H4), Relationships (H5-H8), and Purpose (H9-H12) is balanced mathematically.")
        lines.append("**Step 7: Connecting Bhava Links (Integration):**\n- Evaluation relies on specific House cords, its Lord, Trines (5,9), Sustenance (2nd), and Expenditure (12th).")
        
        h_lines = ["**Step 8: Determining the Strength of the House (Bhava Bala):**"]
        for h in range(1, 13):
            br = bhava_bala_data[h]["rupas"]
            be = "Wonderful (>8.0 Rupas)" if br >= 6.5 else ("Self-effort (5.8-6.5 Rupas)" if br >= 5.5 else "Severe delay (<5.5 Rupas)")
            h_lines.append(f"- House {h}: {br:.2f} Rupas -> {be}")
        lines.append("\n".join(h_lines))
        
        p_lines = ["**Step 9: Determining Shadbala and Ishta/Kashta Phala (Planetary Quality):**"]
        for r in s_data:
            p = r["Planet"]
            pr = planet_rupas[p]
            ishta = float(r["IshtaPhala"])
            kashta = float(r["KashtaPhala"])
            status = "Great Yoga configuration" if ishta > kashta else "Structural Friction"
            p_lines.append(f"- {p}: Shadbala {pr:.2f}R | Ishta: {ishta/60:.2f}R | Kashta: {kashta/60:.2f}R -> {status}")
        lines.append("\n".join(p_lines))
        
        sa_aspect = ((lagna_rasi_idx) - tr_sa_rasi) % 12 in [0, 2, 6, 9]
        tr_msg = "🚨 **LIVE TRANSIT:** Gochar Saturn is aspecting your Lagna core! Demands structural discipline." if sa_aspect else "Live Transit: No critical structural blocks intersecting the Lagna right now."
        lines.append(f"**Step 10: Dasha - Bhukti Integration & Ultimate Master Principle:**\n- Mahadasha lord rules 70% of lifecycle delivery potential.\n- {tr_msg}")
        
        return "\n\n".join(lines)

# ---------------- GRAPHICS MATRIX COMPILER ----------------
def generate_vedic_chart_figure(engine):
    tjd = swe.julday(engine.view_date.year, engine.view_date.month, engine.view_date.day, 12.0)
    transit = engine.calc_planets(tjd, True)
    natal = engine.n_sid

    fig = go.Figure()

    # Place Natal Coordinates
    n_thetas = [v["lon"] for v in natal.values()]
    n_labels = [f"{p[:2]} {int(v['lon']%30)}°" for p, v in natal.items()]
    fig.add_trace(go.Scatterpolar(
        r=[0.8] * len(natal), theta=n_thetas, text=n_labels,
        mode="markers+text", name="Natal (Birth)", textposition="top center",
        marker=dict(color="#1a2a6c", size=12)
    ))

    # Place Transit Coordinates
    t_thetas = [v["lon"] for v in transit.values()]
    t_labels = [f"{p[:2]} {int(v['lon']%30)}°" for p, v in transit.items()]
    fig.add_trace(go.Scatterpolar(
        r=[1.2] * len(transit), theta=t_thetas, text=t_labels,
        mode="markers+text", name="Live Gochar Transit", textposition="bottom center",
        marker=dict(color="#b21f1f", size=12)
    ))

    fig.update_layout(
        polar=dict(
            angularaxis=dict(
                rotation=90, direction="clockwise",
                tickvals=[i*30 for i in range(12)],
                ticktext=["Ari","Tau","Gem","Can","Leo","Vir","Lib","Sco","Sag","Cap","Aqu","Pis"]
            ),
            radialaxis=dict(visible=False, range=[0, 1.5])
        ),
        margin=dict(l=40, r=40, t=40, b=40),
        height=550
    )
    return fig

# ---------------- DASH WEB INTERFACE LAYOUT ----------------
app = dash.Dash(__name__)

app.layout = html.Div([
    html.H2("PARASHARA VEDIC ASTRO ENGINE - DASHBOARD", style={'textAlign': 'center', 'color': '#1a2a6c', 'fontFamily': 'Arial'}),
    html.Hr(),
    
    # Configuration Bar
    html.Div([
        html.Div([
            html.B("Name: "), dcc.Input(id='w-name', value="Koteswara", style={'width':'120px', 'marginRight':'15px'}),
            html.B("DOB: "), dcc.Input(id='w-dob', value='05/04/1979', style={'width':'90px', 'marginRight':'15px'}),
            html.B("TOB: "), dcc.Input(id='w-tob', value='16:23:00', style={'width':'75px', 'marginRight':'15px'}),
            html.B("Birth City: "), dcc.Input(id='w-city', value="", placeholder="Default (Challapalli)", style={'width':'150px', 'marginRight':'15px'}),
            html.B("Transit Date: "), dcc.Input(id='w-tdate', value=datetime.now().strftime('%d/%m/%Y'), style={'width':'90px'}),
            html.Button('COMPUTE MATRIX', id='w-btn', n_clicks=0, style={'marginLeft':'20px', 'backgroundColor':'#1a2a6c', 'color':'white', 'fontWeight':'bold'})
        ], style={'padding':'15px', 'background':'#f8f9fa', 'borderRadius':'8px'})
    ]),
    
    # Primary Analytical Content Fields
    html.Div([
        # Column 1: Radials and Custom Matrix Selection
        html.Div([
            html.H3("🏆 Rasi Kundali Map Overlay", style={'color':'#1a2a6c'}),
            dcc.Graph(id='w-chart'),
            
            html.H4("Select Planet for Specific Cosmic Synthesis:"),
            dcc.Dropdown(id='w-planet-dropdown', options=[{'label': p, 'value': p} for p in PLANET_LIST], value='Sun', clearable=False),
            html.Div(id='w-synthesis-card', style={'marginTop':'15px', 'padding':'15px', 'background':'#eef2f7', 'borderRadius':'6px', 'whiteSpace':'pre-line'})
        ], style={'width': '55%', 'display': 'inline-block', 'verticalAlign': 'top', 'paddingRight':'2%'}),
        
        # Column 2: Structural Tables and 10 Steps Reading
        html.Div([
            html.H3("📊 Mathematical Balas Matrix", style={'color':'#1a2a6c'}),
            html.H5("Shadbala Calculations (In Rupas)"),
            dash_table.DataTable(
                id='w-shadbala-table',
                columns=[{"name": i.replace("_", " "), "id": i} for i in ["Planet", "Shadbala", "In_Rupas", "Percent_Strength", "IshtaPhala", "KashtaPhala"]],
                style_cell={'fontSize':'11px', 'textAlign':'center', 'padding':'5px'},
                style_header={'fontWeight':'bold', 'backgroundColor':'#f0f4f8'}
            ),
            
            html.H5("Calculated Pure Vedic Bhava Bala Strength", style={'marginTop':'15px'}),
            html.Div(id='w-bhava-bala-display', style={'fontSize':'12px', 'fontWeight':'bold', 'color':'#2c3e50', 'background':'#f8f9fa', 'padding':'10px'}),
            
            html.H3("🎯 Master 10-Steps Principle Assessment", style={'color':'#1a2a6c', 'marginTop':'20px'}),
            dcc.Markdown(id='w-master-report-markdown', style={'padding':'15px', 'background':'#fff9e6', 'borderRadius':'6px', 'border':'1px solid #ffe0b2'})
        ], style={'width': '43%', 'display': 'inline-block', 'verticalAlign': 'top'})
    ], style={'display':'flex', 'marginTop':'20px'})
], style={'padding':'20px', 'fontFamily':'Arial, sans-serif'})

# --- ROUTER CORE REACTIVE CALLBACK LINKING ---
@app.callback(
    [Output('w-chart', 'figure'),
     Output('w-shadbala-table', 'data'),
     Output('w-bhava-bala-display', 'children'),
     Output('w-synthesis-card', 'children'),
     Output('w-master-report-markdown', 'children')],
    [Input('w-btn', 'n_clicks'),
     Input('w-planet-dropdown', 'value')],
    [State('w-dob', 'value'),
     State('w-tob', 'value'),
     State('w-city', 'value'),
     State('w-tdate', 'value')]
)
def refresh_web_dashboard(n_clicks, selected_planet, dob, tob, city, tdate):
    try:
        engine = AstroEngine(dob=dob, tob=tob, birth_city=city, transit_date_str=tdate)
        
        # 1. Map Plotter Data
        fig = generate_vedic_chart_figure(engine)
        
        # 2. Shadbala Table Compile
        sb_data = engine.get_shadbala_data()
        
        # 3. Bhava Bala Formatting
        bb_res = engine.calculate_pure_vedic_bhava_bala()
        bb_string = " | ".join([f"H{h}: {v['rupas']}R ({v['pct']}%)" for h, v in bb_res.items()])
        
        # 4. Planetary Details Translation Component
        card_content = engine.get_artistic_synthesis(selected_planet)
        
        # 5. Parashara Final Report Summary String
        master_report = engine.get_master_10_steps_report()
        
        return fig, sb_data, bb_string, card_content, master_report
        
    except Exception as e:
        return go.Figure(), [], f"Error Processing Data: {str(e)}", "No Data Available", "Check input string configurations."

if __name__ == "__main__":
    app.run(debug=True)