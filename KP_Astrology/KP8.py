import swisseph as swe
import time
import sys
import os
from datetime import datetime, timedelta
from pynput import keyboard
from rich.live import Live
from rich.table import Table
from rich.panel import Panel
from rich.layout import Layout
from rich.console import Console

# ---------------- CONFIG & CONSTANTS ----------------
swe.set_ephe_path("./ephe")
console = Console()

PLANET_LIT = ["Ke", "Ve", "Su", "Mo", "Ma", "Ra", "Ju", "Sa", "Me"]
DASHA_YEARS = [7, 20, 6, 10, 7, 18, 16, 19, 17]

# ---------------- NATAL DATA (Koteswararao) ----------------
DOB_N, TOB_N = "05/04/1979", "16:55:00"
B_LAT, B_LON = 16.11, 80.91

class KPEngineV43:
    def __init__(self):
        # State & Toggles
        self.view_date = datetime.now()
        self.request_jump = False
        self.show_dasha = True
        self.show_aspects = True
        self.show_houses = True
        
        swe.set_sid_mode(swe.SIDM_KRISHNAMURTI)
        
        # Natal Setup
        d, m, y = map(int, DOB_N.split("/"))
        hh, mm, ss = map(int, TOB_N.split(":"))
        utc_hour = (hh + mm/60 + ss/3600) - 5.5
        self.njd = swe.julday(y, m, d, utc_hour)
        
        self.n_pos = {}
        for pid, nm in [(0,"Su"),(1,"Mo"),(2,"Me"),(3,"Ve"),(4,"Ma"),(5,"Ju"),(6,"Sa"),(11,"Ra")]:
            res, _ = swe.calc_ut(self.njd, pid, swe.FLG_SWIEPH | swe.FLG_SIDEREAL)
            self.n_pos[nm] = res[0]
        self.n_pos["Ke"] = (self.n_pos["Ra"] + 180.0) % 360

    def get_dasha_at(self, target_dt):
        t_jd = swe.julday(target_dt.year, target_dt.month, target_dt.day, 
                          target_dt.hour + target_dt.minute/60.0 + target_dt.second/3600.0)
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

engine = KPEngineV43()

# ---------------- RENDERING ----------------
def get_dashboard_table():
    table = Table(expand=True, border_style="bold green", header_style="bold yellow")
    table.add_column("Time (IST)", width=10)
    
    if engine.show_dasha:
        table.add_column("6-Level Dasha", style="white")
    if engine.show_houses:
        table.add_column("Transit Loc (H/Star)", style="bold cyan")
    if engine.show_aspects:
        table.add_column("KP Aspect Hits (T->N)", style="bold magenta")

    last_dasha = None
    ASPECT_MAP = {0: "Conj", 180: "Opp", 120: "Trine", 90: "Sqr", 60: "Sxt"}

    for i in range(241): # 8 hours, 2min steps
        dt = engine.view_date + timedelta(minutes=i*2)
        d_str = "-".join(engine.get_dasha_at(dt))
        
        findings_h = []
        findings_a = []
        t_jd = swe.julday(dt.year, dt.month, dt.day, dt.hour + dt.minute/60.0)
        
        for pid, nm in [(0,"Su"),(1,"Mo"),(2,"Me"),(3,"Ve"),(4,"Ma"),(5,"Ju"),(6,"Sa"),(11,"Ra")]:
            res, _ = swe.calc_ut(t_jd, pid, swe.FLG_SWIEPH | swe.FLG_SIDEREAL)
            t_lon = res[0]
            
            # Transit Meta
            t_star = PLANET_LIT[int(t_lon * 60 / 800) % 9]
            t_house = int(t_lon / 30) + 1
            
            # Comparison against all Natal points
            for natal_nm, n_lon in engine.n_pos.items():
                diff = abs(t_lon - n_lon) % 360
                if diff > 180: diff = 360 - diff
                
                for angle, label in ASPECT_MAP.items():
                    if abs(diff - angle) < 0.6: # Orb
                        findings_h.append(f"T-{nm} H{t_house}({t_star})")
                        findings_a.append(f"{label} N-{natal_nm}")

        if d_str != last_dasha or findings_a:
            row = [dt.strftime("%H:%M")]
            if engine.show_dasha: row.append(d_str)
            if engine.show_houses: row.append(" | ".join(list(set(findings_h))))
            if engine.show_aspects: row.append(" | ".join(list(set(findings_a))))
            
            # Filler if aspect is empty but dasha changed
            if not findings_a and d_str != last_dasha and engine.show_aspects:
                row[-1] = "[dim]--- Shift ---[/]"
                
            table.add_row(*row)
            last_dasha = d_str
            
    return table

def make_layout():
    layout = Layout()
    layout.split_column(
        Layout(Panel(f"KP COMMAND CENTER V43 | NATAL: {DOB_N} | TRANSIT: {engine.view_date.strftime('%d-%m-%Y %H:%M')}\n"
                     f"[D] Dasha:{engine.show_dasha} [A] Aspects:{engine.show_aspects} [H] Houses:{engine.show_houses} | [J] JUMP | [Q] QUIT", 
                     style="bold white on blue"), size=4),
        Layout(get_dashboard_table())
    )
    return layout

# ---------------- CONTROLS ----------------
exit_flag = False
def on_press(key):
    global exit_flag
    try:
        if key == keyboard.Key.right: engine.view_date += timedelta(minutes=15)
        elif key == keyboard.Key.left: engine.view_date -= timedelta(minutes=15)
        elif hasattr(key, 'char'):
            c = key.char.lower()
            if c == 'q': exit_flag = True
            if c == 'j': engine.request_jump = True
            if c == 'd': engine.show_dasha = not engine.show_dasha
            if c == 'a': engine.show_aspects = not engine.show_aspects
            if c == 'h': engine.show_houses = not engine.show_houses
    except: pass

listener = keyboard.Listener(on_press=on_press); listener.start()

# ---------------- MAIN ----------------
try:
    with Live(make_layout(), refresh_per_second=4, screen=True) as live:
        while not exit_flag:
            if engine.request_jump:
                live.stop()
                console.print("\n" * 2)
                target = console.input("[bold yellow]Jump to Transit Date (DD/MM/YYYY HH:MM): [/]")
                try: engine.view_date = datetime.strptime(target, "%d/%m/%Y %H:%M")
                except: pass
                engine.request_jump = False
                live.start()
            
            live.update(make_layout())
            time.sleep(0.1)
finally:
    listener.stop()