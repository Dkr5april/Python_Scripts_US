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
console = Console()
geolocator = Nominatim(user_agent="astro_engine_fixed")

ORB_LON = 1.5 
ORB_DEC = 1.2

RISE_FLAGS = swe.BIT_DISC_CENTER | swe.CALC_RISE
SET_FLAGS  = swe.BIT_DISC_CENTER | swe.CALC_SET

# ---------------- ENGINE ----------------
class AstroEngine:
    def __init__(self, name, d, m, y, h, lat, lon):
        self.name = name
        self.njd = float(swe.julday(y, m, d, h))
        swe.set_sid_mode(swe.SIDM_LAHIRI)

        self.mode = "SIDEREAL"
        self.view_date = datetime.now()
        self.b_lat, self.b_lon = float(lat), float(lon)

        self.n_sid = self.calc_planets(self.njd, True)
        self.n_trop = self.calc_planets(self.njd, False)

        self.n_up = self.get_upagrahas(d, m, y)

        sun_lon = self.n_sid["Su"]["lon"]
        dhuma = (sun_lon + 133.3333) % 360
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

        self.n_ant = {k: (180 - v["lon"]) % 360 for k, v in self.n_trop.items()}
        self.dagdha_signs = self.get_dagdha_rashis(self.njd)

    def get_dagdha_rashis(self, jd):
        res_s, _ = swe.calc_ut(jd, 0)
        res_m, _ = swe.calc_ut(jd, 1)
        tithi = int(((res_m[0] - res_s[0]) % 360) / 12) + 1
        mapping = {1:[7,10],2:[9,12],3:[11,2],4:[5,2],5:[4,7],6:[6,3],
                   7:[3,4],8:[6,9],9:[5,11],10:[5,11],11:[9,12],12:[10,1],
                   13:[11,2],14:[3,4,6,9],15:[],30:[]}
        return mapping.get(tithi if tithi <= 15 else tithi-15, [])

    def get_upagrahas(self, d, m, y):
        mjd = float(swe.julday(y, m, d, 0.0))
        geopos = (self.b_lon, self.b_lat, 0)

        try:
            r_res = swe.rise_trans(mjd, swe.SUN, geopos, RISE_FLAGS)
            s_res = swe.rise_trans(mjd, swe.SUN, geopos, SET_FLAGS)

            r = r_res[1][0]
            s = s_res[1][0]
        except:
            return {}

        is_day = r <= self.njd <= s
        duration = (s - r) if is_day else (1.0 - (s - r))
        part = duration / 8.0

        start_l = int(swe.day_of_week(self.njd))
        if not is_day:
            start_l = (start_l + 4) % 7

        lords = ["Kala","Gauri","Artha","Khanda","Mrityu","Yama","Gulika","M-Kala"]

        up_pos = {}
        base = r if is_day else s

        for i in range(8):
            seg_time = base + (i * part)
            try:
                _, ascmc = swe.houses_ex(seg_time, self.b_lat, self.b_lon, b'P')
                up_pos[lords[(start_l + i) % 8]] = ascmc[0]
            except:
                continue

        return up_pos

    def calc_planets(self, jd, sidereal):
        flags = swe.FLG_SWIEPH | swe.FLG_SPEED
        if sidereal:
            flags |= swe.FLG_SIDEREAL

        data = {}
        plist = [(0,"Su"), (1,"Mo"), (2,"Me"), (3,"Ve"), (4,"Ma"),
                 (5,"Ju"), (6,"Sa"), (11,"Ra"), (7,"Ur"), (8,"Ne"), (9,"Pl")]

        for pid, pnm in plist:
            res, _ = swe.calc_ut(jd, pid, flags)
            data[pnm] = {
                "lon": res[0] % 360,
                "dec": res[1],
                "retro": res[3] < 0
            }
            if pnm == "Ra":
                data["Ke"] = {
                    "lon": (res[0] + 180) % 360,
                    "dec": -res[1],
                    "retro": True
                }

        return data

