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

# ---------- CONFIG ----------
if sys.platform == "win32":
    os.system("color")

swe.set_ephe_path("./ephe")
console = Console(force_terminal=True)
geolocator = Nominatim(user_agent="astro_hybrid_engine")

ORB_MAJOR = 3
ORB_MINOR = 2
ORB_DEC = 1.5
ORB_STAR = 1.5

SHOW = {
    "ASPECT": True,
    "PARALLEL": True,
    "ANTISCIA": True,
    "MIDPOINT": True,
    "STAR": True,
    "VEDIC": True,
    "INFO": True
}

# ---------- HELPERS ----------
def ang_diff(a,b):
    return min(abs(a-b),360-abs(a-b))

def midpoint(a,b):
    return (a+b)/2 % 360

# ---------- ENGINE ----------
class AstroEngine:
    def __init__(self, name, jd, lat, lon):
        self.name=name
        self.jd=jd
        self.lat=lat
        self.lon=lon
        self.mode="SIDEREAL"
        self.view_date=datetime.now()

    def planets(self,jd,sid):
        flags=swe.FLG_SWIEPH|swe.FLG_SPEED
        if sid: flags|=swe.FLG_SIDEREAL

        plist=[0,1,2,3,4,5,6,11]
        names=["Su","Mo","Me","Ve","Ma","Ju","Sa","Ra"]

        data={}
        for pid,n in zip(plist,names):
            r,_=swe.calc_ut(jd,pid,flags)
            data[n]={"lon":r[0]%360,"dec":r[1]}
            if n=="Ra":
                data["Ke"]={"lon":(r[0]+180)%360,"dec":-r[1]}
        return data

    def init_vedic(self, p_sid):
        sun = p_sid["Su"]["lon"]

        self.n_up = {
            "Kala": (sun + 30) % 360,
            "Gulika": (sun + 90) % 360,
            "Yama": (sun + 150) % 360
        }

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

# ---------- ASPECTS ----------
ASPECTS={
    0:("CONJ","New start"),
    60:("SEXT","Opportunity"),
    90:("SQR","Tension"),
    120:("TRI","Flow"),
    180:("OPP","External event"),
    150:("QUINC","Adjustment"),
    45:("SEMISQR","Irritation"),
    135:("SESQUI","Pressure")
}

STARS={"Regulus":150,"Spica":204,"Algol":26,"Aldebaran":69}

