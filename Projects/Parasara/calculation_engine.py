import swisseph as swe

# =========================================================
# CALCULATION ENGINE
# =========================================================

class CalculationEngine:

    def __init__(self):

        # Path to Swiss Ephemeris files
        swe.set_ephe_path("./ephe")

        # Default Ayanamsha
        swe.set_sid_mode(swe.SIDM_LAHIRI)

    # =====================================================
    # PLANET POSITIONS
    # =====================================================

    def get_planets(self, jd):

        planet_ids = {
            "Sun": swe.SUN,
            "Moon": swe.MOON,
            "Mars": swe.MARS,
            "Mercury": swe.MERCURY,
            "Jupiter": swe.JUPITER,
            "Venus": swe.VENUS,
            "Saturn": swe.SATURN,
            "Rahu": swe.MEAN_NODE
        }

        planets = {}

        flags = swe.FLG_SIDEREAL | swe.FLG_SPEED

        for name, pid in planet_ids.items():

            # -------------------------------------------------
            # Swiss Ephemeris Calculation
            # -------------------------------------------------

            result = swe.calc_ut(jd, pid, flags)

            # result[0] => tuple:
            # (longitude, latitude, distance, speed_long, ...)
            values = result[0]

            longitude = values[0] % 360

            planets[name] = longitude

        return planets

    # =====================================================
    # NAKSHATRA + PADA
    # =====================================================

    def get_nakshatra_data(self, longitude):

        nakshatras = [

            "Ashwini",
            "Bharani",
            "Krittika",
            "Rohini",
            "Mrigashira",
            "Ardra",
            "Punarvasu",
            "Pushya",
            "Ashlesha",

            "Magha",
            "Purva Phalguni",
            "Uttara Phalguni",
            "Hasta",
            "Chitra",
            "Swati",
            "Vishakha",
            "Anuradha",
            "Jyeshtha",

            "Moola",
            "Purva Ashadha",
            "Uttara Ashadha",
            "Shravana",
            "Dhanishta",
            "Shatabhisha",
            "Purva Bhadra",
            "Uttara Bhadra",
            "Revati"
        ]

        nak_length = 360 / 27

        index = int(longitude / nak_length)

        if index > 26:
            index = 26

        balance = longitude % nak_length

        pada = int(balance / (nak_length / 4)) + 1

        return {
            "nakshatra": nakshatras[index],
            "pada": pada
        }

    # =====================================================
    # SPECIAL POINTS
    # =====================================================

    def get_special_points(self, jd):

        points = {}

        special_points = {
            "Mandi": swe.MANDI,
            "Gulika": swe.GULIKA
        }

        for name, pid in special_points.items():

            result = swe.calc_ut(
                jd,
                pid,
                swe.FLG_SIDEREAL
            )

            values = result[0]

            longitude = values[0] % 360

            points[name] = longitude

        return points

    # =====================================================
    # PLANETS WITH RETROGRADE
    # =====================================================

    def get_planets_with_retro(self, jd, lat, lon):
        houses, ascmc = swe.houses(jd, lat, lon, b'P')
        ayanamsa = swe.get_ayanamsa_ut(jd)
        
        # Ascendant (Lagna) calculation - ayanamsa adjust చేసి
        asc_lon = (ascmc[0] - ayanamsa) % 360
        
        # House Cusp Calculation
        cusps = [(h - ayanamsa) % 360 for h in houses]
        def get_house(lon_val):
            for i in range(12):
                start = cusps[i]
                end = cusps[(i + 1) % 12]
                if start < end:
                    if start <= lon_val < end: return i + 1
                else:
                    if lon_val >= start or lon_val < end: return i + 1
            return 1

        data = {}
        planet_ids = {"Sun": swe.SUN, "Moon": swe.MOON, "Mars": swe.MARS, "Mercury": swe.MERCURY, 
                      "Jupiter": swe.JUPITER, "Venus": swe.VENUS, "Saturn": swe.SATURN, "Rahu": swe.MEAN_NODE}

        # 1. ప్లానెట్స్ డేటా
        for name, pid in planet_ids.items():
            res = swe.calc_ut(jd, pid, swe.FLG_SIDEREAL | swe.FLG_SPEED)
            lon_val = res[0][0] % 360
            data[name] = {
                "lon": lon_val,
                "retro": res[0][3] < 0 and name not in ["Sun", "Moon", "Rahu"],
                "house": get_house(lon_val),
                "sign": int(lon_val // 30)
            }
        
        # 2. Ascendant ని కూడా చేర్చడం
        data["Asc"] = {
            "lon": asc_lon,
            "retro": False, # Asc ఎప్పుడూ Retro ఉండదు
            "house": 1,
            "sign": int(asc_lon // 30)
        }
        
        return data

# =========================================================
# TESTING
# =========================================================

if __name__ == "__main__":

    engine = CalculationEngine()

    # Example JD
    jd = swe.julday(
        1990,
        8,
        15,
        10.5
    )

    # -----------------------------------------------------
    # PLANETS
    # -----------------------------------------------------

    planets = engine.get_planets(jd)

    print("\n========== PLANETS ==========\n")

    for name, lon in planets.items():

        sign = int(lon // 30)

        print(
            f"{name:10} "
            f"{lon:8.2f}° "
            f"Sign={sign}"
        )

    # -----------------------------------------------------
    # NAKSHATRAS
    # -----------------------------------------------------

    print("\n======= NAKSHATRAS =======\n")

    for name, lon in planets.items():

        nk = engine.get_nakshatra_data(lon)

        print(
            f"{name:10} "
            f"{nk['nakshatra']} "
            f"Pada {nk['pada']}"
        )

    # -----------------------------------------------------
    # RETROGRADE
    # -----------------------------------------------------

    print("\n======= RETROGRADE =======\n")

    retro_data = engine.get_planets_with_retro(
        jd,
        17.3850,   # Hyderabad Latitude
        78.4867    # Hyderabad Longitude
    )

    for name, info in retro_data.items():

        print(
            f"{name:10} "
            f"{info['lon']:8.2f}° "
            f"Retro={info['retro']}"
        )

    # -----------------------------------------------------
    # SPECIAL POINTS
    # -----------------------------------------------------

    print("\n======= SPECIAL POINTS =======\n")

    points = engine.get_special_points(jd)

    for name, lon in points.items():

        print(
            f"{name:10} "
            f"{lon:8.2f}°"
        )