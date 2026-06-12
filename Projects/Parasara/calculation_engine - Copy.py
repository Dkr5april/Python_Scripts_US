import swisseph as swe

class CalculationEngine:
    def __init__(self):
        swe.set_ephe_path("./ephe")
        # Ensure sidereal mode is set globally here if desired
        swe.set_sid_mode(swe.SIDM_LAHIRI) 

    def get_planets(self, jd):
        ayan = swe.get_ayanamsa_ut(jd)
        planet_ids = {
            "Sun": swe.SUN, "Moon": swe.MOON, "Mars": swe.MARS,
            "Mercury": swe.MERCURY, "Jupiter": swe.JUPITER, 
            "Venus": swe.VENUS, "Saturn": swe.SATURN, "Rahu": swe.TRUE_NODE
        }
        
        # Use FLG_SIDEREAL consistently
        planets = {}
        for name, pid in planet_ids.items():
            res = swe.calc_ut(jd, pid, swe.FLG_SIDEREAL | swe.FLG_SPEED)
            lon = (res[0][0]) % 360 # If FLG_SIDEREAL is set, the output is already sidereal
            planets[name] = lon
        return planets

    def get_nakshatra_data(self, lon):
        nakshatras = ["Ashwini", "Bharani", "Krittika", "Rohini", "Mrigashira", "Ardra", "Punarvasu", "Pushya", "Ashlesha",
                      "Magha", "Purva Phalguni", "Uttara Phalguni", "Hasta", "Chitra", "Swati", "Vishakha", "Anuradha", "Jyeshtha",
                      "Moola", "Purva Ashadha", "Uttara Ashadha", "Shravana", "Dhanishta", "Shatabhisha", "Purva Bhadra", "Uttara Bhadra", "Revati"]
        
        step = 360/27
        idx = int(lon / step)
        if idx >= 27: idx = 26
        pada = int(((lon % step) / step) * 4) + 1
        return nakshatras[idx], pada

    def get_special_points(self, jd):
        points = {}
        for name, pid in {"Mandi": swe.MANDI, "Gulika": swe.GULIKA}.items():
            res = swe.calc_ut(jd, pid, swe.FLG_SIDEREAL)[0]
            points[name] = res[0] % 360
        return points
        
    def get_planets_with_retro(self, jd, lat, lon):
        # 1. Calculate Tropical Ascendant
        houses, ascmc = swe.houses(jd, lat, lon, b'P')
        tropical_asc = ascmc[0]
        
        # 2. Get the current Ayanamsa value for the given JD
        swe.set_sid_mode(swe.SIDM_LAHIRI)
        ayanamsa = swe.get_ayanamsa_ut(jd)
        
        # 3. Apply the correction: Sidereal = Tropical - Ayanamsa
        # Ensure it stays within 0-360 degrees
        ascendant = (tropical_asc - ayanamsa) % 360
        
        # ... rest of your code (planet_ids, etc)
        
        planet_ids = {
            "Sun": swe.SUN, "Moon": swe.MOON, "Mars": swe.MARS,
            "Mercury": swe.MERCURY, "Jupiter": swe.JUPITER, 
            "Venus": swe.VENUS, "Saturn": swe.SATURN, "Rahu": swe.TRUE_NODE
        }
        
        data = {"Asc": {"lon": ascendant, "retro": False}} # Structured like other planets
        for name, pid in planet_ids.items():
            res = swe.calc_ut(jd, pid, swe.FLG_SIDEREAL | swe.FLG_SPEED)
            lon = res[0][0] % 360
            speed = res[0][3]
            is_retro = speed < 0 and name not in ["Sun", "Moon", "Rahu"]
            data[name] = {"lon": lon, "retro": is_retro}
        return data