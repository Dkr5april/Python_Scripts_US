import swisseph as swe
import os
import sys

class AstroEngine:
    def __init__(self):
        # --- AUTOMATIC PATH DETECTION ---
        # This mirrors your existing robust engine logic
        if hasattr(sys, '_MEIPASS'):
            self.ephe_path = os.path.join(sys._MEIPASS, 'ephe')
        else:
            self.ephe_path = os.path.join(os.path.dirname(__file__), 'ephe')
        
        # Configure the engine
        swe.set_ephe_path(self.ephe_path)
        swe.set_sid_mode(swe.SIDM_LAHIRI)
        
        # Static definitions for calculations
        self.rasi_names = ['mesha', 'vrishabha', 'mithuna', 'karkataka', 'simha', 'kanya', 
                           'tula', 'vrischika', 'dhanur', 'makara', 'kumbha', 'meena']

    def calculate_birth_data(self, y, m, d, hh, mm, lat, lon):
        # Calculate Julian Day
        birth_hour_ut = (hh + mm/60) - 5.5
        jd = swe.julday(y, m, d, birth_hour_ut)
        
        # Calculate Planets
        # Sun=0, Moon=1, Mars=4
        mars_res = swe.calc_ut(jd, 4, swe.FLG_SIDEREAL)[0]
        moon_res = swe.calc_ut(jd, 1, swe.FLG_SIDEREAL)[0]
        
        # Calculate Houses/Lagna
        houses, ascmc = swe.houses_ex(jd, lat, lon, b'S', swe.FLG_SIDEREAL)
        lagna_rasi = int(ascmc[0] // 30)
        
        # Map to Engine requirements
        return {
            "rasi": self.rasi_names[lagna_rasi],
            "mars_house": ((int(mars_res[0] // 30) - lagna_rasi) % 12) + 1,
            "moon_star": self._get_star(moon_res[0])
        }

    def _get_star(self, lon):
        star_idx = int(lon // 13.3333)
        stars = ["aswini", "bharani", "krithika", "rohini", "mrigasira", "arudra", "punarvasu", 
                 "pushyami", "aslesha", "makha", "pubba", "uttara", "hastha", "chitta", 
                 "swathi", "visakha", "anuradha", "jyestha", "moola", "p.ashadha", 
                 "u.ashadha", "sravana", "dhanistha", "satabhisha", "p.bhadra", "u.bhadra", "revathi"]
        return stars[star_idx % 27]