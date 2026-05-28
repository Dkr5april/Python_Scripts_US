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

# ---------------- INITIAL INPUTS ----------------
console.clear()
console.print("[bold cyan]=== KP CHRONOS V39: PRECISION ANALYZER ===[/bold cyan]\n")

name = "Koteswararao"
dob = "05/04/1979"
tob = "16:55:00"
birth_city = "Challapalli, India"

# Hardcoded for stability based on your RVA PDF
B_LAT, B_LON = 16.11, 80.91

class KPEngineV39:
    def __init__(self):
        self.view_date = datetime.now()
        self.request_jump = False
        swe.set_sid_mode(swe.SIDM_KRISHNAMURTI)
        
        d, m, y = map(int, dob.split("/"))
        hh, mm, ss = map(int, tob.split(":"))
        utc_hour = (hh + mm/60 + ss/3600) - 5.5
        self.njd = swe.julday(y, m, d, utc_hour)
        
        # Natal Fixed Positions
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

engine = KPEngineV39()

# ---------------- RENDERING ----------------
def get_event_table():
    table = Table(title=f"8-HOUR SCAN | Start: {engine.view_date.strftime('%H:%M:%S')}", expand=True, border_style="bold green")
    table.add_column("Time (IST)", style="yellow", width=12)
    table.add_column("6-Level Dasha Lord", style="white")
    table.add_column("KP Aspect Hits (Transit vs Natal)", style="bold magenta")

    last_dasha = None
    # Micro-scan every 2 minutes for 8 hours
    for i in range(241):
        dt = engine.view_date + timedelta(minutes=i*2)
        d_str = "-".join(engine.get_dasha_at(dt))
        
        findings = []
        t_jd = swe.julday(dt.year, dt.month, dt.day, dt.hour + dt.minute/60.0)
        for pid, nm in [(0,"Su"),(1,"Mo"),(2,"Me"),(3,"Ve"),(4,"Ma"),(5,"Ju"),(6,"Sa"),(11,"Ra")]:
            res, _ = swe.calc_ut(t_jd, pid, swe.FLG_SWIEPH | swe.FLG_SIDEREAL)
            diff = abs(res[0] - engine.n_pos[nm]) % 360
            
            # Aspect Logic: Conjunction (0), Opposition (180), Trine (120)
            if diff < 0.3 or abs(diff - 180) < 0.3:
                findings.append(f"T-{nm} hit N-{nm}")
            elif abs(diff - 120) < 0.3 or abs(diff - 240) < 0.3:
                findings.append(f"T-{nm} Trine N-{nm}")

        if d_str != last_dasha or findings:
            alert = " | ".join(findings) if findings else "[dim]--- Transition ---[/]"
            table.add_row(dt.strftime("%H:%M:%S"), d_str, alert)
            last_dasha = d_str
    return table

def make_layout():
    layout = Layout()
    layout.split_column(
        Layout(Panel(f"KP V39 | NATAL: {dob} | VIEWING: {engine.view_date.strftime('%d-%m-%Y %H:%M')}\n[J] JUMP DATE | [ARROWS] STEP 15m | [Q] QUIT", style="bold white on blue"), size=4),
        Layout(get_event_table())
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
            if key.char == 'j': engine.request_jump = True
            if key.char == 'q': exit_flag = True
    except: pass

listener = keyboard.Listener(on_press=on_press)
listener.start()

# ---------------- MAIN LOOP ----------------
try:
    with Live(make_layout(), refresh_per_second=4, screen=True) as live:
        while not exit_flag:
            if engine.request_jump:
                live.stop()
                console.print("\n" * 2)
                target = console.input("[bold yellow]Jump to Transit Date (DD/MM/YYYY HH:MM): [/]")
                try: 
                    engine.view_date = datetime.strptime(target, "%d/%m/%Y %H:%M")
                except: 
                    console.print("[red]Invalid Format![/]")
                    time.sleep(1)
                engine.request_jump = False
                live.start()
            
            live.update(make_layout())
            time.sleep(0.1)
finally:
    listener.stop()