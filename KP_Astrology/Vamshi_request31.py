import swisseph as swe
import time
import os
import pandas as pd
from datetime import datetime, timedelta
from pynput import keyboard

from rich.live import Live
from rich.table import Table
from rich.console import Console
from rich.panel import Panel
from rich.layout import Layout
from rich.text import Text
from rich.progress import track

console = Console()
live = None

# ==================== SWISS EPHE SETUP ====================
swe.set_ephe_path("./ephe")
swe.set_sid_mode(swe.SIDM_KRISHNAMURTI)

# ==================== CONSTANTS =======================
YEAR_LEN = 365.2425
EPS = 1e-7

PLANET_LIT = ["Ke","Ve","Su","Mo","Ma","Ra","Ju","Sa","Me"]
DASHA_YEARS = [7, 20, 6, 10, 7, 18, 16, 19, 17]
TOTAL_YEARS = sum(DASHA_YEARS)

RASHI_NAMES = ["Ar","Ta","Ge","Cn","Le","Vi","Li","Sc","Sg","Cp","Aq","Pi"]
RASHI_OWNERS = {
    0:"Ma",1:"Ve",2:"Me",3:"Mo",4:"Su",5:"Me",
    6:"Ve",7:"Ma",8:"Ju",9:"Sa",10:"Sa",11:"Ju"
}

POS_HOUSES = {1,2,3,6,10,11}
NEG_HOUSES = {8,12}
NAK_LEN = 360 / 27

# ==================== EXCEL LOGGER ====================
class DashaLogger:
    def __init__(self, filename="dasha_changes.xlsx"):
        self.filename = filename
        self.last_dasha_str = ""

    def log_change(self, current_dt, dasha_list, engine):
        dasha_str = "-".join(dasha_list)
        if dasha_str != self.last_dasha_str:
            data = {
                "Timestamp": [current_dt.strftime("%Y-%m-%d %H:%M:%S")],
                "Dasha Sequence": [dasha_str]
            }
            lvls=["MAHA","BHUKTI","ANTARA","SOOK","PRANA","DEHA"]
            for i, p in enumerate(dasha_list):
                s, sl, st, sub, ss, sss, substar, net, dbg = engine.analyze(p)
                data[f"{lvls[i]}_Planet"] = [p]
                data[f"{lvls[i]}_Net"] = [net]
            
            df = pd.DataFrame(data)
            if not os.path.isfile(self.filename):
                df.to_excel(self.filename, index=False)
            else:
                with pd.ExcelWriter(self.filename, mode='a', engine='openpyxl', if_sheet_exists='overlay') as writer:
                    try:
                        existing_df = pd.read_excel(self.filename)
                        updated_df = pd.concat([existing_df, df], ignore_index=True)
                        updated_df.to_excel(writer, index=False)
                    except:
                        df.to_excel(writer, index=False)
            self.last_dasha_str = dasha_str

logger = DashaLogger()

# ==================== STARTUP INPUTS ==================
def startup_inputs():
    console.print("\n[bold cyan]KP MASTER ENGINE – STARTUP[/]\n")
    
    dbg = input("Enable DEBUG mode? (y/n) [y]: ").strip().lower()
    debug_mode = False if dbg == "n" else True

    use_default = input("Use default birth data? (y/n) [y]: ").strip().lower()
    if use_default != "n":
        dob, tob, lat, lon = "05/04/1979", "16:55:00", 16.12, 80.93
    else:
        dob = input("DOB (DD/MM/YYYY): ").strip()
        tob = input("TOB (HH:MM:SS): ").strip()
        lat = float(input("Latitude: "))
        lon = float(input("Longitude: "))

    # New Scanning Option
    do_scan = input("\nRun an automated Excel scan for a period? (y/n) [n]: ").strip().lower()
    scan_data = None
    if do_scan == "y":
        s_date = input("Start Date (YYYY-MM-DD): ").strip()
        e_date = input("End Date (YYYY-MM-DD): ").strip()
        step = int(input("Step in Minutes (e.g. 60): ") or "60")
        scan_data = (datetime.strptime(s_date, "%Y-%m-%d"), 
                     datetime.strptime(e_date, "%Y-%m-%d"), step)

    t_in = input("\nTransit datetime for UI (YYYY-MM-DD HH:MM) or Enter for NOW: ").strip()
    view_date = datetime.strptime(t_in,"%Y-%m-%d %H:%M") if t_in else datetime.now()

    return debug_mode, dob, tob, lat, lon, view_date, scan_data

