from datetime import datetime, timedelta

class DasaEngine:
    def __init__(self):
        self.dasa_years = {
            "Ketu": 7, "Venus": 20, "Sun": 6, "Moon": 10,
            "Mars": 7, "Rahu": 18, "Jupiter": 16, "Saturn": 19, "Mercury": 17
        }
        self.order = ["Ketu", "Venus", "Sun", "Moon", "Mars", "Rahu", "Jupiter", "Saturn", "Mercury"]
        self.total_cycle = 120

    def calculate_dasa_tree(self, moon_longitude, birth_dt, max_depth=3):
        nak_index = int(moon_longitude / 13.333333333)
        elapsed_in_nak = moon_longitude % 13.333333333
        
        lord_idx = nak_index % 9
        lord = self.order[lord_idx]
        total_dasa = self.dasa_years[lord]
        
        spent_ratio = elapsed_in_nak / 13.333333333
        remaining_years = total_dasa * (1 - spent_ratio)
        
        timeline = []
        # Level 1 (Mahadasa) ప్రారంభం
        self._build_tree(timeline, lord, remaining_years, birth_dt, 1, max_depth)
        return timeline

    def _build_tree(self, timeline, current_lord, duration_years, start_dt, current_level, max_depth):
        if current_level > max_depth:
            return

        end_dt = self._add_years(start_dt, duration_years)
        
        timeline.append({
            "level": current_level,
            "lord": current_lord,
            "start": start_dt,
            "end": end_dt
        })

        if current_level < max_depth:
            idx = self.order.index(current_lord)
            # తర్వాతి లెవెల్ కోసం Start Date అనేది ప్రస్తుత లెవెల్ ప్రారంభంతో మొదలవ్వాలి
            next_start_dt = start_dt
            
            for i in range(9):
                sub_lord = self.order[(idx + i) % 9]
                sub_duration = (self.dasa_years[sub_lord] * duration_years) / self.total_cycle
                
                self._build_tree(timeline, sub_lord, sub_duration, next_start_dt, current_level + 1, max_depth)
                
                # తర్వాతి సబ్-లార్డ్ యొక్క Start Date ని అప్‌డేట్ చేయడం
                next_start_dt = self._add_years(next_start_dt, sub_duration)

    def _add_years(self, d, years):
        return d + timedelta(days=years * 360)