# engine/astro_engine.py
import swisseph as swe
from datetime import timedelta
import config

class AstroEngine:
    def __init__(self):
        # Fallback defaults from your config file
        self.lat = config.LATITUDE
        self.lon = config.LONGITUDE
        self.offset = config.TIMEZONE_OFFSET
        
        # FIXED: Explicit format to lock Swiss Ephemeris to True Lahiri Sidereal mode
        swe.set_sid_mode(swe.SIDM_LAHIRI, 0, 0)

    def get_planet_details(self, jd, p_id, name):
        # Fetch metrics safely using the explicit Swiss Ephemeris + Sidereal flags
        res, _ = swe.calc_ut(jd, p_id, swe.FLG_SWIEPH | swe.FLG_SIDEREAL | swe.FLG_SPEED)
        
        # Normalize longitudes immediately to fit strictly within a 0-360 degree circle
        lon = res[0] % 360.0
        speed = res[3]

        LORDS = ["Ke", "Ve", "Su", "Mo", "Ma", "Ra", "Ju", "Sa", "Me"]
        NAKSHATRAS = [
            "Ashwini", "Bharani", "Krittika", "Rohini", "Mrigashira", "Ardra", 
            "Punarvasu", "Pushya", "Ashlesha", "Magha", "Purva Phalguni", "Uttara Phalguni", 
            "Hasta", "Chitra", "Swati", "Vishakha", "Anuradha", "Jyeshtha", "Mula", 
            "Purva Ashadha", "Uttara Ashadha", "Shravana", "Dhanishta", "Shatabhisha", 
            "Purva Bhadrapada", "Uttara Bhadrapada", "Revati"
        ]

        # Use exact fraction division fractions to eliminate floating-point drops
        nakshatra_span = 360.0 / 27.0  # Exactly 13.333333333333334
        star_idx = int(lon / nakshatra_span)
        
        if star_idx > 26: 
            star_idx = 26

        return {
            "name": name,
            "star": NAKSHATRAS[star_idx],
            "lord": LORDS[star_idx % 9],
            "pada": int((lon % nakshatra_span) / (nakshatra_span / 4.0)) + 1,
            "deg": round(lon % 30, 4),
            "speed": round(speed, 4),
            "is_retro": speed < 0 if name not in ["Ra", "Ke"] else False,
            "lon": lon,
            "rasi": int(lon / 30)
        }

    def get_full_snapshot(self, dt, lat=None, lon=None, offset=None):
        """
        Calculates a full planetary snapshot. Accepts dynamic overrides from the UI 
        to calculate coordinates correctly based on location.
        """
        # FIXED: Ensure the sidereal mode is reset right before calculation execution
        swe.set_sid_mode(swe.SIDM_LAHIRI, 0, 0)

        calc_lat = lat if lat is not None else self.lat
        calc_lon = lon if lon is not None else self.lon
        calc_offset = offset if offset is not None else self.offset

        # Parse local time to GMT/UTC
        gmt_dt = dt - timedelta(hours=calc_offset)

        # Include exact calculation weights down to seconds
        decimal_hours = gmt_dt.hour + (gmt_dt.minute / 60.0) + (gmt_dt.second / 3600.0)

        jd = swe.julday(
            gmt_dt.year,
            gmt_dt.month,
            gmt_dt.day,
            decimal_hours
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
        # KETU (180 degrees opposite Rahu)
        # ---------------------------------
        k_lon = (data["Ra"]["lon"] + 180.0) % 360.0
        nakshatra_span = 360.0 / 27.0
        k_idx = int(k_lon / nakshatra_span)
        if k_idx > 26: k_idx = 26

        LORDS = ["Ke", "Ve", "Su", "Mo", "Ma", "Ra", "Ju", "Sa", "Me"]
        NAKSHATRAS = [
            "Ashwini", "Bharani", "Krittika", "Rohini", "Mrigashira", "Ardra", 
            "Punarvasu", "Pushya", "Ashlesha", "Magha", "Purva Phalguni", "Uttara Phalguni", 
            "Hasta", "Chitra", "Swati", "Vishakha", "Anuradha", "Jyeshtha", "Mula", 
            "Purva Ashadha", "Uttara Ashadha", "Shravana", "Dhanishta", "Shatabhisha", 
            "Purva Bhadrapada", "Uttara Bhadrapada", "Revati"
        ]

        data["Ke"] = {
            "name": "Ke",
            "star": NAKSHATRAS[k_idx],
            "lord": LORDS[k_idx % 9],
            "pada": int((k_lon % nakshatra_span) / (nakshatra_span / 4.0)) + 1,
            "deg": round(k_lon % 30, 4),
            "speed": data["Ra"]["speed"],
            "is_retro": False,
            "lon": k_lon,
            "rasi": int(k_lon / 30)
        }

        # ---------------------------------
        # ASCENDANT (Using Placidus House System)
        # ---------------------------------
        houses, ascmc = swe.houses_ex(
            jd,
            calc_lat,
            calc_lon,
            b'P',  # Placidus configuration matching your original setup
            swe.FLG_SIDEREAL
        )

        asc_lon = ascmc[0] % 360.0
        asc_idx = int(asc_lon / nakshatra_span)
        if asc_idx > 26: asc_idx = 26

        data["Asc"] = {
            "name": "Asc",
            "star": NAKSHATRAS[asc_idx],
            "lord": LORDS[asc_idx % 9],
            "pada": int((asc_lon % nakshatra_span) / (nakshatra_span / 4.0)) + 1,
            "deg": round(asc_lon % 30, 4),
            "speed": 0,
            "is_retro": False,
            "lon": asc_lon,
            "rasi": int(asc_lon / 30),
            "house": 1,
            "status": "DIR"
        }

        # ---------------------------------
        # HOUSE ASSIGNMENTS
        # ---------------------------------
        for planet in data.values():
            if planet["name"] == "Asc":
                continue

            diff = (planet["lon"] - asc_lon) % 360
            house_num = int(diff / 30) + 1

            if house_num > 12:
                house_num -= 12

            planet["house"] = house_num
            planet["status"] = "RETRO" if planet.get("is_retro") else "DIR"

        return data