# ---------- TABLE ----------
def get_table(engine):

    table=Table(title=f"{engine.name} ({engine.mode})",expand=True)
    table.add_column("Type")
    table.add_column("Detail")
    table.add_column("Impact")

    jd=swe.julday(engine.view_date.year,engine.view_date.month,engine.view_date.day,12)
    use_sid=(engine.mode=="SIDEREAL")

    p=engine.planets(jd,use_sid)

    # Initialize vedic once
    if use_sid:
        engine.init_vedic(p)

    # ---------- VEDIC ----------
    if use_sid and SHOW["VEDIC"]:
        for tp,tv in p.items():
            for name,lon in {**engine.n_up,**engine.n_apra}.items():
                if ang_diff(tv["lon"],lon)<ORB_MINOR:

                    if name in ["Dhuma","Vyatipata"]:
                        eff="BAD"; msg="Obstacles / confusion"
                    elif name in ["IndraChapa","Upaketu"]:
                        eff="GOOD"; msg="Insight / help"
                    else:
                        eff="MIXED"; msg="Karmic trigger"

                    table.add_row("Shadow",f"{tp}->{name}",f"{eff} | {msg}")

    # ---------- ASPECTS ----------
    if SHOW["ASPECT"]:
        for a,pa in p.items():
            for b,pb in p.items():
                if a>=b: continue
                d=ang_diff(pa["lon"],pb["lon"])
                for deg,(nm,msg) in ASPECTS.items():
                    orb=ORB_MAJOR if deg in [0,60,90,120,180] else ORB_MINOR
                    if abs(d-deg)<orb:
                        strength="STRONG" if abs(d-deg)<1 else "WEAK"
                        table.add_row("Aspect",f"{a}-{b} {nm}",f"{msg} ({strength})")

    # ---------- PARALLEL ----------
    if SHOW["PARALLEL"]:
        for a,pa in p.items():
            for b,pb in p.items():
                if a>=b: continue
                if abs(pa["dec"]-pb["dec"])<ORB_DEC:
                    table.add_row("Parallel",f"{a}-{b}","Amplified")
                if abs(pa["dec"]+pb["dec"])<ORB_DEC:
                    table.add_row("Contra",f"{a}-{b}","Conflict")

    # ---------- ANTISCIA ----------
    if SHOW["ANTISCIA"] and not use_sid:
        valid=["Su","Mo","Me","Ve","Ma","Ju","Sa"]
        for k in valid:
            ant=(180-p[k]["lon"])%360
            cant=(180+p[k]["lon"])%360

            for tp,tv in p.items():
                if ang_diff(tv["lon"],ant)<ORB_MINOR:
                    table.add_row("Ant",f"{tp}-{k}","Hidden support")
                if ang_diff(tv["lon"],cant)<ORB_MINOR:
                    table.add_row("ContraAnt",f"{tp}-{k}","Hidden tension")

    # ---------- MIDPOINT ----------
    if SHOW["MIDPOINT"]:
        m=midpoint(p["Su"]["lon"],p["Mo"]["lon"])
        for tp,tv in p.items():
            if ang_diff(tv["lon"],m)<ORB_MINOR:
                table.add_row("Midpoint","Sun/Moon","Life trigger")

    # ---------- STARS ----------
    if SHOW["STAR"]:
        for tp,tv in p.items():
            for s,lon in STARS.items():
                if ang_diff(tv["lon"],lon)<ORB_STAR:
                    table.add_row("Star",f"{tp}-{s}","Fated event")

    return table

# ---------- INFO ----------
def info():
    if not SHOW["INFO"]: return Panel("")
    return Panel("""
T: Mode | A: Aspects | P: Parallel
N: Antiscion | M: Midpoint | F: Stars
V: Vedic | I: Info | Q: Quit
""",title="Help")

# ---------- LAYOUT ----------
def layout(engine):
    lay=Layout()
    lay.split_column(
        Layout(Panel(f"{engine.name} | Mode: {engine.mode}"),size=3),
        Layout(name="body")
    )
    lay["body"].split_row(
        Layout(get_table(engine)),
        Layout(info(),size=30)
    )
    return lay

# ---------- RUN ----------
name=input("Name: ")
dob=input("DOB dd/mm/yyyy: ")
tob=input("TOB hh:mm:ss: ")
city=input("City: ")

d,m,y=map(int,dob.split("/"))
hh,mm,ss=map(int,tob.split(":"))
h=hh+mm/60+ss/3600

lat,lon=16.1,80.9
try:
    loc=geolocator.geocode(city)
    if loc: lat,lon=loc.latitude,loc.longitude
except: pass

jd=swe.julday(y,m,d,h)
engine=AstroEngine(name,jd,lat,lon)

def on_press(key):
    try:
        if hasattr(key,'char'):
            c=key.char.lower()
            if c=="t": engine.mode="TROPICAL" if engine.mode=="SIDEREAL" else "SIDEREAL"
            if c=="a": SHOW["ASPECT"]=not SHOW["ASPECT"]
            if c=="p": SHOW["PARALLEL"]=not SHOW["PARALLEL"]
            if c=="n": SHOW["ANTISCIA"]=not SHOW["ANTISCIA"]
            if c=="m": SHOW["MIDPOINT"]=not SHOW["MIDPOINT"]
            if c=="f": SHOW["STAR"]=not SHOW["STAR"]
            if c=="v": SHOW["VEDIC"]=not SHOW["VEDIC"]
            if c=="i": SHOW["INFO"]=not SHOW["INFO"]
            if c=="q": exit()
    except: pass

keyboard.Listener(on_press=on_press).start()

with Live(layout(engine),console=console,refresh_per_second=4,screen=True):
    while True:
        time.sleep(0.1)