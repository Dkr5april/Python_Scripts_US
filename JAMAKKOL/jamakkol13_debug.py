import geocoder
from suntime import Sun
from datetime import datetime, timedelta

def run_interactive_gk_math():
    print("====================================================")
    print("   JAMAKKOL PRASANAM: DYNAMIC CALCULATION ENGINE    ")
    print("====================================================\n")

    # 1. AUTO-DETECT LOCATION
    g = geocoder.ip('me')
    lat, lng = g.latlng
    city = g.city if g.city else "Unknown Location"
    
    # 2. FETCH ASTRONOMICAL DATA
    sun = Sun(lat, lng)
    now = datetime.now()
    sr = sun.get_local_sunrise_time().replace(tzinfo=None)
    ss = sun.get_local_sunset_time().replace(tzinfo=None)

    # 3. INTERACTIVE VERIFICATION
    print(f"I have detected your location as: {city} ({lat}, {lng})")
    print(f"Calculated Sunrise : {sr.strftime('%H:%M:%S')}")
    print(f"Calculated Sunset  : {ss.strftime('%H:%M:%S')}")
    print("-" * 30)
    
    confirm = input("Are these timings correct? (Y/N): ").strip().upper()

    if confirm != 'Y':
        print("\n--- Manual Override ---")
        sr_input = input("Enter correct Sunrise (HH:MM:SS): ")
        ss_input = input("Enter correct Sunset (HH:MM:SS): ")
        
        # Update objects with user input
        today_date = now.strftime('%Y-%m-%d')
        sr = datetime.strptime(f"{today_date} {sr_input}", '%Y-%m-%d %H:%M:%S')
        ss = datetime.strptime(f"{today_date} {ss_input}", '%Y-%m-%d %H:%M:%S')

    # 4. GK DYNAMIC MATH (Divide Duration by 8)
    is_day = sr <= now <= ss
    
    if is_day:
        mode = "DAY"
        total_duration = ss - sr
        elapsed = now - sr
    else:
        mode = "NIGHT"
        if now >= ss:
            elapsed = now - ss
            tomorrow_sr = sun.get_local_sunrise_time(now + timedelta(days=1)).replace(tzinfo=None)
            total_duration = tomorrow_sr - ss
        else:
            yesterday_ss = sun.get_local_sunset_time(now - timedelta(days=1)).replace(tzinfo=None)
            elapsed = now - yesterday_ss
            total_duration = sr - yesterday_ss

    total_mins = total_duration.total_seconds() / 60
    each_jamam_mins = total_mins / 8
    
    elapsed_mins = elapsed.total_seconds() / 60
    current_jama_index = int(elapsed_mins // each_jamam_mins) + 1

    # 5. FINAL CALCULATION DISPLAY
    print("\n" + "="*40)
    print(f"FINAL CALCULATION DETAILS")
    print("="*40)
    print(f"Current Time       : {now.strftime('%H:%M:%S')}")
    print(f"Mode               : {mode}")
    print(f"Total {mode} Minutes : {total_mins:.2f} mins")
    print(f"One Jamam Length   : {each_jamam_mins:.2f} mins")
    print(f"Elapsed Time       : {elapsed_mins:.2f} mins")
    print(f"RUNNING JAMA NO    : {current_jama_index} of 8")
    print("="*40)

    return {
        "index": current_jama_index,
        "mode": mode,
        "mins_per_jama": each_jamam_mins
    }

if __name__ == "__main__":
    run_interactive_gk_math()