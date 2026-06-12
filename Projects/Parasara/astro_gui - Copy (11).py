import tkinter as tk
from tkinter import ttk, messagebox
from geopy.geocoders import Nominatim
from datetime import datetime, timedelta
import traceback
import swisseph as swe
from rule_engine import RuleEngine

from calculation_engine import CalculationEngine

# =========================================================
# MAIN GUI
# =========================================================

class AstroApp:

    def __init__(self, root):
        self.root = root
        self.root.title("Astro Engine V28 - Natal + Transit")
        self.root.geometry("1400x950")

        self.engine = CalculationEngine()
        self.cached_city = None
        self.cached_coords = (16.1176, 80.9314)
        self.natal_cache = None
        self.geo = Nominatim(user_agent="astro_v28")

        # 1. నిలువు విభజన (Vertical Split)
        self.left_frame = ttk.Frame(root)
        self.left_frame.pack(side="left", fill="both", expand=True, padx=5, pady=5)
        
        self.right_frame = ttk.Frame(root)
        self.right_frame.pack(side="right", fill="both", expand=True, padx=5, pady=5)

        # 2. చార్ట్ (ఎడమవైపు - Left Frame)
        self.canvas = tk.Canvas(self.left_frame, bg="white")
        self.canvas.pack(fill="both", expand=True)

        # 3. కంట్రోల్స్ & అనాలిసిస్ (కుడివైపు - Right Frame)
        self.res_frame = ttk.LabelFrame(self.right_frame, text="Astrological Analysis")
        self.res_frame.pack(fill="both", expand=True, padx=5, pady=5)
        self.res_text = tk.Text(self.res_frame, height=20, width=60)
        self.res_text.pack(fill="both", expand=True)
        
        frame = ttk.LabelFrame(self.right_frame, text="Natal Data")
        frame.pack(fill="x", padx=5, pady=5)

        # ఇన్‌పుట్ ఫీల్డ్స్
        ttk.Label(frame, text="Name").grid(row=0, column=0, padx=5)
        self.name = ttk.Entry(frame, width=15); self.name.grid(row=0, column=1)
        ttk.Label(frame, text="DOB").grid(row=0, column=2)
        self.dob = ttk.Entry(frame, width=12); self.dob.grid(row=0, column=3)
        ttk.Label(frame, text="TOB").grid(row=1, column=0)
        self.tob = ttk.Entry(frame, width=10); self.tob.grid(row=1, column=1)
        ttk.Label(frame, text="City").grid(row=1, column=2)
        self.city = ttk.Entry(frame, width=15); self.city.grid(row=1, column=3)
        # ముఖ్యమైన మార్పు: self.tz ని ఇక్కడ డిఫైన్ చేయండి
        ttk.Label(frame, text="TZ").grid(row=1, column=4)
        self.tz = ttk.Entry(frame, width=5); self.tz.insert(0, "5.5"); self.tz.grid(row=1, column=5)

        # ట్రాన్సిట్ కంట్రోల్
        t_frame = ttk.LabelFrame(self.right_frame, text="Transit Control")
        t_frame.pack(fill="x", padx=5, pady=5)
        self.t_dob = ttk.Entry(t_frame, width=12); self.t_dob.insert(0, datetime.now().strftime("%d/%m/%Y")); self.t_dob.grid(row=0, column=0)
        self.t_tob = ttk.Entry(t_frame, width=10); self.t_tob.insert(0, datetime.now().strftime("%H:%M")); self.t_tob.grid(row=0, column=1)
        ttk.Button(t_frame, text="Generate", command=self.generate).grid(row=0, column=2, padx=5)
        ttk.Button(t_frame, text="Reset", command=self.reset_transit_to_now).grid(row=0, column=3)

        # కీబోర్డ్ బైండింగ్స్
        self.root.bind("<Up>", lambda e: self.adjust_minutes(1))
        self.root.bind("<Down>", lambda e: self.adjust_minutes(-1))
        self.root.bind("<Right>", lambda e: self.adjust_days(1))
        self.root.bind("<Left>", lambda e: self.adjust_days(-1))

        self.size = 100
        self.start_x = 50  # చార్ట్ ని సెంటర్ చేయడానికి అడ్జస్ట్ చేశాను
        self.start_y = 50

    # =====================================================
    # NEW: UPDATE TRANSIT ONLY
    # =====================================================

    def update_transit_only(self):
        if not self.natal_cache:
            return

        lat, lon = self.cached_coords
        tz = float(self.tz.get())

        td, tm, ty = map(int, self.t_dob.get().split("/"))
        th, tmin = map(int, self.t_tob.get().split(":"))
        transit_dt = datetime(ty, tm, td, th, tmin)
        transit_dt_utc = transit_dt - timedelta(hours=tz)
        
        transit_jd = swe.julday(transit_dt_utc.year, transit_dt_utc.month, 
                                transit_dt_utc.day, transit_dt_utc.hour + transit_dt_utc.minute/60)
        
        transit_data = self.engine.get_planets_with_retro(transit_jd, lat, lon)
        self.draw_planets(self.natal_cache, transit_data)

    # =====================================================
    # ADJUST METHODS (Now calling update_transit_only)
    # =====================================================
    # =====================================================
    # RESET TRANSIT TO NOW
    # =====================================================

    def reset_transit_to_now(self):
        now = datetime.now()
        
        # Update Date
        self.t_dob.delete(0, tk.END)
        self.t_dob.insert(0, now.strftime("%d/%m/%Y"))
        
        # Update Time
        self.t_tob.delete(0, tk.END)
        self.t_tob.insert(0, now.strftime("%H:%M"))
        
        # Refresh display
        self.update_transit_only()

    def adjust_minutes(self, delta):
        try:
            t = datetime.strptime(self.t_tob.get(), "%H:%M")
            t = t + timedelta(minutes=delta)
            self.t_tob.delete(0, tk.END)
            self.t_tob.insert(0, t.strftime("%H:%M"))
            self.update_transit_only()
        except: pass

    def adjust_days(self, delta):
        try:
            d = datetime.strptime(self.t_dob.get(), "%d/%m/%Y")
            d = d + timedelta(days=delta)
            self.t_dob.delete(0, tk.END)
            self.t_dob.insert(0, d.strftime("%d/%m/%Y"))
            self.update_transit_only()
        except: pass

    # =====================================================
    # GENERATE
    # =====================================================

    def generate(self):
        try:
            lat, lon = self.get_coords()
            tz = float(self.tz.get())

            # Natal Data
            d, m, y = map(int, self.dob.get().split("/"))
            hh, mm, ss = map(int, self.tob.get().split(":"))
            natal_dt_utc = datetime(y, m, d, hh, mm, ss) - timedelta(hours=tz)
            natal_jd = swe.julday(natal_dt_utc.year, natal_dt_utc.month, natal_dt_utc.day, 
                                natal_dt_utc.hour + natal_dt_utc.minute/60 + natal_dt_utc.second/3600)

            # Store in cache
            self.natal_cache = self.engine.get_planets_with_retro(natal_jd, lat, lon)
            
            # Update transit display
            self.update_transit_only()

            # =====================================================
            # NEW: RuleEngine Integration
            # =====================================================
            rule_engine = RuleEngine()
            self.res_text.delete(1.0, tk.END) # Clear old analysis
            
            # Analysis for Sun as an example (You can loop this for all planets)
            # Note: Ensure your CalculationEngine provides rasi and house_num
            # Here I am passing dummy values for rasi/house_num; replace with engine data
            sun_data = self.natal_cache.get("Sun", {"lon": 0})
            sign = int(sun_data["lon"] // 30)
            
            analysis = rule_engine.analyze_planet(
                lagna="Mesha", # Replace with actual lagna from engine
                planet="Sun", 
                sign=sign, 
                degree=sun_data["lon"] % 30, 
                house_num=1,   # Replace with actual house calculation
                rasi=sign, 
                rasi_lord="Sun" # Replace with actual lord logic
            )
            self.res_text.insert(tk.END, analysis)

        except Exception as e:
            traceback.print_exc()
            messagebox.showerror("Error", f"Calculation failed:\n{str(e)}")

    def get_coords(self):
        city = self.city.get().strip()
        if city == "": return 16.1176, 80.9314
        if city == self.cached_city: return self.cached_coords
        try:
            location = self.geo.geocode(city, timeout=5)
            if location:
                self.cached_city = city
                self.cached_coords = (float(location.latitude), float(location.longitude))
                return self.cached_coords
        except: pass
        return self.cached_coords

    # (Keep draw_grid, draw_planets, get_coords_map as they were)
    def get_coords_map(self):
        return {11:(0,0),0:(1,0),1:(2,0),2:(3,0),3:(3,1),4:(3,2),5:(3,3),6:(2,3),7:(1,3),8:(0,3),9:(0,2),10:(0,1)}

    def draw_grid(self):
        self.canvas.delete("all")
        for r in range(4):
            for c in range(4):
                if r in [1,2] and c in [1,2]: continue
                self.canvas.create_rectangle(self.start_x + c*self.size, self.start_y + r*self.size, 
                                           self.start_x + c*self.size + self.size, self.start_y + r*self.size + self.size, width=2)
        names = ["Ar","Ta","Ge","Cn","Le","Vi","Li","Sc","Sg","Cp","Aq","Pi"]
        cmap = self.get_coords_map()
        for i in range(12):
            c, r = cmap[i]
            self.canvas.create_text(self.start_x + c*self.size + 10, self.start_y + r*self.size + 10, 
                                    text=names[i], fill="blue", anchor="nw", font=("Arial", 9, "bold"))

    def draw_planets(self, natal, transit):
        self.draw_grid()
        cmap = self.get_coords_map()
        cells = {i: {"nat": [], "tra": []} for i in range(12)}
        short = {"Sun":"Su","Moon":"Mo","Mars":"Ma","Mercury":"Me","Jupiter":"Ju","Venus":"Ve","Saturn":"Sa","Rahu":"Ra"}

        # 1. ప్లానెట్ డేటాను ప్రాసెస్ చేయడం
        def process(data, is_transit):
            key = "tra" if is_transit else "nat"
            for p, info in data.items():
                lon = info["lon"]
                sign = int(lon // 30)
                retro = "(R)" if info.get("retro") else ""
                
                if p == "Rahu":
                    label = "RaT" if is_transit else "Ra"
                    cells[sign][key].append(label + retro)
                    ksign = (sign + 6) % 12
                    klabel = "KeT" if is_transit else "Ke"
                    cells[ksign][key].append(klabel + retro)
                elif p == "Asc":
                    # Ascendant కోసం మార్పు
                    label = "AscT" if is_transit else "Asc"
                    cells[sign][key].append(label)    
                elif p in short:
                    label = short[p] + ("T" if is_transit else "")
                    cells[sign][key].append(label + retro)

        process(natal, False)
        process(transit, True)

        # 2. డ్రాయింగ్ అలైన్‌మెంట్ (Vertical Split కి తగ్గట్టుగా)
        self.start_x = 50 
        self.start_y = 50
        
        for i in range(12):
            c, r = cmap[i]
            x, y = self.start_x + c * self.size, self.start_y + r * self.size
            
            # Natal (గ్రీన్) - ఎడమ వైపు (x + 35)
            if cells[i]["nat"]:
                self.canvas.create_text(x + 35, y + 55, text="\n".join(cells[i]["nat"]), 
                                        fill="green", font=("Arial", 9, "bold"), justify="center")
            
            # Transit (రెడ్) - కుడి వైపు (x + 75)
            if cells[i]["tra"]:
                self.canvas.create_text(x + 75, y + 55, text="\n".join(cells[i]["tra"]), 
                                        fill="red", font=("Arial", 9, "bold"), justify="center")

root = tk.Tk()
app = AstroApp(root)
root.mainloop()