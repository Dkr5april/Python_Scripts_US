import random
import pandas as pd
import os
from datetime import datetime, timedelta
from astral.sun import sun
from astral import LocationInfo
from geopy.geocoders import Nominatim
from timezonefinder import TimezoneFinder

# -----------------------------
# 1. CORE MATH FUNCTIONS
# -----------------------------
def reduce_to_single_digit(number):
    print(f"[reduce_to_single_digit] Input: {number}")
    while number > 9:
        number = sum(int(d) for d in str(number))
        print(f"[reduce_to_single_digit] Reduced Step: {number}")
    print(f"[reduce_to_single_digit] Output: {number}")
    return number

def chaldean_name_number(name):
    print(f"[chaldean_name_number] Name: {name}")
    chaldean_map = {
        'A':1,'B':2,'C':3,'D':4,'E':5,'F':8,'G':3,'H':5,'I':1,'J':1,'K':2,
        'L':3,'M':4,'N':5,'O':7,'P':8,'Q':1,'R':2,'S':3,'T':4,'U':6,'V':6,
        'W':6,'X':5,'Y':1,'Z':7
    }
    total = sum(chaldean_map.get(c.upper(), 0) for c in name if c.isalpha())
    print(f"[chaldean_name_number] Raw Total: {total}")
    result = reduce_to_single_digit(total)
    print(f"[chaldean_name_number] Reduced: {result}")
    return result

def pythagorean_name_number(name):
    print(f"[pythagorean_name_number] Name: {name}")
    pyth_map = {
        'A':1,'B':2,'C':3,'D':4,'E':5,'F':6,'G':7,'H':8,'I':9,
        'J':1,'K':2,'L':3,'M':4,'N':5,'O':6,'P':7,'Q':8,'R':9,
        'S':1,'T':2,'U':3,'V':4,'W':5,'X':6,'Y':7,'Z':8
    }
    total = sum(pyth_map.get(c.upper(), 0) for c in name if c.isalpha())
    print(f"[pythagorean_name_number] Raw Total: {total}")
    result = reduce_to_single_digit(total)
    print(f"[pythagorean_name_number] Reduced: {result}")
    return result

def lo_shu_strength(numbers):
    print(f"[lo_shu_strength] Numbers: {numbers}")
    strength = len(set(numbers))
    print(f"[lo_shu_strength] Strength: {strength}")
    return strength

