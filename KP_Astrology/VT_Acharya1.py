import swisseph as swe
from datetime import datetime, timedelta

class RVAFinalEngine:
    def __init__(self, lat, lon, horary_num):
        self.lat, self.lon = lat, lon
        self.horary_num = horary_num
        # Force KP NEW Ayanamsa
        swe.set_sid_mode(swe.SIDM_KRISHNAMURTI)
        self.PLANETS = ["Ke","Ve","Su","Mo","Ma","Ra","Ju","Sa","Me"]
        self.YRS = [7, 20, 6, 10, 7, 18, 16, 19, 17]
        self.SGLS = ["Ma","Ve","Me","Mo","Su","Me","Ve","Ma","Ju","Sa","Sa","Ju"]

    def get_horary_seed(self):
        """Calculates exact degree for Horary 23"""
        segments = []
        start = 0.0
        for star in range(27):
            for sub in range(9):
                idx = (star + sub) % 9
                length = (self.YRS[idx] / 120.0) * (360/27)
                segments.append(start)
                start += length
        return segments[self.horary_num - 1]

    def get_lords(self, lon):
        """High precision SGL-STL-SBL-SSL extraction"""
        lon = lon % 360  # Critical: Ensure wrapping at 360
        sgl = self.SGLS[int(lon // 30) % 12]
        nak_len = 360/27
        star_idx = int(lon // nak_len) % 9
        stl = self.PLANETS[star_idx]
        rem = lon % nak_len
        acc = 0
        for i in range(9):
            idx = (star_idx + i) % 9
            part = (self.YRS[idx] / 120) * nak_len
            if acc + part >= rem:
                sbl = self.PLANETS[idx]
                ss_rem, ss_acc = rem - acc, 0
                for j in range(9):
                    ss_idx = (idx + j) % 9
                    ss_part = (self.YRS[ss_idx] / 120) * part
                    if ss_acc + ss_part >= ss_rem:
                        ssl = self.PLANETS[ss_idx]
                        return [sgl, stl, sbl, ssl]
                    ss_acc += ss_part
            acc += part
        return ["?", "?", "?", "?"]

    def run(self, ref_dt, start_dt, end_dt):
        # 1. Capture Reference Sky Lagna
        jd_ref = swe.julday(ref_dt.year, ref_dt.month, ref_dt.day, 
                            ref_dt.hour + ref_dt.minute/60 + ref_dt.second/3600 - 5.5)
        cusps_ref, _ = swe.houses_ex(jd_ref, self.lat, self.lon, b'P', swe.FLG_SIDEREAL)
        
        # 2. Set the Fixed Seed Houses
        seed_h1 = self.get_horary_seed()
        # The 12th house is a fixed distance from the 1st house in the horary chart
        h12_offset = (cusps_ref[11] - cusps_ref[0]) % 360
        seed_h12 = (seed_h1 + h12_offset) % 360
        
        print(f"Fixed Seed H12: {seed_h12:.4f} (Pisces Area)")
        print("-" * 40)

        curr = start_dt
        last_lords = None
        while curr <= end_dt:
            jd_now = swe.julday(curr.year, curr.month, curr.day, 
                                curr.hour + curr.minute/60 + curr.second/3600 - 5.5)
            cusps_now, _ = swe.houses_ex(jd_now, self.lat, self.lon, b'P', swe.FLG_SIDEREAL)
            
            # Rotation Travel: How far the sky moved since 12:49:50
            travel = (cusps_now[0] - cusps_ref[0]) % 360
            
            # The Live Moving 12th House
            target_pos = (seed_h12 + travel) % 360
            lords = self.get_lords(target_pos)

            if last_lords is None or lords != last_lords:
                print(f"{curr.strftime('%H:%M:%S')} | 12H: {'-'.join(lords)}")
                last_lords = lords
            curr += timedelta(seconds=1)

if __name__ == "__main__":
    # COORDS: Hyderabad
    engine = RVAFinalEngine(17.40, 78.47, 23)
    ref = datetime(2026, 1, 13, 12, 49, 50)
    start = datetime(2026, 1, 13, 19, 30, 0)
    end = datetime(2026, 1, 13, 19, 40, 0)
    engine.run(ref, start, end)