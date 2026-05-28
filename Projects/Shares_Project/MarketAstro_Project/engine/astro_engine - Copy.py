# engine/astro_engine.py
import swisseph as swe
from datetime import timedelta
import config  # Import your new configuration file

class AstroEngine:
    def __init__(self):
        # Pull values directly from config.py
        self.lat = config.LATITUDE
        self.lon = config.LONGITUDE
        self.offset = config.TIMEZONE_OFFSET
        swe.set_sid_mode(swe.SIDM_LAHIRI)

    def get_planet_details(self, jd, p_id, name, houses):
        res, _ = swe.calc_ut(jd, p_id, swe.FLG_SWIEPH | swe.FLG_SIDEREAL | swe.FLG_SPEED)
        lon, speed = res[0], res[3]
        
        h_num = "?"
        for i in range(12):
            if i < 11:
                if houses[i] <= lon < houses[i+1]:
                    h_num = i + 1; break
            else:
                if houses[11] <= lon or lon < houses[0]:
                    h_num = 12
        
        return {
            "name": name,
            "deg": round(lon % 30, 4),
            "is_retro": speed < 0 if name not in ["Ra", "Ke"] else False,
            "h": h_num,
            "speed": round(speed, 4),
            "lon": lon
        }

    def get_full_snapshot(self, dt):
        # The time is now passed dynamically from your UI or script
        gmt_dt = dt - timedelta(hours=self.offset)
        jd = swe.julday(gmt_dt.year, gmt_dt.month, gmt_dt.day, gmt_dt.hour + gmt_dt.minute/60)
        
        h_res, _ = swe.houses_ex(jd, self.lat, self.lon, b'P', swe.FLG_SIDEREAL)
        
        planets = {"Su": 0, "Mo": 1, "Ma": 4, "Me": 2, "Ju": 5, "Ve": 3, "Sa": 6, "Ra": 10}
        data = {n: self.get_planet_details(jd, i, n, h_res) for n, i in planets.items()}
        
        # Ketu calculation
        k_lon = (data["Ra"]["lon"] + 180) % 360
        data["Ke"] = self.get_planet_details(jd, -1, "Ke", h_res)
        data["Ke"]["lon"] = k_lon
        data["Ke"]["deg"] = round(k_lon % 30, 4)
        
        return data