# ---------------- HELPERS ----------------
def get_house(lon):
    return int(lon // 30) % 12 + 1   # ✅ FIXED (never 13)

# ---------------- UI ----------------
def get_chart(engine):
    tjd = swe.julday(engine.view_date.year, engine.view_date.month, engine.view_date.day, 12.0)

    transit = engine.calc_planets(tjd, engine.mode == "SIDEREAL")
    natal = engine.n_sid if engine.mode == "SIDEREAL" else engine.n_trop

    grid = {i:{"n":[], "t":[]} for i in range(1,13)}

    for p,v in natal.items():
        grid[get_house(v["lon"])]["n"].append(f"({p})" if v["retro"] else p)

    for p,v in transit.items():
        grid[get_house(v["lon"])]["t"].append(f"({p})" if v["retro"] else p)

    t = Table.grid(expand=True)
    for _ in range(4):
        t.add_column()

    def cell(n):
        b = "🔥" if n in engine.dagdha_signs else ""
        return Panel(
            f"[green]{' '.join(grid[n]['n'])}[/]\n[red]{' '.join(grid[n]['t'])}[/]",
            title=f"H{n}{b}"
        )

    t.add_row(cell(12), cell(1), cell(2), cell(3))
    t.add_row(cell(11), Align.center(engine.mode), Align.center(f"{engine.view_date:%d-%b}"), cell(4))
    t.add_row(cell(10), "", "", cell(5))
    t.add_row(cell(9), cell(8), cell(7), cell(6))

    return t

def get_impact_table(engine):
    table = Table(expand=True, box=None)
    table.add_column("Transit", style="red", width=8)
    table.add_column("Natal/Point", style="green")
    table.add_column("Result")

    tjd = swe.julday(engine.view_date.year, engine.view_date.month, engine.view_date.day, 12.0)
    t_sid = engine.calc_planets(tjd, True)
    t_trop = engine.calc_planets(tjd, False)

    for tp, t in t_sid.items():
        for name, lon in {**engine.n_up, **engine.n_apra}.items():
            if abs(t["lon"] - lon) < ORB_LON:
                res = "[yellow]REDUCED[/]" if tp in ["Ju","Ve"] else "[red]NEGATIVE[/]"
                table.add_row(tp, name, res)

    for tp, t in t_trop.items():
        for np, lon in engine.n_ant.items():
            if abs(t["lon"] - lon) < ORB_LON:
                table.add_row(tp, f"Ant.{np}", "[cyan]POSITIVE[/]")

        for np, nd in engine.n_trop.items():
            if abs(t["dec"] - nd["dec"]) < ORB_DEC:
                table.add_row(tp, f"|| {np}", "[white]PARALLEL[/]")
            if abs(t["dec"] + nd["dec"]) < ORB_DEC:
                table.add_row(tp, f"Contra-{np}", "[white]C-PARA[/]")

    return table

def make_layout(engine):
    layout = Layout()

    layout.split_column(
        Layout(
            Panel(
                f"USER: {engine.name} | [T] Toggle | [←/→] Day | [Q] Quit",
                style="white on blue"
            ),
            size=3
        ),
        Layout(name="body")
    )

    layout["body"].split_row(
        Layout(Panel(get_chart(engine), title="Chart View"), ratio=2),
        Layout(Panel(get_impact_table(engine), title="Impacts"), ratio=1)
    )

    return layout

# ---------------- RUN ----------------
console.clear()

name_in = input("Enter Name: ")
dob_in = input("Enter DOB (DD/MM/YYYY): ")
tob_in = input("Enter TOB (HH:MM:SS): ")
city_in = input("Enter Birth City: ")

d, m, y = map(int, dob_in.split("/"))
hh, mm, ss = map(int, tob_in.split(":"))
birth_h = hh + mm/60 + ss/3600

lat, lon = 16.1176, 80.9314

try:
    loc = geolocator.geocode(city_in, timeout=10)
    if loc:
        lat, lon = loc.latitude, loc.longitude
except:
    pass

engine = AstroEngine(name_in, d, m, y, birth_h, lat, lon)

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
                engine.mode = "TROPICAL" if engine.mode == "SIDEREAL" else "SIDEREAL"
            if key.char == 'q':
                exit_flag = True
    except:
        pass

listener = keyboard.Listener(on_press=on_press)
listener.start()

sys.stdout.write("\033[?1049h")

try:
    with Live(make_layout(engine), refresh_per_second=4, screen=True) as live:
        while not exit_flag:
            live.update(make_layout(engine))
            time.sleep(0.1)
finally:
    sys.stdout.write("\033[?1049l")
    listener.stop()