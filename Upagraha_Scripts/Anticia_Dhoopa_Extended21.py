import swisseph as swe
import os, sys
import geocoder
from datetime import datetime, timedelta
from geopy.geocoders import Nominatim
from rich.console import Console
from fpdf import FPDF

# ---------------- STABILITY & PATHS ----------------
if sys.platform == "win32":
    os.system("color")

swe.set_ephe_path("./ephe")
console = Console()
geolocator = Nominatim(user_agent="astro_master_v27_final")

ORB_LON = 5.0
ORB_DEC = 3.0

# ---------------- INPUT ----------------
console.clear()
console.print("[bold magenta]=== ASTRO ENGINE V27 (TOTAL INTEGRATION) ===[/bold magenta]\n")

name = input("Enter Name: ")
dob = input("Enter DOB (DD/MM/YYYY): ")
tob = input("Enter TOB (HH:MM:SS): ")
birth_city = input("Enter Birth City: ")

def fetch_coords(city):
    try:
        loc = geolocator.geocode(city, timeout=5)
        if loc:
            return float(loc.latitude), float(loc.longitude)
    except:
        pass
    return 16.12, 80.92  # Challapally fallback

b_lat, b_lon = fetch_coords(birth_city)
scan_days = int(input("\nHow many days to scan for PDF? "))

d, m, y = map(int, dob.split("/"))
hh, mm, ss = map(int, tob.split(":"))
birth_hour = hh + mm / 60 + ss / 3600

INDIAN_PLANETS = [(0,"Su"), (1,"Mo"), (2,"Me"), (3,"Ve"),
                  (4,"Ma"), (5,"Ju"), (6,"Sa"), (11,"Ra")]
WESTERN_PLANETS = [(7,"Ur"), (8,"Ne"), (9,"Pl")]

# ---------------- ENGINE ----------------
class AstroEngine:
    def __init__(self):
        self.njd = swe.julday(y, m, d, birth_hour)
        swe.set_sid_mode(swe.SIDM_LAHIRI)

        self.n_sid = self.calc_planets(self.njd, True)
        self.n_trop = self.calc_planets(self.njd, False)

        _, ascmc = swe.houses_ex(self.njd, b_lat, b_lon, b'P')
        res_asc, _ = swe.calc_ut(self.njd, swe.ASC)
        res_mc, _  = swe.calc_ut(self.njd, swe.MC)

        self.n_trop["Asc"] = {"lon": ascmc[0], "dec": res_asc[1], "retro": False}
        self.n_trop["MC"]  = {"lon": ascmc[1], "dec": res_mc[1],  "retro": False}

        self.n_ant = {k: (180 - v["lon"]) % 360 for k, v in self.n_trop.items()}
        self.n_up = self.get_all_upagrahas()

        sun_lon = self.n_sid["Su"]["lon"]
        self.n_apra = {
            "Dhuma": (sun_lon + 133.333) % 360,
            "Vyatipata": (360 - (sun_lon + 186.666)) % 360,
            "Paridhi": (360 - (sun_lon + 6.666)) % 360,
            "Chapa": (sun_lon + 23.333) % 360,
            "Upaketu": (sun_lon + 40.0) % 360
        }

    def get_all_upagrahas(self):
        mjd = swe.julday(y, m, d, 0.0)
        geopos = (b_lon, b_lat, 0)

        rise = swe.rise_trans(mjd, swe.SUN, swe.CALC_RISE, geopos)[1][0]
        sset = swe.rise_trans(mjd, swe.SUN, swe.CALC_SET, geopos)[1][0]

        is_day = rise <= self.njd <= sset
        part = ((sset - rise) if is_day else (1 - (sset - rise))) / 8.0

        start_l = swe.day_of_week(self.njd) if is_day else (swe.day_of_week(self.njd) + 4) % 7

        lords = {
            0:"Kala", 1:"Gauri", 2:"Artha", 3:"Khanda",
            4:"Mrityu", 5:"Yama", 6:"Gulika", 7:"M-Kala"
        }

        up_pos = {}
        for i in range(8):
            seg = (rise if is_day else sset) + i * part
            _, ascmc = swe.houses_ex(seg, b_lat, b_lon, b'P')
            up_pos[lords.get((start_l + i) % 7, f"U{i}")] = ascmc[0]

        return up_pos

    def calc_planets(self, jd, sidereal):
        flags = swe.FLG_SWIEPH | swe.FLG_SPEED
        if sidereal:
            flags |= swe.FLG_SIDEREAL

        data = {}
        plist = INDIAN_PLANETS if sidereal else INDIAN_PLANETS + WESTERN_PLANETS
        for pid, pnm in plist:
            res, _ = swe.calc_ut(jd, pid, flags)
            data[pnm] = {"lon": res[0], "dec": res[1], "retro": res[3] < 0}
        return data

    # ---------------- FIXED INDENTATION ----------------
    def score_day(self, target_date):
        tjd = swe.julday(target_date.year, target_date.month, target_date.day, 12.0)
        t_sid = self.calc_planets(tjd, True)
        t_trop = self.calc_planets(tjd, False)

        score = 0
        hits = []

        for tp, t in t_sid.items():
            for name, lon in {**self.n_up, **self.n_apra}.items():
                if abs(t["lon"] - lon) < ORB_LON:
                    if name == "Yama":
                        wt = 3
                    elif name in ["Gulika", "Kala", "Mrityu"]:
                        wt = -1
                    elif name == "Vyatipata":
                        wt = -2
                    else:
                        wt = 0
                    score += wt
                    hits.append(f"{tp} hit {name} ({wt})")

        for tp, t in t_trop.items():
            for np, n in self.n_trop.items():
                if abs(t["dec"] - n["dec"]) < ORB_DEC:
                    wt = 2 if np in ["Ju", "Ve", "Su"] else -1
                    score += wt
                    hits.append(f"{tp} Para {np} ({wt})")

                if abs(t["dec"] + n["dec"]) < ORB_DEC:
                    score -= 0.5
                    hits.append(f"{tp} C-Para {np} (-1)")

            for np, alon in self.n_ant.items():
                if abs(t["lon"] - alon) < ORB_LON:
                    score += 1
                    hits.append(f"{tp} Antisc {np} (+1)")

        score = max(min(score, 6), -4)
        return score, hits

engine = AstroEngine()

# ---------------- PDF ----------------
def generate_pdf():
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", "B", 16)
    pdf.cell(0, 10, f"MASTER ASTRO FORECAST: {name}", 0, 1, "C")

    for i in range(scan_days):
        day = datetime.now() + timedelta(days=i)
        score, hits = engine.score_day(day)

        color = (0,150,0) if score >= 3 else (200,0,0) if score <= -3 else (0,0,0)
        pdf.set_text_color(*color)
        pdf.set_font("Arial", "B", 10)
        pdf.cell(0, 8, f"{day:%d-%b-%Y} | Score: {score}", 1, 1)

        pdf.set_font("Arial", "", 8)
        pdf.set_text_color(60,60,60)
        pdf.multi_cell(0, 5, " | ".join(hits) if hits else "Normal Day")
        pdf.ln(1)

    pdf.output(f"Master_{name}.pdf")
    print(f"\nPDF Saved: Master_{name}.pdf")

generate_pdf()
