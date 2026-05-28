import swisseph as swe
import datetime

# మీ డీఫాల్ట్ కోఆర్డినేట్స్ (Challapalli/Default Location)
b_lat, b_lon = 16.1176, 80.9314  

# ప్రస్తుత సమయం ఆధారంగా జూలియన్ డే (Julian Day) లెక్కించడం
now = datetime.datetime.now()
birth_hour_ut = (now.hour + now.minute/60.0) - 5.5 # IST to UT conversion

njd = swe.julday(now.year, now.month, now.day, birth_hour_ut)

try:
    # Sun (0) యొక్క లెక్కింపు ఏ మోడల్ ద్వారా జరుగుతుందో చెక్ చేస్తున్నాం
    flags = swe.FLG_SWIEPH | swe.FLG_SIDEREAL
    res, flag_returned = swe.calc_ut(njd, 0, flags)
    
    print("\n================== 🎯 ASTRO ENGINE DIAGNOSTIC ==================")
    if flag_returned & swe.FLG_MOSEPH:
        print("👉 STATUS: మీ స్క్రిప్ట్ 'Moshier Analytical Model' వాడుతోంది.")
        print("👉 INFO  : దీనికి బాహ్య 'ephe' ఫోల్డర్ లేదా డేటా ఫైల్స్ అస్సలు అవసరం లేదు!")
    else:
        print("👉 STATUS: మీ స్క్రిప్ట్ పక్కా 'Swiss Ephemeris (DE431/DE441) Files' వాడుతోంది.")
        print("👉 INFO  : దీనికి ఖచ్చితంగా 'ephe' ఫోల్డర్ లోపల ఉన్న ఫైల్స్ కావాలి.")
    print("================================================================\n")
    
except Exception as e:
    print(f"Error checking coordinates: {e}")