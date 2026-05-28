import swisseph as swe
import os, time, logging
from datetime import datetime, timedelta
from collections import Counter
from pynput import keyboard
from rich.live import Live
from rich.table import Table
from rich.console import Console

# ==================== LOGGER ==========================
logging.basicConfig(
    filename="KP_ENGINE_DEBUG.log",
    filemode="w",
    level=logging.DEBUG,
    format="%(asctime)s | %(levelname)s | %(message)s"
)

def log(msg):
    logging.debug(msg)

console = Console()

# ==================== CONSTANTS =======================
DEBUG_MODE = True
YEAR_LEN = 365.2425
EPS = 1e-7

swe.set_ephe_path("./ephe")
swe.set_sid_mode(swe.SIDM_KRISHNAMURTI)

PLANET_LIT = ["Ke","Ve","Su","Mo","Ma","Ra","Ju","Sa","Me"]
DASHA_YEARS = [7,20,6,10,7,18,16,19,17]

RASHI_OWNERS = {
    0:"Ma",1:"Ve",2:"Me",3:"Mo",4:"Su",5:"Me",
    6:"Ve",7:"Ma",8:"Ju",9:"Sa",10:"Sa",11:"Ju"
}

POS_HOUSES = {1,2,3,6,10,11}
NEG_HOUSES = {8,12}

ALL_ASPECTS = [
    (0,"Conj"),(180,"Oppo"),(120,"Trin"),(90,"Squa"),
    (60,"Sext"),(30,"SSxt"),(45,"SSqu"),
    (150,"Quin"),(72,"Qnt"),(135,"Sesq")
]