# ... [KPEngineV89 Class remains exactly same as your original] ...
class KPEngineV89:
    def __init__(self, dob, tob, lat, lon):
        self.lat, self.lon = lat, lon
        d,m,y = map(int, dob.split("/"))
        hh,mm,ss = map(int, tob.split(":"))
        self.njd = swe.julday(y,m,d,hh+mm/60+ss/3600 - 5.5)
        flag = swe.FLG_SWIEPH | swe.FLG_SIDEREAL
        self.birth_moon = swe.calc_ut(self.njd, swe.MOON, flag)[0][0]
        self.view_date = datetime.now()
        self.refresh()

    def kp_lords(self, lon, depth=4):
        nak_idx = int(lon // NAK_LEN)
        pos = lon - nak_idx * NAK_LEN
        star_idx = nak_idx % 9
        star = PLANET_LIT[star_idx]
        result = [star]
        debug = [f"Nak={nak_idx} Pos={pos:.6f}"]
        base_len = NAK_LEN
        cur_idx = star_idx
        for lvl in range(1, depth):
            acc = 0
            for i in range(9):
                idx = (cur_idx + i) % 9
                part = (DASHA_YEARS[idx] / TOTAL_YEARS) * base_len
                if acc + part >= pos:
                    result.append(PLANET_LIT[idx])
                    debug.append(f"L{lvl}:{PLANET_LIT[idx]} Seg={part:.6f}")
                    pos -= acc
                    base_len = part
                    cur_idx = idx
                    break
                acc += part
        return result, debug

    def refresh(self):
        flag = swe.FLG_SWIEPH | swe.FLG_SIDEREAL
        t_jd = swe.julday(self.view_date.year,self.view_date.month,self.view_date.day,
                          self.view_date.hour + self.view_date.minute/60 - 5.5)
        self.n_pos, self.t_pos = {}, {}
        for pid,nm in [(0,"Su"),(1,"Mo"),(2,"Me"),(3,"Ve"),(4,"Ma"),(5,"Ju"),(6,"Sa"),(11,"Ra")]:
            self.n_pos[nm] = swe.calc_ut(self.njd,pid,flag)[0][0]
            self.t_pos[nm] = swe.calc_ut(t_jd,pid,flag)[0][0]
        self.n_pos["Ke"] = (self.n_pos["Ra"] + 180) % 360
        self.t_pos["Ke"] = (self.t_pos["Ra"] + 180) % 360
        self.cusps = swe.houses_ex(self.njd,self.lat,self.lon,b'P',flag)[0]
        self.p_to_h = {p:self.get_h(lon) for p,lon in self.n_pos.items()}
        self.own_map = {p:[] for p in PLANET_LIT}
        for i in range(12):
            owner = RASHI_OWNERS[int(self.cusps[i]//30)]
            self.own_map[owner].append(i+1)

    def get_h(self, lon):
        for i in range(12):
            s,e = self.cusps[i], self.cusps[(i+1)%12]
            if (s<e and s<=lon<e) or (s>e and (lon>=s or lon<e)): return i+1
        return 1

    def analyze(self, p):
        n_lon, t_lon = self.n_pos[p], self.t_pos[p]
        sign_idx = int(n_lon//30)
        sign, sign_lord = RASHI_NAMES[sign_idx], RASHI_OWNERS[sign_idx]
        chain, kp_dbg = self.kp_lords(n_lon,4)
        star, sub, ss, sss = chain
        sub_star = PLANET_LIT[int(self.n_pos[sub]//NAK_LEN)%9]
        hits = ([self.p_to_h[p],self.p_to_h[star],self.p_to_h[sign_lord]] + self.own_map[star] + self.own_map[sign_lord] + [self.get_h(t_lon)])
        pos, neg = [h for h in hits if h in POS_HOUSES], [h for h in hits if h in NEG_HOUSES]
        net, dbg = len(pos)-len(neg), [f"Sign={sign}({sign_lord})",f"P={pos}",f"N={neg}",*kp_dbg]
        return sign,sign_lord,star,sub,ss,sss,sub_star,net,dbg

    def dasha6(self, dt):
        nak = int(self.birth_moon//NAK_LEN)
        idx = nak%9
        bal = ((NAK_LEN-(self.birth_moon%NAK_LEN))/NAK_LEN)*DASHA_YEARS[idx]
        start = self.njd - (DASHA_YEARS[idx]-bal)*YEAR_LEN
        t_jd = swe.julday(dt.year,dt.month,dt.day, dt.hour+dt.minute/60 - 5.5)
        def walk(s,yrs,i,l):
            if l==6: return []
            cur=s
            for k in range(9):
                j=(i+k)%9
                dur=(DASHA_YEARS[j]/120)*yrs*YEAR_LEN
                if cur<=t_jd<cur+dur: return [PLANET_LIT[j]] + walk(cur,dur/YEAR_LEN,j,l+1)
                cur+=dur
            return ["?"]
        return walk(start,120,idx,0)

# UI functions same as original
def controls_panel():
    t = Text()
    t.append("PgUp / PgDn : ±10 Days | Home / End : ±1 Month | ↑ / ↓ : ±1 Hour\n")
    t.append("[ / ] : ±5 Min | < / > : ±30 Min | g : Go to Date | q : Quit\n")
    return Panel(t, title="KEY CONTROLS", border_style="bright_yellow")

def goto_datetime():
    console.clear()
    s = input("YYYY-MM-DD HH:MM (blank = cancel): ").strip()
    try: return datetime.strptime(s,"%Y-%m-%d %H:%M") if s else None
    except: return None

# ==================== EXECUTION LOGIC =============================
DEBUG_MODE, DOB, TOB, LAT, LON, VIEW_DATE, SCAN_DATA = startup_inputs()
engine = KPEngineV89(DOB, TOB, LAT, LON)

# Run Background Scan if requested
if SCAN_DATA:
    start_dt, end_dt, step_min = SCAN_DATA
    current = start_dt
    total_steps = int((end_dt - start_dt).total_seconds() / (60 * step_min))
    console.print(f"\n[bold green]Scanning from {start_dt.date()} to {end_dt.date()}...[/]")
    for _ in track(range(total_steps), description="Processing Dasha Changes..."):
        engine.view_date = current
        engine.refresh()
        logger.log_change(current, engine.dasha6(current), engine)
        current += timedelta(minutes=step_min)
    console.print("[bold green]Scan Complete. Results saved to Excel.[/]\n")
    time.sleep(1)

# Transition to Interactive Mode
engine.view_date = VIEW_DATE
engine.refresh()
exit_f = False

def on_p(key):
    global exit_f, live
    try:
        if key == keyboard.Key.page_up: engine.view_date += timedelta(days=10)
        elif key == keyboard.Key.page_down: engine.view_date -= timedelta(days=10)
        elif key == keyboard.Key.home: engine.view_date += timedelta(days=30)
        elif key == keyboard.Key.end: engine.view_date -= timedelta(days=30)
        elif key == keyboard.Key.up: engine.view_date += timedelta(hours=1)
        elif key == keyboard.Key.down: engine.view_date -= timedelta(hours=1)
        elif hasattr(key,"char"):
            if key.char == "]": engine.view_date += timedelta(minutes=5)
            elif key.char == "[": engine.view_date -= timedelta(minutes=5)
            elif key.char == ">": engine.view_date += timedelta(minutes=30)
            elif key.char == "<": engine.view_date -= timedelta(minutes=30)
            elif key.char.lower() == "g":
                live.stop(); dt = goto_datetime(); 
                if dt: engine.view_date = dt
                live.start()
            elif key.char.lower() == "q": exit_f = True; return False
        
        engine.refresh()
        # Log manual changes during interactive mode too
        logger.log_change(engine.view_date, engine.dasha6(engine.view_date), engine)
        live.update(draw())
    except: pass

def draw():
    layout = Layout()
    layout.split_column(Layout(name="main", ratio=4), Layout(name="controls", size=6))
    table = Table(title=f"KP MASTER ENGINE | {engine.view_date}", expand=True)
    table.add_column("Lvl"); table.add_column("Planet"); table.add_column("Sign/Star/Sub/SS/SSS"); 
    if DEBUG_MODE: table.add_column("DEBUG")
    table.add_column("Net")
    
    lvls=["MAHA","BHUKTI","ANTARA","SOOK","PRANA","DEHA"]
    for i,p in enumerate(engine.dasha6(engine.view_date)):
        s,sl,st,sub,ss,sss,substar,net,dbg = engine.analyze(p)
        row=[lvls[i],p,f"{s}({sl})/{st}/{sub}/{ss}/{sss}"]
        if DEBUG_MODE: row.append(" | ".join(dbg))
        row.append(str(net))
        table.add_row(*row)
    layout["main"].update(table); layout["controls"].update(controls_panel())
    return layout

listener = keyboard.Listener(on_release=on_p)
listener.start()
with Live(draw(), refresh_per_second=10, screen=True) as live:
    while not exit_f: time.sleep(0.1)
listener.stop()