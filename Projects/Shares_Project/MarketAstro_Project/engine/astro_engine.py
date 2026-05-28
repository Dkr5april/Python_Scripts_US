# engine/astro_engine.py
import swisseph as swe
from datetime import timedelta
import config

class AstroEngine:
    def __init__(self):
        self.lat = config.LATITUDE
        self.lon = config.LONGITUDE
        self.offset = config.TIMEZONE_OFFSET
        swe.set_sid_mode(swe.SIDM_LAHIRI)

    def get_planet_details(self, jd, p_id, name):
        res, _ = swe.calc_ut(jd, p_id, swe.FLG_SWIEPH | swe.FLG_SIDEREAL | swe.FLG_SPEED)
        lon, speed = res[0], res[3]
        
        # Mapping to Star/Lord/Pada
        LORDS = ["Ke", "Ve", "Su", "Mo", "Ma", "Ra", "Ju", "Sa", "Me"]
        NAKSHATRAS = ["Ashwini", "Bharani", "Krittika", "Rohini", "Mrigashira", "Ardra", "Punarvasu", "Pushya", "Ashlesha", "Magha", "Purva Phalguni", "Uttara Phalguni", "Hasta", "Chitra", "Swati", "Vishakha", "Anuradha", "Jyeshtha", "Mula", "Purva Ashadha", "Uttara Ashadha", "Shravana", "Dhanishta", "Shatabhisha", "Purva Bhadrapada", "Uttara Bhadrapada", "Revati"]
        
        star_idx = int(lon / 13.33333333)
        
        return {
            "name": name,
            "star": NAKSHATRAS[star_idx],
            "lord": LORDS[star_idx % 9],
            "pada": int((lon % 13.33333333) / 3.33333333) + 1,
            "deg": round(lon % 30, 4),
            "speed": round(speed, 4),
            "is_retro": speed < 0 if name not in ["Ra", "Ke"] else False,
            "lon": lon,
            "rasi": int(lon/30)
        }

    def get_full_snapshot(self, dt):
        gmt_dt = dt - timedelta(hours=self.offset)
        jd = swe.julday(gmt_dt.year, gmt_dt.month, gmt_dt.day, gmt_dt.hour + gmt_dt.minute/60)
        
        # Including Outer Planets
        PLANET_MAP = {
            "Su": 0, "Mo": 1, "Ma": 4, "Me": 2, "Ju": 5, "Ve": 3, "Sa": 6,
            "Ra": 10, "Ur": 7, "Ne": 8, "Pl": 9
        }
        
        data = {n: self.get_planet_details(jd, i, n) for n, i in PLANET_MAP.items()}
        
        # Ketu Calculation
        k_lon = (data["Ra"]["lon"] + 180) % 360
        k_idx = int(k_lon / 13.33333333)
        LORDS = ["Ke", "Ve", "Su", "Mo", "Ma", "Ra", "Ju", "Sa", "Me"]
        NAKSHATRAS = ["Ashwini", "Bharani", "Krittika", "Rohini", "Mrigashira", "Ardra", "Punarvasu", "Pushya", "Ashlesha", "Magha", "Purva Phalguni", "Uttara Phalguni", "Hasta", "Chitra", "Swati", "Vishakha", "Anuradha", "Jyeshtha", "Mula", "Purva Ashadha", "Uttara Ashadha", "Shravana", "Dhanishta", "Shatabhisha", "Purva Bhadrapada", "Uttara Bhadrapada", "Revati"]
        
        data["Ke"] = {
            "name": "Ke", "star": NAKSHATRAS[k_idx], "lord": LORDS[k_idx % 9],
            "pada": int((k_lon % 13.33333333) / 3.33333333) + 1, "deg": round(k_lon % 30, 4),
            "speed": data["Ra"]["speed"], "is_retro": data["Ra"]["is_retro"], "lon": k_lon
        }
        return data