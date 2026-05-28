# ================== ULTIMATE HYBRID ASTRO ENGINE ==================

import swisseph as swe
import os, sys, time
from datetime import datetime, timedelta
from pynput import keyboard
import msvcrt
from geopy.geocoders import Nominatim
from rich.live import Live
from rich.table import Table
from rich.console import Console
from rich.layout import Layout
from rich.panel import Panel
from rich.align import Align

# ---------------- CONFIG ----------------
if sys.platform == "win32":
    os.system("color")

swe.set_ephe_path("./ephe")
console = Console(force_terminal=True)
geolocator = Nominatim(user_agent="astro_ultimate_engine")

ORB_LON = 3.0
ORB_DEC = 1.5

# ---------------- HELPERS ----------------
def ang_diff(a, b):
    return min(abs(a - b), 360 - abs(a - b))

def get_house(lon):
    return int(lon // 30) + 1

def midpoint(a, b):
    d = (b - a) % 360
    return (a + d / 2) % 360

# 🎯 EVENT SCORING
def update_score(scores, key, value):
    scores[key] += value

def get_scores():
    return {"Career":0,"Relationship":0,"Health":0,"Finance":0}

# ---------------- ENGINE ----------------
class AstroEngine:
    def __init__(self, name, d, m, y, h, lat, lon):
        self.name = name
        self.njd = float(swe.julday(y, m, d, h))
        swe.set_sid_mode(swe.SIDM_LAHIRI)

        self.mode = "SIDEREAL"
        self.view_date = datetime.now()

        self.lat, self.lon = float(lat), float(lon)

        self.n_sid = self.calc_planets(self.njd, True)
        self.n_trop = self.calc_planets(self.njd, False)

        self.n_up = self.get_upagrahas(d, m, y)
        self.n_apra = self.get_shadow_planets()

    def calc_planets(self, jd, sidereal):
        flags = int(swe.FLG_SWIEPH | swe.FLG_SPEED)
        if sidereal:
            flags |= int(swe.FLG_SIDEREAL)

        plist = [(0,"Su"),(1,"Mo"),(2,"Me"),(3,"Ve"),
                 (4,"Ma"),(5,"Ju"),(6,"Sa"),
                 (11,"Ra"),(7,"Ur"),(8,"Ne"),(9,"Pl")]

        data = {}
        for pid, name in plist:
            r, _ = swe.calc_ut(float(jd), int(pid), flags)
            data[name] = {"lon": r[0] % 360,"dec": r[1],"retro": r[3] < 0}

            if name == "Ra":
                data["Ke"] = {"lon": (r[0] + 180) % 360,"dec": -r[1],"retro": True}

        return data

    def get_upagrahas(self, d, m, y):
        try:
            mjd = float(swe.julday(y, m, d, 0.0))
            # REPAIR: Fixed search flags to prevent TypeError
            r_res = swe.rise_trans(mjd, 0, float(self.lon), float(self.lat), 0.0, int(1024 | 1))
            s_res = swe.rise_trans(mjd, 0, float(self.lon), float(self.lat), 0.0, int(1024 | 2))

            r, s = r_res[1][0], s_res[1][0]
            is_day = (self.njd >= r and self.njd <= s)
            dur = (s - r) if is_day else (1.0 - (s - r))
            part = dur / 8.0

            lords = ["Kala","Gauri","Artha","Khanda","Mrityu","Yama","Gulika","M-Kala"]
            base = r if is_day else s
            up = {}

            for i in range(8):
                seg = base + (i * part)
                _, ascmc = swe.houses_ex(seg, self.lat, self.lon, b'P')
                up[lords[i]] = ascmc[0]

            return up
        except:
            return {}

    def get_shadow_planets(self):
        sun = self.n_sid["Su"]["lon"]
        dhuma = (sun + 133.3333) % 360
        vyatipata = (360 - dhuma) % 360
        parivesha = (vyatipata + 180) % 360
        indra = (parivesha + 16.6666) % 360
        upaketu = (indra + 16.6666) % 360

        return {"Dhuma": dhuma,"Vyatipata": vyatipata,
                "Parivesha": parivesha,"IndraChapa": indra,"Upaketu": upaketu}

# ---------------- IMPACT ----------------
def impact_table(engine):
    scores = get_scores()

    table = Table(expand=True)
    table.add_column("Type")
    table.add_column("Detail")
    table.add_column("Effect")

    jd = float(swe.julday(engine.view_date.year, engine.view_date.month, engine.view_date.day, 12.0))
    t_sid = engine.calc_planets(jd, True)
    t_trop = engine.calc_planets(jd, False)

    if engine.mode == "SIDEREAL":
        for tp, t in t_sid.items():
            for name, lon in {**engine.n_up, **engine.n_apra}.items():
                if ang_diff(t["lon"], lon) < ORB_LON:
                    effect = "[red]BAD[/]" if name in ["Dhuma","Vyatipata","Mrityu"] else "[green]GOOD[/]"
                    table.add_row("Vedic", f"{tp}->{name}", effect)

    if engine.mode == "TROPICAL":
        ASPECTS = {0:"Conj",60:"Sextile",90:"Square",120:"Trine",180:"Opp",150:"Quincunx"}

        for a,pa in t_trop.items():
            for b,pb in t_trop.items():
                if a>=b: continue
                d=ang_diff(pa["lon"],pb["lon"])
                for deg,name in ASPECTS.items():
                    if abs(d-deg) < ORB_LON:
                        table.add_row("Aspect",f"{a}-{b} {name}","[cyan]Active[/]")

                        if name in ["Trine","Sextile"]:
                            update_score(scores,"Career",2)
                            update_score(scores,"Finance",2)
                        if name in ["Square","Opp"]:
                            update_score(scores,"Health",-2)

        sm_mid = midpoint(t_trop["Su"]["lon"], t_trop["Mo"]["lon"])
        for tp, t in t_trop.items():
            if ang_diff(t["lon"], sm_mid) < ORB_LON:
                table.add_row("Midpoint", f"{tp}↔Sun/Moon","[yellow]Trigger[/]")
                update_score(scores,"Relationship",2)

    return table, scores

# ---------------- SCORE PANEL ----------------
def score_panel(scores):
    t = Table(title="Event Scores")
    t.add_column("Area")
    t.add_column("Score")

    for k,v in scores.items():
        color = "green" if v>0 else "red" if v<0 else "white"
        t.add_row(k, f"[{color}]{v}[/]")

    return Panel(t)

# ---------------- CHART ----------------
def get_chart(engine):
    jd = float(swe.julday(engine.view_date.year, engine.view_date.month, engine.view_date.day, 12.0))
    transit = engine.calc_planets(jd, engine.mode == "SIDEREAL")
    natal = engine.n_sid if engine.mode == "SIDEREAL" else engine.n_trop

    grid = {i: {"n": [], "t": []} for i in range(1, 13)}

    for p, v in natal.items():
        grid[get_house(v["lon"])]["n"].append(p)

    for p, v in transit.items():
        grid[get_house(v["lon"])]["t"].append(p)

    t = Table.grid(expand=True)
    for _ in range(4): t.add_column()

    def cell(n):
        return Panel(f"[green]{' '.join(grid[n]['n'])}[/]\n[red]{' '.join(grid[n]['t'])}[/]", title=f"H{n}")

    t.add_row(cell(12), cell(1), cell(2), cell(3))
    t.add_row(cell(11), Align.center(engine.mode), Align.center(f"{engine.view_date:%d-%b}"), cell(4))
    t.add_row(cell(10), "", "", cell(5))
    t.add_row(cell(9), cell(8), cell(7), cell(6))

    return t

# ---------------- LAYOUT ----------------
def make_layout(engine):
    layout = Layout()
    layout.split_column(Layout(Panel(f"{engine.name} | Mode: {engine.mode} | ← → Navigate | T Toggle | Q Quit"), size=3),
                        Layout(name="body"))

    table, scores = impact_table(engine)

    right = Layout()
    right.split_column(Layout(Panel(table, title="Impacts"), ratio=2), Layout(score_panel(scores), ratio=1))

    layout["body"].split_row(Layout(Panel(get_chart(engine), title="Transit Chart"), ratio=2), right)
    return layout

# ---------------- RUN ----------------
console.clear()

name = input("Name: ")
dob = input("DOB dd/mm/yyyy: ")
tob = input("TOB hh:mm:ss: ")
city = input("City: ")

d, m, y = map(int, dob.split("/"))
hh, mm, ss = map(int, tob.split(":"))
h = hh + mm/60 + ss/3600

# Default Lat/Lon
lat, lon = 16.1176, 80.9314

try:
    loc = geolocator.geocode(city)
    if loc:
        lat, lon = loc.latitude, loc.longitude
except:
    pass

engine = AstroEngine(name, d, m, y, h, lat, lon)

exit_flag = False

def on_press(key):
    global exit_flag
    try:
        if hasattr(key, "char") and key.char:
            if key.char.lower() == "q":
                exit_flag = True
    except:
        pass

listener = keyboard.Listener(on_press=on_press)
listener.start()

try:
    with Live(make_layout(engine), console=console, refresh_per_second=4, screen=True):
        while not exit_flag:
            if msvcrt.kbhit():
                key = msvcrt.getch()

                # Handle arrow keys (Special prefix \xe0 or \x00)
                if key in [b'\xe0', b'\x00']:
                    key2 = msvcrt.getch()
                    if key2 == b'M': # Right Arrow
                        engine.view_date += timedelta(days=1)
                    elif key2 == b'K': # Left Arrow
                        engine.view_date -= timedelta(days=1)
                else:
                    try:
                        ch = key.decode().lower()
                        if ch == 't':
                            engine.mode = "TROPICAL" if engine.mode == "SIDEREAL" else "SIDEREAL"
                        elif ch == 'q':
                            exit_flag = True
                    except:
                        pass

            time.sleep(0.05)

finally:
    listener.stop()
    sys.stdout.write("\nExiting Engine...\n")