# -----------------------------
# 2. GEO & HORA LOGIC
# -----------------------------
def get_hora_data(m_date, m_time, venue):
    print(f"[get_hora_data] Date: {m_date}, Time: {m_time}, Venue: {venue}")
    geolocator = Nominatim(user_agent="match_hora_app_v6")
    location = geolocator.geocode(venue)
    if not location:
        raise ValueError("Venue not found. Please check the spelling.")
    print(f"[get_hora_data] Location: {location.latitude}, {location.longitude}")

    tf = TimezoneFinder()
    tz_str = tf.timezone_at(lat=location.latitude, lng=location.longitude)
    print(f"[get_hora_data] Timezone: {tz_str}")

    date_obj = datetime.strptime(m_date, "%Y-%m-%d")
    match_dt = datetime.combine(date_obj, datetime.strptime(m_time, "%H:%M").time())
    print(f"[get_hora_data] Match Datetime: {match_dt}")

    loc = LocationInfo(latitude=location.latitude, longitude=location.longitude, timezone=tz_str)
    s = sun(loc.observer, date=date_obj, tzinfo=loc.timezone)
    sunrise = s["sunrise"].replace(tzinfo=None)
    print(f"[get_hora_data] Sunrise: {sunrise}")

    if match_dt < sunrise:
        sunrise -= timedelta(days=1)
        print(f"[get_hora_data] Adjusted Sunrise (match before sunrise): {sunrise}")

    hours = int((match_dt - sunrise).total_seconds() // 3600)
    weekday = match_dt.strftime("%A")
    print(f"[get_hora_data] Hours since sunrise: {hours}, Weekday: {weekday}")

    seq = ["Saturn","Jupiter","Mars","Sun","Venus","Mercury","Moon"]
    rulers = {"Sunday":"Sun","Monday":"Moon","Tuesday":"Mars","Wednesday":"Mercury",
              "Thursday":"Jupiter","Friday":"Venus","Saturday":"Saturn"}
    v_map = {"Sun":1,"Moon":2,"Mars":9,"Mercury":5,"Jupiter":3,"Venus":6,"Saturn":8}

    hora_lord = seq[(seq.index(rulers[weekday]) + hours) % 7]
    print(f"[get_hora_data] Hora Lord: {hora_lord}, Value: {v_map[hora_lord]}")
    return hora_lord, v_map[hora_lord], weekday

# -----------------------------
# 3. MAIN EXECUTION ENGINE
# -----------------------------
print("--- SANJEEV PREDICTION ENGINE PRESENTS---")
m_date = input("Match Date (YYYY-MM-DD): ")
m_time = input("Match Time (HH:MM): ")
venue = input("Venue: ")
tA_name = input("Team A Name: ")
tA_capt = input("Team A Captain: ")
tA_dob = input("Team A Capt DOB (YYYY-MM-DD): ")
tB_name = input("Team B Name: ")
tB_capt = input("Team B Captain: ")
tB_dob = input("Team B Capt DOB (YYYY-MM-DD): ")

print("\n[DEBUG] Getting Hora & Weekday Info")
h_lord, h_val, w_day = get_hora_data(m_date, m_time, venue)
w_val = {"Sunday":1,"Monday":2,"Tuesday":9,"Wednesday":5,"Thursday":3,"Friday":6,"Saturday":8}[w_day]
day_hora_power = w_val + h_val
print(f"[DEBUG] Weekday Value: {w_val}, Hora Value: {h_val}, Day+Hora Power: {day_hora_power}")

print("\n[DEBUG] Calculating Date Numerology")
dt_obj = datetime.strptime(m_date, "%Y-%m-%d")
date_score = sum(int(d) for d in f"{dt_obj.day}{dt_obj.month}{dt_obj.year}") + dt_obj.day + 90
print(f"[DEBUG] Date Score: {date_score}")

print("\n[DEBUG] Calculating Destiny Sync")
m_dest = reduce_to_single_digit(sum(map(int, m_date.replace("-",""))))
a_dest = reduce_to_single_digit(sum(map(int, tA_dob.replace("-",""))))
b_dest = reduce_to_single_digit(sum(map(int, tB_dob.replace("-",""))))
a_sync = reduce_to_single_digit(m_dest + a_dest)
b_sync = reduce_to_single_digit(m_dest + b_dest)
print(f"[DEBUG] Match Destiny: {m_dest}, TeamA Destiny: {a_dest}, TeamB Destiny: {b_dest}")
print(f"[DEBUG] TeamA Sync: {a_sync}, TeamB Sync: {b_sync}")

print("\n[DEBUG] Calculating Personal Vibration")
a_pv = reduce_to_single_digit(a_sync + h_val)
b_pv = reduce_to_single_digit(b_sync + h_val)
print(f"[DEBUG] TeamA PV: {a_pv}, TeamB PV: {b_pv}")

print("\n[DEBUG] Calculating Name Numerology")
a_chal = chaldean_name_number(tA_name) + chaldean_name_number(tA_capt)
b_chal = chaldean_name_number(tB_name) + chaldean_name_number(tB_capt)
a_pyth = pythagorean_name_number(tA_name)
b_pyth = pythagorean_name_number(tB_name)
print(f"[DEBUG] TeamA Chaldean: {a_chal}, Pythagorean: {a_pyth}")
print(f"[DEBUG] TeamB Chaldean: {b_chal}, Pythagorean: {b_pyth}")

print("\n[DEBUG] Calculating Lo Shu Strength")
a_ls = lo_shu_strength([a_sync, day_hora_power])
b_ls = lo_shu_strength([b_sync, day_hora_power])
print(f"[DEBUG] TeamA Lo Shu: {a_ls}, TeamB Lo Shu: {b_ls}")

print("\n[DEBUG] Summing Internal Power")
team_a_internal = day_hora_power + (date_score % 10) + a_sync + a_pv + a_chal + a_pyth + a_ls
team_b_internal = day_hora_power + (date_score % 10) + b_sync + b_pv + b_chal + b_pyth + b_ls
print(f"[DEBUG] TeamA Internal: {team_a_internal}, TeamB Internal: {team_b_internal}")

print("\n[DEBUG] Applying Randomized Simulations")
random.seed(7)
team_a_internal += random.choice([0,1])
team_b_internal += random.choice([0,1])
random.seed(11)
team_a_internal += random.choice([0,1])
team_b_internal += random.choice([0,1])
print(f"[DEBUG] TeamA after simulations: {team_a_internal}, TeamB after simulations: {team_b_internal}")

print("\n[DEBUG] QMDJ Palace & Gate Logic")
palace = [1,2,3,4,5,6,7,8,9]
gates = ["Open","Rest","Life","Harm","Shock","Delay","Scenery","Fear"]
harmful = ["Harm","Shock","Fear","Delay"]

a_gate = gates[palace[int(team_a_internal % 9)] % 8]
b_gate = gates[palace[int(team_b_internal % 9)] % 8]
print(f"[DEBUG] TeamA Gate: {a_gate}, TeamB Gate: {b_gate}")

print("\n[DEBUG] Determining Internal Favourite")
internal_fav = tA_name if team_a_internal > team_b_internal else tB_name
final_winner = internal_fav

if internal_fav == tA_name and a_gate in harmful:
    final_winner = tB_name
    q_status = f"Flip due to {a_gate} gate"
elif internal_fav == tB_name and b_gate in harmful:
    final_winner = tA_name
    q_status = f"Flip due to {b_gate} gate"
else:
    q_status = "Confirmed"

print("\n" + "="*40)
print(f"RESULT FOR: {venue}")
print(f"Hora Lord: {h_lord} ({h_val})")
print(f"Internal Favourite: {internal_fav}")
print(f"QMDJ Status: {q_status}")
print(f"FINAL MATCH WINNER: {final_winner}")
print("="*40)

print("\n[DEBUG] Checking Match_Analysis.xlsx (if exists)")
if os.path.exists("Match_Analysis.xlsx"):
    try:
        df = pd.read_excel("Match_Analysis.xlsx")
        if 'Winner' in df.columns and not df['Winner'].isnull().all():
            history = df.dropna(subset=['Winner'])
            print(f"\n--- AUDIT REPORT (Total: {len(history)} Matches) ---")
            print(history.head())
    except Exception as e:
        print(f"\nExcel Read Error: {e}")
