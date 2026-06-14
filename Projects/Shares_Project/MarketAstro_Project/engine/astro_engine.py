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
            "rasi": int(lon / 30)
        }

    def get_full_snapshot(self, dt):
        gmt_dt = dt - timedelta(hours=self.offset)

        jd = swe.julday(
            gmt_dt.year,
            gmt_dt.month,
            gmt_dt.day,
            gmt_dt.hour + gmt_dt.minute / 60
        )

        PLANET_MAP = {
            "Su": swe.SUN,
            "Mo": swe.MOON,
            "Ma": swe.MARS,
            "Me": swe.MERCURY,
            "Ju": swe.JUPITER,
            "Ve": swe.VENUS,
            "Sa": swe.SATURN,
            "Ra": swe.TRUE_NODE,
            "Ur": swe.URANUS,
            "Ne": swe.NEPTUNE,
            "Pl": swe.PLUTO,
        }

        data = {}

        for name, pid in PLANET_MAP.items():
            data[name] = self.get_planet_details(jd, pid, name)

        # ---------------------------------
        # KETU
        # ---------------------------------
        k_lon = (data["Ra"]["lon"] + 180) % 360

        LORDS = ["Ke", "Ve", "Su", "Mo", "Ma", "Ra", "Ju", "Sa", "Me"]
        NAKSHATRAS = [
            "Ashwini", "Bharani", "Krittika", "Rohini", "Mrigashira",
            "Ardra", "Punarvasu", "Pushya", "Ashlesha", "Magha",
            "Purva Phalguni", "Uttara Phalguni", "Hasta", "Chitra",
            "Swati", "Vishakha", "Anuradha", "Jyeshtha", "Mula",
            "Purva Ashadha", "Uttara Ashadha", "Shravana",
            "Dhanishta", "Shatabhisha", "Purva Bhadrapada",
            "Uttara Bhadrapada", "Revati"
        ]

        k_idx = int(k_lon / 13.33333333)

        data["Ke"] = {
            "name": "Ke",
            "star": NAKSHATRAS[k_idx],
            "lord": LORDS[k_idx % 9],
            "pada": int((k_lon % 13.33333333) / 3.33333333) + 1,
            "deg": round(k_lon % 30, 4),
            "speed": data["Ra"]["speed"],
            "is_retro": False,
            "lon": k_lon,
            "rasi": int(k_lon / 30)
        }

        # ---------------------------------
        # ASCENDANT
        # ---------------------------------
        houses, ascmc = swe.houses_ex(
            jd,
            self.lat,
            self.lon,
            b'P',
            swe.FLG_SIDEREAL
        )

        asc_lon = ascmc[0]
        asc_idx = int(asc_lon / 13.33333333)

        data["Asc"] = {
            "name": "Asc",
            "star": NAKSHATRAS[asc_idx],
            "lord": LORDS[asc_idx % 9],
            "pada": int((asc_lon % 13.33333333) / 3.33333333) + 1,
            "deg": round(asc_lon % 30, 4),
            "speed": 0,
            "is_retro": False,
            "lon": asc_lon,
            "rasi": int(asc_lon / 30),
            "house": 1,
            "status": "DIR"
        }

        # ---------------------------------
        # HOUSE & RETRO CALCULATION
        # ---------------------------------
        for planet in data.values():
            if planet["name"] == "Asc":
                continue

            diff = (planet["lon"] - asc_lon) % 360
            house_num = int(diff / 30) + 1

            if house_num > 12:
                house_num -= 12

            planet["house"] = house_num

            # Explicit layout matching flag evaluation
            if planet.get("is_retro") is True:
                planet["status"] = "RETRO"
            else:
                planet["status"] = "DIR"

        return data