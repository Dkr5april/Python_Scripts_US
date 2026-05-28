import swisseph as swe

class TriVedaMatrix:
    def __init__(self, match_name, yr, mn, dy, hr, mi, lat, lon):
        self.match_name = match_name
        ut_hour = hr - 5.5 
        self.jd = swe.julday(yr, mn, dy, ut_hour)
        self.lat = lat
        self.lon = lon

    def get_positions(self):
        # The Brain: Calculating exact planetary coordinates
        planets = {"Mars": 4, "Saturn": 6, "Ketu": 11, "Sun": 0, "Mercury": 2}
        pos = {}
        print("\n[DEBUG] Calculating Planetary Longitudes...")
        for name, id in planets.items():
            res, ret = swe.calc_ut(self.jd, id)
            pos[name] = res[0]
            print(f" > {name}: {pos[name]:.2f}°")
            
        # The Brain: Calculating Mandi (Vedic Logic)
        pos["Mandi"] = (pos["Saturn"] + 155.5) % 360
        print(f" > MANDI (Calculated): {pos['Mandi']:.2f}°")
        return pos

    def predict(self, ray_count, k_10_seal, sl_11_retro, qmdj_void):
        pos = self.get_positions()
        print("\n[DEBUG] Running Logic Layer Verification...")
        
        # --- RULE 1: JAMAKKOL FINAL SEAL ---
        print(f" Check 1: Kavipu 10th Seal Status -> {'BLOCKED' if k_10_seal else 'CLEAR'}")
        if k_10_seal:
            return "WIN BLOCKED", "Kavipu in 10th House (Jamakkol Seal)"

        # --- RULE 2: MANDI COLLAPSE (100% CERTAINTY) ---
        print(" Check 2: Mandi/Innings Collapse Analysis...")
        mandi_impact = False
        for p in ["Mars", "Saturn", "Ketu"]:
            diff = abs(pos[p] - pos["Mandi"])
            print(f"  - Distance {p} to Mandi: {diff:.2f}°")
            if diff < 3.25:
                mandi_impact = True
                print(f"  [!] CRITICAL: {p} is in the Mandi Zone!")

        print(f"  - Ray Count: {ray_count}")
        if mandi_impact and ray_count < 8:
            return "COLLAPSE / LOSS", f"Mandi Impact detected with Low Rays ({ray_count})"

        # --- RULE 3: KP ACCURACY ---
        print(f" Check 3: KP 11th Sub-Lord Movement -> {'RETROGRADE' if sl_11_retro else 'DIRECT'}")
        if sl_11_retro:
            return "REVERSAL / LOSS", "11th Sub-Lord is Retrograde (Success Withdrawn)"

        # --- RULE 4: QMDJ VOID ---
        print(f" Check 4: QMDJ Palace Energy -> {'VOID' if qmdj_void else 'ACTIVE'}")
        if qmdj_void:
            return "FAILURE", "Victory Palace is in VOID (Shunyata/Energy Leak)"

        return "VICTORY", "All Layers (KP, Jamakkol, Mandi) passed successfully"

# ============================================================
# DATA INPUT
# ============================================================
if __name__ == "__main__":
    my_match = TriVedaMatrix(
        match_name="Team A vs Team B",
        yr=2026, mn=1, dy=15, hr=19, mi=30, 
        lat=16.50, lon=80.64                
    )

    # Change these values to see the 'Brain' change its decision
    result, reason = my_match.predict(
        ray_count=7,        
        k_10_seal=False,    
        sl_11_retro=False,  
        qmdj_void=False     
    )

    print("\n" + "="*50)
    print(f"FINAL REPORT: {my_match.match_name}")
    print(f"RESULT      : {result}")
    print(f"REASON      : {reason}")
    print("="*50 + "\n")