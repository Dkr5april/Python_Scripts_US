import swisseph as swe
from datetime import datetime, timedelta
from pynput import keyboard
from rich.live import Live
from rich.table import Table
from rich.panel import Panel
from rich.layout import Layout
import time

# ---------------- CONFIG & NATAL DATA ----------------
swe.set_ephe_path("./ephe")
PLANET_LIT = ["Ke", "Ve", "Su", "Mo", "Ma", "Ra", "Ju", "Sa", "Me"]
DASHA_YEARS = [7, 20, 6, 10, 7, 18, 16, 19, 17]

# Fixed Natal Data from RVA Software
NAME = "Koteswararao"
DOB, TOB = "05/04/1979", "16:55:00"
B_LAT, B_LON = 16.11, 80.91

class KPEngine:
    def __init__(self):
        self.view_date = datetime.now()
        swe.set_sid_mode(swe.SIDM_KRISHNAMURTI) # KP New Ayanamsa
        d, m, y = map(int, DOB.split("/"))
        hh, mm, ss = map(int, TOB.split(":"))
        # IST to UTC Adjustment
        utc_hour = (hh + mm/60 + ss/3600) - 5.5
        self.njd = swe.julday(y, m, d, utc_hour)
        
        # Natal Positions for Collision Analysis
        self.n_pos = {}
        for pid, nm in [(0,"Su"),(1,"Mo"),(2,"Me"),(3,"Ve"),(4,"Ma"),(5,"Ju"),(6,"Sa"),(11,"Ra")]:
            res, _ = swe.calc_ut(self.njd, pid, swe.FLG_SWIEPH | swe.FLG_SIDEREAL)
            self.n_pos[nm] = res[0]
        self.n_pos["Ke"] = (self.n_pos["Ra"] + 180.0) % 360

    def get_dasha_at(self, target_dt):
        t_jd = swe.julday(target_dt.year, target_dt.month, target_dt.day, target_dt.hour + target_dt.minute/60.0)
        moon_lon = self.n_pos["Mo"] # ~93.29 Cancer
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
        # Time Machine Logic: Adjust cycle for Past or Future
        while t_jd > (check_start + cycle): check_start += cycle
        while t_jd < check_start: check_start -= cycle
        return recurse(check_start, cycle, lord_id, 0)

# Instantiate the Engine
engine = KPEngine()

# ---------------- UI & COLLISION LOGIC ----------------
def get_progression_table():
    table = Table(title=f"8-HOUR ANALYSIS: DASHAS & TRANSIT COLLISIONS", expand=True, border_style="cyan")
    table.add_column("Time (IST)", style="yellow", width=10)
    table.add_column("6-Level Dasha Lord (Lord-Sub-SubSub...)", style="white")
    table.add_column("Collisions (Transit hits Natal < 1°)", style="bold red")

    for i in range(9):
        dt = engine.view_date + timedelta(hours=i)
        dasha_list = engine.get_dasha_at(dt)
        dasha_str = "-".join(dasha_list)
        
        # Scan for planetary collisions at this hour
        hits = []
        t_jd = swe.julday(dt.year, dt.month, dt.day, dt.hour + dt.minute/60.0)
        for pid, nm in [(0,"Su"),(1,"Mo"),(2,"Me"),(3,"Ve"),(4,"Ma"),(5,"Ju"),(6,"Sa"),(11,"Ra")]:
            res, _ = swe.calc_ut(t_jd, pid, swe.FLG_SWIEPH | swe.FLG_SIDEREAL)
            # Compare Transit (res[0]) to Natal (engine.n_pos[nm])
            if abs(res[0] - engine.n_pos[nm]) < 1.0:
                hits.append(f"{nm}")
        
        table.add_row(dt.strftime("%H:%M"), dasha_str, ", ".join(hits) if hits else "---")
    return table

def make_layout():
    layout = Layout()
    layout.split_column(
        Layout(Panel(f"KP TIME MACHINE V35 | ANALYZING: {engine.view_date.strftime('%d-%m-%Y %H:%M')}\n[D] Jump to Date | [Arrows] Step +/- 1hr | [Q] Quit", style="bold white on blue"), size=4),
        Layout(get_progression_table())
    )
    return layout

# ---------------- RUNTIME ----------------
exit_flag = False
def on_press(key):
    global exit_flag
    try:
        if key == keyboard.Key.right: engine.view_date += timedelta(hours=1)
        elif key == keyboard.Key.left: engine.view_date -= timedelta(hours=1)
        elif hasattr(key, 'char'):
            if key.char == 'q': exit_flag = True
            if key.char == 'd':
                # No 'Live' update during input to prevent screen flicker
                new_date = input("\nEnter Analysis Date (DD/MM/YYYY HH:MM): ")
                try: engine.view_date = datetime.strptime(new_date, "%d/%m/%Y %H:%M")
                except: print("Invalid Format! Use DD/MM/YYYY HH:MM")
    except: pass

listener = keyboard.Listener(on_press=on_press)
listener.start()

try:
    with Live(make_layout(), refresh_per_second=2, screen=True) as live:
        while not exit_flag:
            live.update(make_layout())
            time.sleep(0.5)
finally:
    listener.stop()