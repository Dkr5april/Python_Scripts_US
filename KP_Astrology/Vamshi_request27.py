import swisseph as swe
import os, time
from datetime import datetime, timedelta
from collections import Counter
from pynput import keyboard
from rich.live import Live
from rich.table import Table
from rich.console import Console

console = Console()

# ==================== CONSTANTS =======================
DEBUG_MODE = True
YEAR_LEN = 365.2425
EPS = 1e-7

swe.set_ephe_path("./ephe")
swe.set_sid_mode(swe.SIDM_KRISHNAMURTI)

PLANET_LIT = ["Ke","Ve","Su","Mo","Ma","Ra","Ju","Sa","Me"]
DASHA_YEARS = [7, 20, 6, 10, 7, 18, 16, 19, 17]
TOTAL_YEARS = sum(DASHA_YEARS)

RASHI_OWNERS = {
    0:"Ma", 1:"Ve", 2:"Me", 3:"Mo", 4:"Su", 5:"Me",
    6:"Ve", 7:"Ma", 8:"Ju", 9:"Sa", 10:"Sa", 11:"Ju"
}

POS_HOUSES = {1,2,3,6,10,11}
NEG_HOUSES = {8,12}

ALL_ASPECTS = [
    (0,"Conj"),(180,"Oppo"),(120,"Trin"),(90,"Squa"),
    (60,"Sext"),(30,"SSxt"),(45,"SSqu"),
    (150,"Quin"),(72,"Qnt"),(135,"Sesq")
]

