import swisseph as swe
import time
from datetime import datetime, timedelta
from pynput import keyboard
from rich.live import Live
from rich.table import Table
from rich.panel import Panel
from rich.layout import Layout

# ---------------- CONFIG ----------------
swe.set_ephe_path("./ephe")
PLANET_LIT = ["Ke", "Ve", "Su", "Mo", "Ma", "Ra", "Ju", "Sa", "Me"]
DASHA_YEARS = [7, 20, 6, 10, 7, 18, 16, 19, 17]

# Hardcoded Natal Data (Fixed Foundation)
DOB, TOB = "05/04/1979", "16:55:00"
B_LAT, B_LON = 16.11, 80.91

class KPEngineV37:
    def __init__(self):
        self.view_date = datetime.now()
        swe.set_sid_mode(swe.SIDM_KRISHNAMURTI)
        d, m, y = map(int, DOB.split("/"))
        hh, mm, ss = map(int, TOB.split(":"))
        utc_hour = (hh + mm/60 + ss/3600) - 5.5
        self.njd = swe.julday(y, m, d, utc_hour)
        
        self.n_pos = {}
        for pid, nm in [(0,"Su"),(1,"Mo"),(2,"Me"),(3,"Ve"),(4,"Ma"),(5,"Ju"),(6,"Sa"),(11,"Ra")]:
            res, _ = swe.calc_ut(self.njd, pid, swe.FLG_SWIEPH | swe.FLG_SIDEREAL)
            self.n_pos[nm] = res[0]
        self.n_pos["Ke"] = (self.n_pos["Ra"] + 180.0) % 360

    def get_dasha_at(self, target_dt):
        t_jd = swe.julday(target_dt.year, target_dt.month, target_dt.day, target_dt.hour + target_dt.minute/60.0 + target_dt.second/3600.0)
        moon_lon = self.n_pos["Mo"]
        one_star = 800 / 60.0
        star_idx = int(moon_lon / one_star)
        lord_id = star_idx % 9
        rem_deg = one_star - (moon_lon % one_star)
        m_start = self.njd - (((DASHA_YEARS[lord_id] - (rem_deg / one_star * DASHA_YEARS[lord_id]))) * 365.2425)
        
        def recurse(start, total_days, p_idx, depth):
            if depth == 6: return []
            curr = start
            for i in range(9):
                idx = (p_idx + i) % 9
                dur = (DASHA_YEARS[idx] / 120.0) * total_days
                if curr <= t_jd < (curr + dur + 0.0000001):
                    return [PLANET_LIT[idx]] + recurse(curr, dur, idx, depth + 1)
                curr += dur
            return ["?"]
        
        cycle = 120 * 365.2425
        check_start = m_start
        while t_jd > (check_start + cycle): check_start += cycle
        while t_jd < check_start: check_start -= cycle
        return recurse(check_start, cycle, lord_id, 0)

engine = KPEngineV37()

def get_event_table():
    table = Table(title=f"SCANNED EVENTS (8h Window)", expand=True, border_style="bold cyan")
    table.add_column("Time (IST)", style="yellow", width=10)
    table.add_column("6-Level Dasha", style="white")
    table.add_column("Interesting Findings (Aspect Hits)", style="bold magenta")

    last_dasha = None
    # Scan every 10 seconds for 8 hours (2880 points)
    # We only show the row if something "Interesting" happens
    for i in range(2881):
        dt = engine.view_date + timedelta(seconds=i*10)
        d_list = engine.get_dasha_at(dt)
        d_str = "-".join(d_list)
        
        findings = []
        t_jd = swe.julday(dt.year, dt.month, dt.day, dt.hour + dt.minute/60.0 + dt.second/3600.0)
        
        for pid, nm in [(0,"Su"),(1,"Mo"),(2,"Me"),(3,"Ve"),(4,"Ma"),(5,"Ju"),(6,"Sa"),(11,"Ra")]:
            res, _ = swe.calc_ut(t_jd, pid, swe.FLG_SWIEPH | swe.FLG_SIDEREAL)
            t_lon = res[0]
            n_lon = engine.n_pos[nm]
            diff = abs(t_lon - n_lon) % 360
            
            # COLLISION LOGIC (Conjunction, Opposition, Trine)
            if diff < 0.05 or abs(diff - 180) < 0.05:
                findings.append(f"T-{nm} hits N-{nm} (Axis)")
            elif abs(diff - 120) < 0.05 or abs(diff - 240) < 0.05:
                findings.append(f"T-{nm} Trine N-{nm}")

        # Interesting Filter: Dasha change OR Aspect Hit
        if d_str != last_dasha or findings:
            event_desc = " | ".join(findings) if findings else "--- Dasha Transition ---"
            table.add_row(dt.strftime("%H:%M:%S"), d_str, event_desc)
            last_dasha = d_str
            
    return table

def make_layout():
    layout = Layout()
    layout.split_column(
        Layout(Panel(f"KP CHRONOS V37 | NATAL: 05-04-1979 | VIEWING TRANSIT: {engine.view_date.strftime('%d-%m-%Y %H:%M')}\n[D] Jump Transit Date | [Arrows] +/- 1h | [Q] Quit", style="white on blue"), size=4),
        Layout(get_event_table())
    )
    return layout

# ---------------- CONTROLS ----------------
exit_flag = False
def on_press(key):
    global exit_flag
    try:
        if key == keyboard.Key.right: engine.view_date += timedelta(hours=1)
        elif key == keyboard.Key.left: engine.view_date -= timedelta(hours=1)
        elif hasattr(key, 'char'):
            if key.char == 'q': exit_flag = True
            if key.char == 'd':
                new_date = input("\nEnter Transit Date (DD/MM/YYYY HH:MM): ")
                try: engine.view_date = datetime.strptime(new_date, "%d/%m/%Y %H:%M")
                except: pass
    except: pass

listener = keyboard.Listener(on_press=on_press); listener.start()

try:
    with Live(make_layout(), refresh_per_second=2, screen=True) as live:
        while not exit_flag:
            live.update(make_layout())
            time.sleep(0.5)
finally:
    listener.stop()