# ==================== ENGINE ==========================
class KPEngineV89_DEBUG:

    def __init__(self, dob, tob, lat, lon):
        log("========== ENGINE INIT ==========")
        self.lat, self.lon = lat, lon
        d, m, y = map(int, dob.split("/"))
        hh, mm, ss = map(int, tob.split(":"))

        self.njd = swe.julday(
            y, m, d,
            hh + mm/60 + ss/3600 - 5.5
        )
        log(f"BIRTH JD = {self.njd}")

        flag = swe.FLG_SWIEPH | swe.FLG_SIDEREAL
        self.birth_moon = swe.calc_ut(self.njd, swe.MOON, flag)[0][0]
        log(f"BIRTH MOON LONGITUDE = {self.birth_moon}")

        self.view_date = datetime.now()
        self.refresh()

    # ---------------------------------------------------
    def refresh(self):
        log("------ REFRESH START ------")
        flag = swe.FLG_SWIEPH | swe.FLG_SIDEREAL

        t_jd = swe.julday(
            self.view_date.year,
            self.view_date.month,
            self.view_date.day,
            self.view_date.hour + self.view_date.minute/60 - 5.5
        )
        log(f"TRANSIT JD = {t_jd}")

        self.n_pos, self.t_pos = {}, {}

        for pid, nm in [
            (0,"Su"),(1,"Mo"),(2,"Me"),(3,"Ve"),
            (4,"Ma"),(5,"Ju"),(6,"Sa"),(11,"Ra")
        ]:
            self.n_pos[nm] = swe.calc_ut(self.njd, pid, flag)[0][0]
            self.t_pos[nm] = swe.calc_ut(t_jd, pid, flag)[0][0]
            log(f"NATAL {nm} = {self.n_pos[nm]:.6f}")
            log(f"TRANSIT {nm} = {self.t_pos[nm]:.6f}")

        self.n_pos["Ke"] = (self.n_pos["Ra"] + 180) % 360
        self.t_pos["Ke"] = (self.t_pos["Ra"] + 180) % 360
        log(f"NATAL KE = {self.n_pos['Ke']:.6f}")
        log(f"TRANSIT KE = {self.t_pos['Ke']:.6f}")

        self.cusps = swe.houses_ex(
            self.njd, self.lat, self.lon, b'P', flag
        )[0]
        log(f"HOUSE CUSPS = {self.cusps}")

        self.p_to_h = {}
        for p, lon in self.n_pos.items():
            h = self.get_h(lon)
            self.p_to_h[p] = h
            log(f"PLANET {p} → HOUSE {h}")

        self.own_map = {p:[] for p in PLANET_LIT}
        for i in range(12):
            owner = RASHI_OWNERS[int(self.cusps[i]/30)]
            self.own_map[owner].append(i+1)

        log(f"RASHI OWNERSHIP MAP = {self.own_map}")
        log("------ REFRESH END ------")

    # ---------------------------------------------------
    def get_h(self, lon):
        for i in range(12):
            s = self.cusps[i]
            e = self.cusps[(i+1)%12]
            if (s < e and s <= lon < e) or \
               (s > e and (lon >= s or lon < e)):
                return i+1
        return 1

    # ---------------------------------------------------
    def analyze(self, p):
        log(f"ANALYZE PLANET = {p}")
        if p not in self.n_pos:
            return "-", "-", "-", "-", [], 0, []

        n_lon = self.n_pos[p]
        t_lon = self.t_pos[p]

        sgn = RASHI_OWNERS[int(n_lon/30)]
        str_l = PLANET_LIT[int(n_lon*3/40)%9]
        sub = PLANET_LIT[int(n_lon*27/40)%9]
        substar = PLANET_LIT[int(self.n_pos[sub]*3/40)%9]

        log(f"SIGN={sgn} STAR={str_l} SUB={sub} SUBSTAR={substar}")

        hits = (
            [self.p_to_h[p],
             self.p_to_h[str_l],
             self.p_to_h[sgn]] +
            self.own_map[str_l] +
            self.own_map[sgn] +
            [self.get_h(t_lon)]
        )

        log(f"HITS RAW = {hits}")

        pos_f = [h for h in hits if h in POS_HOUSES]
        neg_f = [h for h in hits if h in NEG_HOUSES]
        net = len(pos_f) - len(neg_f)

        log(f"POSITIVE HITS = {pos_f}")
        log(f"NEGATIVE HITS = {neg_f}")
        log(f"NET SCORE = {net}")

        asp_hits = []
        for n_nm, n_lon_b in self.n_pos.items():
            diff = abs(t_lon - n_lon_b) % 360
            if diff > 180:
                diff = 360 - diff

            for ang, name in ALL_ASPECTS:
                orb = 2.5 if ang in [0,180,120,90,60] else 1.2
                if abs(diff - ang) < orb:
                    asp_hits.append(f"{name}->{n_nm}")
                    log(
                        f"ASPECT | {p} T={t_lon:.2f} "
                        f"{n_nm} N={n_lon_b:.2f} "
                        f"DIFF={diff:.2f} ANG={ang}"
                    )

        return sgn, str_l, sub, substar, asp_hits, net, [pos_f, neg_f]

    # ---------------------------------------------------
    def dasha6(self, dt):
        log(f"DASHA QUERY DATE = {dt}")
        moon = self.birth_moon
        nak = int(moon // (360/27))
        m_lord_idx = nak % 9

        bal = (((360/27)-(moon%(360/27))) / (360/27)) * DASHA_YEARS[m_lord_idx]
        m_start = self.njd - (DASHA_YEARS[m_lord_idx] - bal) * YEAR_LEN

        t_jd = swe.julday(
            dt.year, dt.month, dt.day,
            dt.hour + dt.minute/60 - 5.5
        )

        log(f"MAHA START JD = {m_start}")

        def walk(s_jd, yrs, idx, lvl):
            if lvl == 6:
                return []

            cur = s_jd
            for k in range(9):
                i = (idx + k) % 9
                dur = (DASHA_YEARS[i]/120) * yrs * YEAR_LEN
                log(
                    f"DASHA LVL {lvl} CHECK {PLANET_LIT[i]} "
                    f"START={cur:.6f} END={(cur+dur):.6f}"
                )
                if cur <= t_jd < cur + dur:
                    return [PLANET_LIT[i]] + walk(cur, dur/YEAR_LEN, i, lvl+1)
                cur += dur
            return ["?"]

        return walk(m_start, 120, m_lord_idx, 0)

# ==================== UI ===============================
engine = KPEngineV89_DEBUG("05/04/1979", "16:55:00", 16.12, 80.93)
exit_f = False

def on_p(key):
    global exit_f
    try:
        if key == keyboard.Key.right:
            engine.view_date += timedelta(minutes=1)
            engine.refresh()
        if key == keyboard.Key.left:
            engine.view_date -= timedelta(minutes=1)
            engine.refresh()
        if hasattr(key,'char') and key.char=='q':
            exit_f = True
    except:
        pass

def draw():
    table = Table(
        title=f"KP ENGINE v89 DEBUG | {engine.view_date}",
        expand=True
    )
    table.add_column("Level")
    table.add_column("Planet")
    table.add_column("Lords")
    table.add_column("Net")
    table.add_column("Aspects")

    dashas = engine.dasha6(engine.view_date)
    lvls = ["MAHA","BHUKTI","ANTARA","SOOKSHMA","PRANA","DEHA"]

    for i,p in enumerate(dashas):
        sgn, star, sub, sstr, asp, net, dbg = engine.analyze(p)
        table.add_row(
            lvls[i],
            p,
            f"{sgn}/{star}/{sub}/{sstr}",
            str(net),
            ",".join(asp)
        )
    return table

listener = keyboard.Listener(on_press=on_p)
listener.start()

with Live(draw(), refresh_per_second=2, screen=True):
    while not exit_f:
        time.sleep(0.2)

listener.stop()
