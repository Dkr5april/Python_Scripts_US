import swisseph as swe
import os, sys, time
from datetime import datetime, timedelta
from pynput import keyboard
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
geolocator = Nominatim(user_agent="astro_engine_final")

ORB_LON = 3.0
ORB_DEC = 2.0

# ---------------- HELPERS ----------------
def ang_diff(a, b):
    return min(abs(a - b), 360 - abs(a - b))

def get_house(lon):
    return int(lon // 30) % 12 + 1

# ---------------- ENGINE ----------------
class AstroEngine:
    def __init__(self, name, d, m, y, h, lat, lon):
        self.name = name
        self.njd = swe.julday(y, m, d, h)
        swe.set_sid_mode(swe.SIDM_LAHIRI)

        self.mode = "SIDEREAL"
        self.view_date = datetime.now()
        self.b_lat, self.b_lon = lat, lon

        self.n_sid = self.calc_planets(self.njd, True)
        self.n_trop = self.calc_planets(self.njd, False)

        # ---------------- UPAGRAHAS ----------------
        self.n_up = self.get_upagrahas(d, m, y)

        # fallback if calculation fails
        if not self.n_up:
            base = self.n_sid["Su"]["lon"]
            self.n_up = {
                "Kala": (base + 30) % 360,
                "Gulika": (base + 90) % 360,
                "Yama": (base + 150) % 360
            }

        # ---------------- SHADOW PLANETS ----------------
        sun = self.n_sid["Su"]["lon"]
        dhuma = (sun + 133.3333) % 360
        vyatipata = (360 - dhuma) % 360
        parivesha = (vyatipata + 180) % 360
        indra = (parivesha + 16.6666) % 360
        upaketu = (indra + 16.6666) % 360

        self.n_apra = {
            "Dhuma": dhuma,
            "Vyatipata": vyatipata,
            "Parivesha": parivesha,
            "IndraChapa": indra,
            "Upaketu": upaketu
        }

        # ---------------- ANTISCION ----------------
        self.n_ant = {k: (180 - v["lon"]) % 360 for k, v in self.n_trop.items()}

    def get_upagrahas(self, d, m, y):
        try:
            jd = swe.julday(y, m, d, 0.0)
            geopos = (self.b_lon, self.b_lat, 0)

            r = swe.rise_trans(jd, swe.SUN, geopos, swe.CALC_RISE)[1][0]
            s = swe.rise_trans(jd, swe.SUN, geopos, swe.CALC_SET)[1][0]

            is_day = r <= self.njd <= s
            duration = (s - r) if is_day else (1 - (s - r))
            part = duration / 8

            lords = ["Kala","Gauri","Artha","Khanda","Mrityu","Yama","Gulika","M-Kala"]

            up = {}
            base = r if is_day else s

            for i in range(8):
                seg = base + (i * part)
                _, ascmc = swe.houses_ex(seg, self.b_lat, self.b_lon, b'P')
                up[lords[i]] = ascmc[0]

            return up
        except:
            return {}

    def calc_planets(self, jd, sidereal):
        flags = swe.FLG_SWIEPH | swe.FLG_SPEED
        if sidereal:
            flags |= swe.FLG_SIDEREAL

        data = {}
        plist = [
            (0,"Su"), (1,"Mo"), (2,"Me"), (3,"Ve"),
            (4,"Ma"), (5,"Ju"), (6,"Sa"),
            (11,"Ra"), (7,"Ur"), (8,"Ne"), (9,"Pl")
        ]

        for pid, name in plist:
            res, _ = swe.calc_ut(jd, pid, flags)
            data[name] = {
                "lon": res[0] % 360,
                "dec": res[1],
                "retro": res[3] < 0
            }
            if name == "Ra":
                data["Ke"] = {
                    "lon": (res[0] + 180) % 360,
                    "dec": -res[1],
                    "retro": True
                }

        return data

# ---------------- UI ----------------
def get_chart(engine):
    tjd = swe.julday(engine.view_date.year, engine.view_date.month, engine.view_date.day, 12.0)

    transit = engine.calc_planets(tjd, engine.mode == "SIDEREAL")
    natal = engine.n_sid if engine.mode == "SIDEREAL" else engine.n_trop

    grid = {i:{"n":[], "t":[]} for i in range(1,13)}

    for p,v in natal.items():
        grid[get_house(v["lon"])]["n"].append(p)

    for p,v in transit.items():
        grid[get_house(v["lon"])]["t"].append(p)

    t = Table.grid(expand=True)
    for _ in range(4):
        t.add_column()

    def cell(n):
        return Panel(
            f"[green]{' '.join(grid[n]['n'])}[/]\n[red]{' '.join(grid[n]['t'])}[/]",
            title=f"H{n}"
        )

    t.add_row(cell(12), cell(1), cell(2), cell(3))
    t.add_row(cell(11), Align.center(engine.mode), Align.center(f"{engine.view_date:%d-%b}"), cell(4))
    t.add_row(cell(10), "", "", cell(5))
    t.add_row(cell(9), cell(8), cell(7), cell(6))

    return t

def get_extra_table(engine):
    table = Table(title="Upagrahas & Shadow Planets", expand=True)
    table.add_column("Type")
    table.add_column("Name")
    table.add_column("Longitude")

    for k,v in engine.n_up.items():
        table.add_row("Upagraha", k, f"{v:.2f}")

    for k,v in engine.n_apra.items():
        table.add_row("Shadow", k, f"{v:.2f}")

    return table

def get_impact_table(engine):
    table = Table(title="Impacts", expand=True)
    table.add_column("Transit")
    table.add_column("Point")
    table.add_column("Effect")

    tjd = swe.julday(engine.view_date.year, engine.view_date.month, engine.view_date.day, 12.0)

    t_sid = engine.calc_planets(tjd, True)
    t_trop = engine.calc_planets(tjd, False)

    for tp, t in t_sid.items():
        for name, lon in {**engine.n_up, **engine.n_apra}.items():
            if ang_diff(t["lon"], lon) < ORB_LON:
                table.add_row(tp, name, "HIT")

    for tp, t in t_trop.items():
        for name, lon in engine.n_ant.items():
            if ang_diff(t["lon"], lon) < ORB_LON:
                table.add_row(tp, f"Ant.{name}", "POSITIVE")

        for name, nd in engine.n_trop.items():
            if abs(t["dec"] - nd["dec"]) < ORB_DEC:
                table.add_row(tp, f"|| {name}", "PARALLEL")

    return table

def make_layout(engine):
    layout = Layout()

    # Header
    layout.split_column(
        Layout(
            Panel(f"{engine.name} | [T] Toggle | ←/→ Move | Q Quit"),
            size=3
        ),
        Layout(name="body")
    )

    # LEFT + RIGHT split
    layout["body"].split_row(
        Layout(name="left", ratio=2),
        Layout(name="right", ratio=1)
    )

    # LEFT panel (chart)
    layout["left"].update(
        Panel(get_chart(engine), title="Chart")
    )

    # RIGHT split (vertical)
    layout["right"].split_column(
        Layout(Panel(get_impact_table(engine), title="Impacts")),
        Layout(Panel(get_extra_table(engine), title="Upagrahas & Shadows"))
    )

    return layout

# ---------------- RUN ----------------
console.clear()

name = input("Enter Name: ")
dob = input("Enter DOB (DD/MM/YYYY): ")
tob = input("Enter TOB (HH:MM:SS): ")
city = input("Enter Birth City: ")

d,m,y = map(int, dob.split("/"))
hh,mm,ss = map(int, tob.split(":"))
h = hh + mm/60 + ss/3600

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
        if key == keyboard.Key.right:
            engine.view_date += timedelta(days=1)
        elif key == keyboard.Key.left:
            engine.view_date -= timedelta(days=1)
        elif hasattr(key, 'char'):
            if key.char == 't':
                engine.mode = "TROPICAL" if engine.mode=="SIDEREAL" else "SIDEREAL"
            if key.char == 'q':
                exit_flag = True
    except:
        pass

listener = keyboard.Listener(on_press=on_press)
listener.start()

sys.stdout.write("\033[?1049h")

try:
    with Live(make_layout(engine), console=console, refresh_per_second=4, screen=True):
        while not exit_flag:
            time.sleep(0.1)
finally:
    sys.stdout.write("\033[?1049l")
    listener.stop()