import swisseph as swe

# ============================================================
# MASTER CALCULATION ENGINE (Phase 1-4 Combined)
# ============================================================

class TriVedaMatrix:
    def __init__(self, match_name, yr, mn, dy, hr, mi, lat, lon):
        self.match_name = match_name
        # 1. Calculate Julian Day (Standardizing the Time)
        ut_hour = hr - 5.5 
        self.jd = swe.julday(yr, mn, dy, ut_hour)
        self.lat = lat
        self.lon = lon

    def get_positions(self):
        # Calculates precise locations of planets and Mandi
        planets = {"Mars": 4, "Saturn": 6, "Ketu": 11, "Sun": 0, "Mercury": 2}
        pos = {}
        for name, id in planets.items():
            res, ret = swe.calc_ut(self.jd, id)
            pos[name] = res[0]
        # Calculate Mandi for Collapse Factor
        pos["Mandi"] = (pos["Saturn"] + 155.5) % 360
        return pos

    def predict(self, ray_count, k_10_seal, sl_11_retro, qmdj_void):
        pos = self.get_positions()
        summary = []
        
        # --- RULE 1: JAMAKKOL FINAL SEAL ---
        if k_10_seal:
            return "WIN BLOCKED", "Kavipu in 10th House (Jamakkol Seal)"

        # --- RULE 2: MANDI COLLAPSE (100% CERTAINTY) ---
        mandi_impact = any(abs(pos[p] - pos["Mandi"]) < 3.25 for p in ["Mars", "Saturn", "Ketu"])
        if mandi_impact and ray_count < 8:
            return "COLLAPSE / LOSS", "Mandi Impact + Low Rays (< 8)"

        # --- RULE 3: KP ACCURACY ---
        if sl_11_retro:
            return "REVERSAL / LOSS", "11th Sub-Lord is Retrograde"

        # --- RULE 4: QMDJ VOID ---
        if qmdj_void:
            return "FAILURE", "Victory Palace is in VOID (Shunyata)"

        return "VICTORY", "All Layers (KP, Jamakkol, Mandi) are Positive"

# ============================================================
# STEP 1: ENTER YOUR DATA BELOW
# ============================================================
if __name__ == "__main__":
    # A. Enter Match Details
    my_match = TriVedaMatrix(
        match_name="Team A vs Team B",
        yr=2026, mn=1, dy=15, hr=19, mi=30, # Date and Time
        lat=16.50, lon=80.64                # Place (Vijayawada)
    )

    # B. Enter your Chart Observations (Your "Gold" Inputs)
    # Check your KP/Jamakkol/QMDJ charts and fill these 4 values:
    result, reason = my_match.predict(
        ray_count=7,        # Enter Rays of Udayam Lord
        k_10_seal=False,    # Is Kavipu in 10th House? (True/False)
        sl_11_retro=False,  # Is 11th Sub-Lord Retrograde? (True/False)
        qmdj_void=False     # Is the Success Palace Void? (True/False)
    )

    # C. GET THE FINAL OUTPUT
    print("\n" + "="*40)
    print(f"REPORT FOR: {my_match.match_name}")
    print(f"PREDICTION: {result}")
    print(f"REASONING : {reason}")
    print("="*40 + "\n")