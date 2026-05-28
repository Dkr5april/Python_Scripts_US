import swisseph as swe
import json
import os
from datetime import datetime

# --- SETTINGS ---
JSON_FILE = "pulippani_300.json"
swe.set_ephe_path("./ephe")

class PulippaniEngine:
    def __init__(self, dob, tob, lat, lon, tz):
        self.grandham = self.load_grandham()
        self.planets = self.calculate_natal(dob, tob, lat, lon, tz)
        self.lagna_house = self.calculate_lagna(dob, tob, lat, lon, tz)
        
    def load_grandham(self):
        if os.path.exists(JSON_FILE):
            with open(JSON_FILE, 'r') as f:
                return json.load(f)
        return {"placements": {}, "combinations": []}

    def calculate_natal(self, dob, tob, lat, lon, tz):
        d, m, y = map(int, dob.split("/"))
        hh, mm, ss = map(int, tob.split(":"))
        utc_time = (hh + mm/60 + ss/3600) - tz
        jd = swe.julday(y, m, d, utc_time)
        
        swe.set_sid_mode(swe.SIDM_LAHIRI)
        planets = {"Su": 0, "Mo": 1, "Ma": 4, "Me": 2, "Ju": 5, "Ve": 3, "Sa": 6, "Ra": 11}
        data = {}
        for name, id in planets.items():
            lon_val = swe.calc_ut(jd, id, swe.FLG_SIDEREAL)[0][0]
            data[name] = lon_val
        data["Ke"] = (data["Ra"] + 180) % 360
        return data

    def calculate_lagna(self, dob, tob, lat, lon, tz):
        d, m, y = map(int, dob.split("/"))
        hh, mm, ss = map(int, tob.split(":"))
        utc_time = (hh + mm/60 + ss/3600) - tz
        jd = swe.julday(y, m, d, utc_time)
        return swe.houses_ex(jd, lat, lon, b'W')[0][0]

    def get_house(self, p_lon):
        lagna_rasi = int(self.lagna_house / 30)
        p_rasi = int(p_lon / 30)
        return (p_rasi - lagna_rasi + 12) % 12 + 1

    def run_audit(self):
        findings = []
        house_map = {i: set() for i in range(1, 13)}
        
        # 1. Map current chart to houses
        for p, lon in self.planets.items():
            h = self.get_house(lon)
            house_map[h].add(p)
            
            # Check Single Placements in JSON
            h_str = str(h)
            if p in self.grandham["placements"] and h_str in self.grandham["placements"][p]:
                sloka, desc = self.grandham["placements"][p][h_str]
                findings.append(f"[Sloka {sloka}] {p} in H{h}: {desc}")

        # 2. Scan for Combinations from JSON
        for combo in self.grandham["combinations"]:
            target_planets = set(combo["planets"])
            target_house = combo["house"]
            
            for h, present_planets in house_map.items():
                if target_planets.issubset(present_planets):
                    # Check if it matches house constraint
                    if target_house == "any" or target_house == h:
                        findings.append(f"[Sloka {combo['sloka']}] {combo['title']} in H{h}: {combo['effect']}")
        
        return findings

# --- EXECUTION ---
# Example for your Scottsdale coordinates
engine = PulippaniEngine("15/06/1985", "03:57:42", 33.4942, -111.9261, -7.0)
results = engine.run_audit()

print("\n--- PULIPPANI 300 AUDIT RESULTS ---")
for r in results:
    print(r)