from datetime import datetime, timedelta
import pandas as pd

class DasaEngine:
    def __init__(self):
        self.dasa_years = {
            "Ketu": 7, "Venus": 20, "Sun": 6, "Moon": 10,
            "Mars": 7, "Rahu": 18, "Jupiter": 16, "Saturn": 19, "Mercury": 17
        }
        self.order = ["Ketu", "Venus", "Sun", "Moon", "Mars", "Rahu", "Jupiter", "Saturn", "Mercury"]
        self.total_cycle = 120

    def calculate_dasa_tree(self, moon_longitude, birth_dt, max_depth=3):
        # Constants for precision
        SOLAR_DAYS_PER_DASA_YEAR = 365.2425 / 360.0
        
        # 1. Calculate which lord is active and the elapsed portion
        nak_index = int(moon_longitude / 13.333333333)
        elapsed_in_nak = moon_longitude % 13.333333333
        
        lord_idx = nak_index % 9
        current_lord = self.order[lord_idx]
        total_lord_years = self.dasa_years[current_lord]
        
        # Calculate years spent before birth
        spent_ratio = elapsed_in_nak / 13.333333333
        years_spent = total_lord_years * spent_ratio
        
        # 2. Backdate the start of the current Mahadasa
        # Use the conversion ratio to ensure we align with solar calendar dates
        days_spent = years_spent * 360.0 * SOLAR_DAYS_PER_DASA_YEAR
        start_of_current_mahadasha = birth_dt - timedelta(days=days_spent)
        
        timeline = []
        current_idx = self.order.index(current_lord)
        
        # 3. Track absolute time to prevent compounding errors
        # We store cumulative days as a float to maintain precision
        cumulative_days = 0.0
        
        for i in range(9):
            idx = (current_idx + i) % 9
            lord = self.order[idx]
            duration_years = self.dasa_years[lord]
            
            # Start of this lord = start_of_mahadasha + time elapsed so far
            lord_start = start_of_current_mahadasha + timedelta(days=cumulative_days)
            
            # Build the tree for this lord
            self._build_tree(timeline, lord, duration_years, lord_start, 1, max_depth)
            
            # Update cumulative days using the solar-adjusted duration
            cumulative_days += (duration_years * 360.0 * SOLAR_DAYS_PER_DASA_YEAR)
            
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
            next_start_dt = start_dt
            
            for i in range(9):
                sub_lord = self.order[(idx + i) % 9]
                sub_duration = (self.dasa_years[sub_lord] * duration_years) / self.total_cycle
                
                self._build_tree(timeline, sub_lord, sub_duration, next_start_dt, current_level + 1, max_depth)
                
                next_start_dt = self._add_years(next_start_dt, sub_duration)
                
    def get_structured_timeline(self, timeline):
        # Sort by level first, then start date. 
        # This ensures parents are ALWAYS processed before their children.
        sorted_dasa = sorted(timeline, key=lambda x: (x['level'], x['start']))
        
        for entry in sorted_dasa:
            # Unique ID
            entry['id'] = f"{entry['lord']}_{entry['start'].strftime('%Y%m%d%H%M%S')}_{entry['level']}"
            entry['parent_id'] = "" 
            
            # Find the direct parent
            if entry['level'] > 1:
                # Look backwards through the list for the parent
                for p in sorted_dasa:
                    if (p['level'] == entry['level'] - 1 and 
                        p['start'] <= entry['start'] and 
                        p['end'] >= entry['end']):
                        # Set parent_id to the most recent match
                        entry['parent_id'] = p['id']
        
        return sorted_dasa           
    

    def _add_years(self, d, years):
        # 360-day Savana year calculation
        return d + timedelta(days=years * 360)

    def get_active_dasa(self, timeline, target_dt):
        """
        Returns a list of active lords for a specific date (Maha, Bhukti, Antara).
        """
        active = []
        # Sort by level so we get Maha -> Bhukti -> Antara
        for entry in sorted(timeline, key=lambda x: x['level']):
            if entry['start'] <= target_dt <= entry['end']:
                active.append(entry)
        return active
        
    def get_dasa_at_level(self, timeline, target_dt, level):
        """Find the Dasa lord active at a specific hierarchy level for a date."""
        # Find all nodes that match the level and cover the date
        matches = [e for e in timeline if e['level'] == level and e['start'] <= target_dt <= e['end']]
        return matches[0] if matches else None

    def get_nested_breakdown(self, timeline, target_dt):
        """Returns the full path: Maha > Bhukti > Antara active at this date."""
        return [e for e in timeline if e['start'] <= target_dt <= e['end']]    

    # --- ADDED: UI and Export Utilities ---

    def get_dasa_window(self, timeline, target_dt, window_size=10):
        # Sort by level (ascending) then by start time
        sorted_timeline = sorted(timeline, key=lambda x: (x['level'], x['start']))
    
        # Filter to look for the active period at the highest level (Level 3 or whatever the deepest is)
        # This prevents the window from grabbing a Level 1 entry when you want a Level 3 entry
        deepest_level = max(e['level'] for e in timeline)
    
        for i, entry in enumerate(sorted_timeline):
            if entry['level'] == deepest_level and entry['start'] <= target_dt <= entry['end']:
                start_idx = max(0, i - 2)
                return sorted_timeline[start_idx : start_idx + window_size]
        return sorted_timeline[:window_size]
        
    def _add_years(self, d, years):
        return d + timedelta(days=years * 360)
    
    def export_custom_range(self, timeline, start_dt, delta, filename="Dasa_Export.xlsx"):
        """
        Exports Dasa levels to Excel based on a specific time range duration.
        """
        end_dt = start_dt + delta
        subset = [e for e in timeline if e['end'] >= start_dt and e['start'] <= end_dt]
        
        # Sort by start time for the Excel report so it reads chronologically
        subset.sort(key=lambda x: x['start'])
        
        df = pd.DataFrame([{
            "Level": e['level'],
            "Lord": e['lord'],
            "Start": e['start'].strftime("%d-%m-%Y %H:%M"),
            "End": e['end'].strftime("%d-%m-%Y %H:%M")
        } for e in subset])
        
        df.to_excel(filename, index=False)
        return filename
        
    def export_by_level(self, timeline, level_filter=None, filename="Dasa_Report.xlsx"):
        subset = timeline
        if level_filter:
            subset = [e for e in timeline if e['level'] == level_filter]
        
        # Sort by start date to ensure the "change of dasa" dates are chronological
        subset.sort(key=lambda x: x['start'])
        
        df = pd.DataFrame([{
            "Level": e['level'],
            "Lord": e['lord'],
            "Start": e['start'].strftime("%d-%m-%Y"),
            "End": e['end'].strftime("%d-%m-%Y")
        } for e in subset])
        
        df.to_excel(filename, index=False)
        
    def get_active_dasa_display(self, timeline, target_dt):
        """
        Returns a formatted string of the current active hierarchy 
        for the top-line UI display.
        Example: "1:Venus | 2:Sun | 3:Ketu"
        """
        active = self.get_active_dasa(timeline, target_dt)
        return " | ".join([f"{e['level']}:{e['lord']}" for e in active])