import swisseph as swe
import time
import sys
from datetime import datetime, timedelta
from pynput import keyboard
from rich.live import Live
from rich.table import Table
from rich.panel import Panel
from rich.layout import Layout
from rich.console import Console

swe.set_ephe_path("./ephe")
console = Console()

PLANET_LIT = ["Ke", "Ve", "Su", "Mo", "Ma", "Ra", "Ju", "Sa", "Me"]
DASHA_YEARS = [7, 20, 6, 10, 7, 18, 16, 19, 17]
DOB_N, TOB_N = "05/04/1979", "16:55:00"

class KPEngineV44:
    def __init__(self):
        self.view_date = datetime.now()
        self.request_jump = False
        self.is_paused = False  # PAUSE STATE
        self.show_dasha = True
        self.show_aspects = True
        self.show_houses = True
        swe.set_sid_mode(swe.SIDM_KRISHNAMURTI)
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
        t_jd = swe.julday(target_dt.year, target_dt.month, target_dt.day, target_dt.hour + target_dt.minute/60.0)
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

engine = KPEngineV44()

def get_dashboard_table():
    table = Table(expand=True, border_style="bold green")
    table.add_column("Time (IST)", width=10)
    if engine.show_dasha: table.add_column("6-Level Dasha", style="white")
    if engine.show_houses: table.add_column("Transit Loc (H/Star)", style="bold cyan")
    if engine.show_aspects: table.add_column("KP Aspect Hits (T->N)", style="bold magenta")
    last_dasha = None
    ASPECT_MAP = {0: "Conj", 180: "Opp", 120: "Trine", 90: "Sqr", 60: "Sxt"}
    for i in range(241):
        dt = engine.view_date + timedelta(minutes=i*2)
        d_str = "-".join(engine.get_dasha_at(dt))
        f_h, f_a = [], []
        t_jd = swe.julday(dt.year, dt.month, dt.day, dt.hour + dt.minute/60.0)
        for pid, nm in [(0,"Su"),(1,"Mo"),(2,"Me"),(3,"Ve"),(4,"Ma"),(5,"Ju"),(6,"Sa"),(11,"Ra")]:
            res, _ = swe.calc_ut(t_jd, pid, swe.FLG_SWIEPH | swe.FLG_SIDEREAL)
            t_lon = res[0]
            t_star = PLANET_LIT[int(t_lon * 60 / 800) % 9]
            t_house = int(t_lon / 30) + 1
            for natal_nm, n_lon in engine.n_pos.items():
                diff = abs(t_lon - n_lon) % 360
                if diff > 180: diff = 360 - diff
                for angle, label in ASPECT_MAP.items():
                    if abs(diff - angle) < 0.6:
                        f_h.append(f"T-{nm} H{t_house}({t_star})")
                        f_a.append(f"{label} N-{natal_nm}")
        if d_str != last_dasha or f_a:
            row = [dt.strftime("%H:%M")]
            if engine.show_dasha: row.append(d_str)
            if engine.show_houses: row.append(" | ".join(list(set(f_h))))
            if engine.show_aspects: row.append(" | ".join(list(set(f_a))))
            table.add_row(*row)
            last_dasha = d_str
    return table

def make_layout():
    status = "[bold red]PAUSED[/]" if engine.is_paused else "[bold green]LIVE[/]"
    layout = Layout()
    layout.split_column(
        Layout(Panel(f"KP V44 | {status} | VIEWING: {engine.view_date.strftime('%d-%m-%Y %H:%M')}\n"
                     f"[SPACE] Pause | [D/A/H] Toggles | [J] Jump | [Q] Quit", style="white on blue"), size=4),
        Layout(get_dashboard_table())
    )
    return layout

def on_press(key):
    global exit_flag
    try:
        if key == keyboard.Key.space: engine.is_paused = not engine.is_paused
        if not engine.is_paused:
            if key == keyboard.Key.right: engine.view_date += timedelta(minutes=15)
            elif key == keyboard.Key.left: engine.view_date -= timedelta(minutes=15)
        if hasattr(key, 'char'):
            c = key.char.lower()
            if c == 'q': exit_flag = True
            if c == 'j': engine.request_jump = True
            if c == 'd': engine.show_dasha = not engine.show_dasha
            if c == 'a': engine.show_aspects = not engine.show_aspects
            if c == 'h': engine.show_houses = not engine.show_houses
    except: pass

listener = keyboard.Listener(on_press=on_press); listener.start()
exit_flag = False
try:
    with Live(make_layout(), refresh_per_second=4, screen=True) as live:
        while not exit_flag:
            if engine.request_jump:
                live.stop()
                target = console.input("\nJump to Date (DD/MM/YYYY HH:MM): ")
                try: engine.view_date = datetime.strptime(target, "%d/%m/%Y %H:%M")
                except: pass
                engine.request_jump = False
                live.start()
            if not engine.is_paused: live.update(make_layout())
            time.sleep(0.1)
finally: listener.stop()