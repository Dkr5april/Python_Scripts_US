import json
import os

class CompatibilityEngine:
    def __init__(self, data_path):
        self.data_path = data_path
        self.marriage_rules = self._load_json("marriage_compatibility_rules.json")
        self.kuja_rules = self._load_json("kuja_dosha_rules.json")
        self.rajju_rules = self._load_json("rajju_dosha_rules.json")
        self.tara_balam = self._load_json("tara_balam.json")

    def _load_json(self, filename):
        file_path = os.path.join(self.data_path, filename)
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)

    def check_rasi_compatibility(self, boy_rasi, girl_rasi):
        incompatible = self.marriage_rules["marriage_compatibility_rules"]["logic_map"].get(boy_rasi, {}).get("incompatible", [])
        return girl_rasi not in incompatible

    def check_rajju_dosha(self, boy_star, girl_star):
        bhaga_map = self.rajju_rules["rajju_dosha_rules"]["bhaga_map"]
        boy_bhaga = next((b for b, stars in bhaga_map.items() if boy_star in stars), None)
        girl_bhaga = next((b for b, stars in bhaga_map.items() if girl_star in stars), None)
        return boy_bhaga != girl_bhaga

    def check_tara_balam(self, boy_star, girl_star):
    # Safety Check: If the data isn't loaded yet, return True (or False) 
    # to avoid the crash while you are working on the JSON file.
    if not hasattr(self, 'tara_balam') or not self.tara_balam:
        return True 

    # Original logic
    try:
        stars = self.tara_balam["tara_balam"]["stars"] 
        b_idx = stars.index(boy_star)
        g_idx = stars.index(girl_star)
        count = (g_idx - b_idx) % 27 + 1
        return count not in [3, 5, 7]
    except (KeyError, ValueError, TypeError):
        # Returns True if star names aren't in your list yet
        return True

    def check_kuja_dosha(self, profile):
        """
        profile expects: {'house': int, 'lagna': str, 'conjoined': list}
        """
        rules = self.kuja_rules["kuja_dosha_rules"]
        # 1. Check if house is a Dosha house
        if profile['house'] not in rules["dosha_houses"]:
            return False
        # 2. Check exemptions (Lagna or Conjunctions)
        if profile['lagna'] in rules["exempt_lagnas"]:
            return False
        if any(c in rules["exemption_conjunctions"] for c in profile['conjoined']):
            return False
        return True # Active Dosha