# ==================== ENGINE ==========================
class KPEngineV89:

    def __init__(self, dob, tob, lat, lon):
        self.lat, self.lon = lat, lon
        d,m,y = map(int, dob.split("/"))
        hh,mm,ss = map(int, tob.split(":"))

        self.njd = swe.julday(y,m,d, hh+mm/60+ss/3600 - 5.5)
        flag = swe.FLG_SWIEPH | swe.FLG_SIDEREAL

        self.birth_moon = swe.calc_ut(self.njd, swe.MOON, flag)[0][0]
        self.view_date = datetime.now()
        self.refresh()

    # ================= KP LORD CALC ===================
    def kp_lords(self, lon, depth=4):
        """
        Returns:
        STAR, SUB, SUBSUB, SUBSUBSUB + DEBUG INFO
        """
        NAK_LEN = 360 / 27
        nak_idx = int(lon // NAK_LEN)
        nak_start = nak_idx * NAK_LEN
        pos = lon - nak_start

        star_idx = nak_idx % 9
        star = PLANET_LIT[star_idx]

        result = [star]
        debug = [f"NakIdx={nak_idx}, NakPos={pos:.6f}"]

        base_len = NAK_LEN
        cur_idx = star_idx

        for lvl in range(1, depth):
            acc = 0
            for i in range(9):
                idx = (cur_idx + i) % 9
                part = (DASHA_YEARS[idx] / TOTAL_YEARS) * base_len
                if acc + part >= pos:
                    result.append(PLANET_LIT[idx])
                    debug.append(
                        f"L{lvl} {PLANET_LIT[idx]} | "
                        f"Seg={part:.6f} Off={pos-acc:.6f}"
                    )
                    pos -= acc
                    base_len = part
                    cur_idx = idx
                    break
                acc += part

        return result, debug

    # ================= REFRESH ========================
    def refresh(self):
        flag = swe.FLG_SWIEPH | swe.FLG_SIDEREAL
        t_jd = swe.julday(
            self.view_date.year, self.view_date.month,
            self.view_date.day,
            self.view_date.hour + self.view_date.minute/60 - 5.5
        )

        self.n_pos, self.t_pos = {}, {}
        for pid,nm in [
            (0,"Su"),(1,"Mo"),(2,"Me"),(3,"Ve"),
            (4,"Ma"),(5,"Ju"),(6,"Sa"),(11,"Ra")
        ]:
            self.n_pos[nm] = swe.calc_ut(self.njd, pid, flag)[0][0]
            self.t_pos[nm] = swe.calc_ut(t_jd, pid, flag)[0][0]

        self.n_pos["Ke"] = (self.n_pos["Ra"] + 180) % 360
        self.t_pos["Ke"] = (self.t_pos["Ra"] + 180) % 360

        self.cusps = swe.houses_ex(self.njd, self.lat, self.lon, b'P', flag)[0]
        self.p_to_h = {p:self.get_h(lon) for p,lon in self.n_pos.items()}

        self.own_map = {p:[] for p in PLANET_LIT}
        for i in range(12):
            owner = RASHI_OWNERS[int(self.cusps[i]/30)]
            self.own_map[owner].append(i+1)

    def get_h(self, lon):
        for i in range(12):
            s,e = self.cusps[i], self.cusps[(i+1)%12]
            if (s<e and s<=lon<e) or (s>e and (lon>=s or lon<e)):
                return i+1
        return 1

    # ================= ANALYZE ========================
    def analyze(self, p):
        if p=="?" or p not in self.n_pos:
            return "-", "-", "-", "-", "-", "-", [], 0, []

        n_lon = self.n_pos[p]
        t_lon = self.t_pos[p]

        sgn = RASHI_OWNERS[int(n_lon/30)]

        lords, kp_debug = self.kp_lords(n_lon, depth=4)
        star, sub, subsub, subsubsub = lords

        sub_star = PLANET_LIT[int(self.n_pos[sub] // (360/27)) % 9]

        hits = (
            [self.p_to_h[p], self.p_to_h[star], self.p_to_h[sgn]] +
            self.own_map[star] + self.own_map[sgn] +
            [self.get_h(t_lon)]
        )

        pos_f = sorted(h for h in hits if h in POS_HOUSES)
        neg_f = sorted(h for h in hits if h in NEG_HOUSES)
        net = len(pos_f) - len(neg_f)

        debug_info = [
            f"P:{pos_f}",
            f"N:{neg_f}",
            *kp_debug
        ]

        asp_hits = []
        for n_nm,n_lon_birth in self.n_pos.items():
            diff = abs(t_lon - n_lon_birth) % 360
            if diff>180: diff=360-diff
            for ang,name in ALL_ASPECTS:
                orb = 2.5 if ang in [0,180,120,90,60] else 1.2
                if abs(diff-ang) < orb:
                    asp_hits.append(f"{name}->{n_nm}")

        return (
            sgn, star, sub, subsub, subsubsub, sub_star,
            asp_hits, net, debug_info
        )

    # ================= DASHA ==========================
    def dasha6(self, dt):
        moon = self.birth_moon
        nak = int(moon // (360/27))
        m_idx = nak % 9

        bal = (((360/27)-(moon%(360/27)))/(360/27))*DASHA_YEARS[m_idx]
        m_start = self.njd - (DASHA_YEARS[m_idx]-bal)*YEAR_LEN

        t_jd = swe.julday(
            dt.year,dt.month,dt.day,
            dt.hour+dt.minute/60 - 5.5
        )

        def walk(s_jd, t_yrs, idx, lvl):
            if lvl==6: return []
            cur = s_jd
            for k in range(9):
                i = (idx+k)%9
                dur = (DASHA_YEARS[i]/120)*t_yrs*YEAR_LEN
                if cur<=t_jd<cur+dur:
                    return [PLANET_LIT[i]] + walk(cur, dur/YEAR_LEN, i, lvl+1)
                cur += dur
            return ["?"]

        return walk(m_start,120,m_idx,0)

# ==================== UI ==============================
engine = KPEngineV89("05/04/1979","16:55:00",16.12,80.93)
exit_f = False

def on_p(key):
    global exit_f
    try:
        if key==keyboard.Key.right:
            engine.view_date+=timedelta(days=1); engine.refresh()
        if key==keyboard.Key.left:
            engine.view_date-=timedelta(days=1); engine.refresh()
        if hasattr(key,'char') and key.char=='q':
            exit_f=True
    except: pass

def draw():
    table = Table(
        title=f"KP MASTER ENGINE V89 | {engine.view_date}",
        expand=True
    )
    table.add_column("Lvl")
    table.add_column("Planet")
    table.add_column("Sgn / Star / Sub / SSub / SSSub (Sub★)")
    if DEBUG_MODE:
        table.add_column("DEBUG")
    table.add_column("Net")
    table.add_column("Aspects")

    lvls = ["MAHA","BHUKTI","ANTARA","SOOK","PRANA","DEHA"]
    dashas = engine.dasha6(engine.view_date)

    for i,p in enumerate(dashas):
        sgn,star,sub,ss,sss,sub_star,asp,net,dbg = engine.analyze(p)
        row = [
            lvls[i],
            p,
            f"{sgn}/{star}/{sub}/{ss}/{sss} (★{sub_star})"
        ]
        if DEBUG_MODE:
            row.append(" | ".join(dbg))
        row += [str(net), ", ".join(asp)]
        table.add_row(*row)

    return table

listener = keyboard.Listener(on_press=on_p)
listener.start()

with Live(draw(), refresh_per_second=2, screen=True):
    while not exit_f:
        time.sleep(0.2)

listener.stop()
