import customtkinter as ctk # Import CustomTkinter
from tkinter import ttk
import ctypes
import platform
from tkinter import messagebox, END
from dasa_engine import DasaEngine

# DPI Scaling fix
if platform.system() == "Windows":
    ctypes.windll.shcore.SetProcessDpiAwareness(1)
    
from geopy.geocoders import Nominatim
from datetime import datetime, timedelta
import traceback
import swisseph as swe
from rule_engine import RuleEngine
from input_engine import InputEngine
from calculation_engine import CalculationEngine

# థీమ్ సెట్టింగ్స్
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

class AstroApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Astro Engine V28 - Natal + Transit")
        self.root.geometry("1400x950")

        self.engine = CalculationEngine()
        self.dasa_engine = DasaEngine()
        self.cached_city = None
        self.cached_coords = (16.1176, 80.9314)
        self.natal_cache = None
        self.geo = Nominatim(user_agent="astro_v28")

        # Layout
        self.left_frame = ctk.CTkFrame(root)
        self.left_frame.pack(side="left", fill="both", expand=True, padx=5, pady=5)
        
        self.right_frame = ctk.CTkFrame(root)
        self.right_frame.pack(side="right", fill="both", expand=True, padx=5, pady=5)

        # Canvas
        self.canvas = ctk.CTkCanvas(self.left_frame, bg="#2b2b2b", highlightthickness=0)
        self.canvas.pack(fill="both", expand=True)

        # Analysis
        self.res_frame = ctk.CTkLabel(self.right_frame, text="Astrological Analysis")
        self.res_frame.pack(fill="x", padx=5, pady=5)
        self.res_text = ctk.CTkTextbox(self.right_frame, height=300)
        self.res_text.pack(fill="both", expand=True, padx=5, pady=5)
               
        # Natal Data
        frame = ctk.CTkFrame(self.right_frame)
        frame.pack(fill="x", padx=5, pady=5)
        b_frame = ctk.CTkFrame(self.right_frame)
        b_frame.pack(fill="x", padx=5, pady=5)

        ctk.CTkLabel(frame, text="Name").grid(row=0, column=0, padx=5)
        self.name = ctk.CTkEntry(frame, width=150); self.name.grid(row=0, column=1)
        ctk.CTkLabel(frame, text="DOB").grid(row=0, column=2)
        self.dob = ctk.CTkEntry(frame, width=120); self.dob.grid(row=0, column=3)
        ctk.CTkLabel(frame, text="TOB").grid(row=1, column=0)
        self.tob = ctk.CTkEntry(frame, width=100); self.tob.grid(row=1, column=1)
        ctk.CTkLabel(frame, text="City").grid(row=1, column=2)
        self.city = ctk.CTkEntry(frame, width=150); self.city.grid(row=1, column=3)
        ctk.CTkLabel(frame, text="TZ").grid(row=1, column=4)
        self.tz = ctk.CTkEntry(frame, width=60); self.tz.insert(0, "5.5"); self.tz.grid(row=1, column=5)
        #Adding buttons for dasas in the chart
        ctk.CTkButton(b_frame, text="Entire Dasa", command=self.show_entire_dasa).pack(side="left", padx=5, pady=5, expand=True)
        ctk.CTkButton(b_frame, text="Current Dasa", command=self.show_current_dasa).pack(side="left", padx=5, pady=5, expand=True)
        ctk.CTkButton(b_frame, text="Transit Dasa", command=self.show_transit_dasa).pack(side="left", padx=5, pady=5, expand=True)
        ctk.CTkButton(b_frame, text="Analysis", command=self.show_analysis).pack(side="left", padx=5, pady=5)
        
        # Transit Control
        t_frame = ctk.CTkFrame(self.right_frame)
        t_frame.pack(fill="x", padx=5, pady=5)
        self.t_dob = ctk.CTkEntry(t_frame, width=120); self.t_dob.insert(0, datetime.now().strftime("%d/%m/%Y")); self.t_dob.grid(row=0, column=0)
        self.t_tob = ctk.CTkEntry(t_frame, width=100); self.t_tob.insert(0, datetime.now().strftime("%H:%M")); self.t_tob.grid(row=0, column=1)
        ctk.CTkButton(t_frame, text="Generate", command=self.generate, width=100).grid(row=0, column=2, padx=5)
        ctk.CTkButton(t_frame, text="Reset", command=self.reset_transit_to_now, width=100).grid(row=0, column=3)

        self.input_engine = InputEngine(self)
        self.input_engine.bind_inputs()

        self.size = 100
        self.start_x = 50
        self.start_y = 50
        self.user_buffer = {"name": "", "dob": "", "tob": "", "tz": "5.5"}
        # 1. Set the default values
        self.name.insert(0, "Koteswararao")
        self.dob.insert(0, "05/04/1979")
        self.tob.insert(0, "16:23:00")
        self.city.insert(0, "Challapalli")

        
        #Dasa Methods
    def _ensure_tree_exists(self):
        """Helper to create or reset the Treeview frame/widget."""
        if not hasattr(self, 'dasa_tree'):
            self.tree_frame = ctk.CTkFrame(self.right_frame)
            self.dasa_tree = ttk.Treeview(self.tree_frame, columns=("start", "end"), show="tree headings")
            scrollbar = ttk.Scrollbar(self.tree_frame, orient="vertical", command=self.dasa_tree.yview)
            self.dasa_tree.configure(yscrollcommand=scrollbar.set)
            scrollbar.pack(side="right", fill="y")
            self.dasa_tree.pack(side="left", fill="both", expand=True)
            self.dasa_tree.heading("#0", text="Dasa Lord")
            self.dasa_tree.heading("start", text="Start")
            self.dasa_tree.heading("end", text="End")
            self.dasa_tree.column("start", width=100)
            self.dasa_tree.column("end", width=100)

    def show_entire_dasa(self):
        # 1. Hide Text View, Show Tree View
        if hasattr(self, 'res_text'): self.res_text.pack_forget()
        self._ensure_tree_exists()
        self.tree_frame.pack(fill="both", expand=True, padx=5, pady=5)
        
        # 2. Populate Tree
        self.dasa_tree.delete(*self.dasa_tree.get_children())
        for entry in self.dasa_engine.get_structured_timeline(self.dasa_timeline):
            self.dasa_tree.insert(parent=entry['parent_id'], index="end", iid=entry['id'], 
                                  text=entry['lord'], values=(entry['start'].strftime('%d-%m-%Y'), 
                                  entry['end'].strftime('%d-%m-%Y')))

    def show_current_dasa(self):
        # 1. Hide Text View, Show Tree View
        if hasattr(self, 'res_text'): self.res_text.pack_forget()
        self._ensure_tree_exists()
        self.tree_frame.pack(fill="both", expand=True, padx=5, pady=5)
        
        # 2. Populate Tree with FILTERED data
        self.dasa_tree.delete(*self.dasa_tree.get_children())
        now = datetime.now()
        current_data = [e for e in self.dasa_timeline if e['start'] <= now <= e['end']]
        for entry in self.dasa_engine.get_structured_timeline(current_data):
            self.dasa_tree.insert(parent=entry['parent_id'], index="end", iid=entry['id'], 
                                  text=entry['lord'], values=(entry['start'].strftime('%d-%m-%Y'), 
                                  entry['end'].strftime('%d-%m-%Y')))

    def show_analysis(self):
        # 1. Hide Tree View, Show Text View
        if hasattr(self, 'tree_frame'): self.tree_frame.pack_forget()
        self.res_text.pack(fill="both", expand=True, padx=5, pady=5)
        # ... logic to fill self.res_text ...

    def show_transit_dasa(self):
        # Placeholder: This will eventually cross-reference the active Dasa 
        # with current planetary transit positions
        self.res_text.delete(1.0, END)
        self.res_text.insert(END, "--- TRANSIT DASA INFLUENCE ---\n")
        self.res_text.insert(END, "Feature coming soon: Cross-referencing Transit with Active Dasa.")

        
    # మిగిలిన ఫంక్షన్స్ (generate, update_transit_only, etc.) యథాతథంగా ఉంచండి...
    # గమనిక: అన్నీ tkinter విడ్జెట్ మెథడ్స్ (delete, insert, config) CTkEntry కి కూడా పనిచేస్తాయి.
    def update_transit_only(self):
        # We check both natal_cache and dasa_timeline to ensure the data is ready
        if not self.natal_cache or not hasattr(self, 'dasa_timeline'):
            return
            
        try:
            lat, lon = self.cached_coords
            tz = float(self.user_buffer.get("tz", 5.5))

            # 1. Parse Transit Date from the UI
            td, tm, ty = map(int, self.t_dob.get().split("/"))
            th, tmin = map(int, self.t_tob.get().split(":"))
            transit_dt = datetime(ty, tm, td, th, tmin)
            transit_dt_utc = transit_dt - timedelta(hours=tz)
            
            # 2. Calculate Julian Day
            transit_jd = swe.julday(transit_dt_utc.year, transit_dt_utc.month, 
                                   transit_dt_utc.day, transit_dt_utc.hour + transit_dt_utc.minute/60)
            
            # 3. Get Data and Draw Planets
            transit_data = self.engine.get_planets_with_retro(transit_jd, lat, lon)
            self.draw_planets(self.natal_cache, transit_data)
            
            
        except Exception as e:
            print(f"Update error: {e}") 
            
    # =====================================================
    # ADJUST METHODS (Now calling update_transit_only)
    # =====================================================
    # =====================================================
    # RESET TRANSIT TO NOW
    # =====================================================

    def reset_transit_to_now(self):
        now = datetime.now()
        
        # Update Date
        self.t_dob.delete(0, END)
        self.t_dob.insert(0, now.strftime("%d/%m/%Y"))
        
        # Update Time
        self.t_tob.delete(0, END)
        self.t_tob.insert(0, now.strftime("%H:%M"))
        
        # Refresh display
        self.update_transit_only()
    
    def adjust_transit(self, delta):
        # ఇక్కడ మనం InputEngine లో ఏ మోడ్ ఉందో దాన్ని బట్టి 
        # పాత adjust_datetime ఫంక్షన్‌ని పిలుస్తున్నాం
        mode = self.input_engine.current_mode
        self.adjust_datetime(mode, delta)

    def adjust_minutes(self, delta):
        try:
            t = datetime.strptime(self.t_tob.get(), "%H:%M")
            t = t + timedelta(minutes=delta)
            self.t_tob.delete(0, END)
            self.t_tob.insert(0, t.strftime("%H:%M"))
            self.update_transit_only()
        except: pass

    def adjust_days(self, delta):
        try:
            d = datetime.strptime(self.t_dob.get(), "%d/%m/%Y")
            d = d + timedelta(days=delta)
            self.t_dob.delete(0, END)
            self.t_dob.insert(0, d.strftime("%d/%m/%Y"))
            self.update_transit_only()
        except: pass
        
    def adjust_datetime(self, unit, delta):
        try:
            # Entry బాక్సుల నుండి డేటా తీసుకోవడం
            d = datetime.strptime(self.t_dob.get(), "%d/%m/%Y")
            t = datetime.strptime(self.t_tob.get(), "%H:%M")
            
            if unit == "minute":
                t = t + timedelta(minutes=delta)
            elif unit == "hour":
                t = t + timedelta(hours=delta)
            elif unit == "day":
                d = d + timedelta(days=delta)
            elif unit == "month":
                # నెలను అడ్జస్ట్ చేయడం
                new_month = d.month + delta
                new_year = d.year + (new_month - 1) // 12
                new_month = (new_month - 1) % 12 + 1
                d = d.replace(year=new_year, month=new_month)
            elif unit == "year":
                d = d.replace(year=d.year + delta)

            # అప్‌డేట్ చేయడం
            self.t_dob.delete(0, END)
            self.t_dob.insert(0, d.strftime("%d/%m/%Y"))
            self.t_tob.delete(0, END)
            self.t_tob.insert(0, t.strftime("%H:%M"))
            
            # రిఫ్రెష్ చేయడం
            self.update_transit_only()
        except Exception as e:
            print(f"Error in adjustment: {e}")    

    # =====================================================
    # GENERATE
    # =====================================================

    def generate(self):
        self.user_buffer["name"] = self.name.get()
        self.user_buffer["dob"] = self.dob.get()
        self.user_buffer["tob"] = self.tob.get()
        self.user_buffer["tz"] = self.tz.get()
        
        try:
            lat, lon = self.get_coords()
            tz = float(self.tz.get())

            # Natal Data
            d, m, y = map(int, self.dob.get().split("/"))
            hh, mm, ss = map(int, self.tob.get().split(":"))
            
            birth_dt = datetime(y, m, d, hh, mm, ss)
            natal_dt_utc = birth_dt - timedelta(hours=tz)
            natal_jd = swe.julday(natal_dt_utc.year, natal_dt_utc.month, natal_dt_utc.day, 
                                  natal_dt_utc.hour + natal_dt_utc.minute/60 + natal_dt_utc.second/3600)

            # Store in cache
            self.natal_cache = self.engine.get_planets_with_retro(natal_jd, lat, lon)
            
            # --- Dasa Calculation Integration ---
            moon_lon = self.natal_cache["Moon"]["lon"]
            self.dasa_timeline = self.dasa_engine.calculate_dasa_tree(moon_lon, birth_dt, max_depth=3)
            
            # Update transit display
            self.update_transit_only()

            # --- RuleEngine Integration ---
            rule_engine = RuleEngine()
            self.res_text.delete(1.0, END) # Clear old analysis
                                 
            # Analysis for Sun
            sun_data = self.natal_cache.get("Sun", {"lon": 0})
            sign = int(sun_data["lon"] // 30)
            
            analysis = rule_engine.analyze_planet(
                lagna="Mesha", # Replace with actual lagna calculation from engine
                planet="Sun", 
                sign=sign, 
                degree=sun_data["lon"] % 30, 
                house_num=1,   # Replace with actual house calculation
                rasi=sign, 
                rasi_lord="Sun" # Replace with actual lord logic
            )
            self.res_text.insert(END, analysis)

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
        
        # ఇక్కడ 'Asc': 'Asc' ని యాడ్ చేశాను
        short = {
            "Sun":"Su","Moon":"Mo","Mars":"Ma","Mercury":"Me","Jupiter":"Ju",
            "Venus":"Ve","Saturn":"Sa","Rahu":"Ra","Asc":"Asc"
        }

        def process(data, is_transit):
            key = "tra" if is_transit else "nat"
            for p, info in data.items():
                # మీకున్న కోడ్ చాలా బాగుంది, Asc ని కూడా ఒకే పద్ధతిలో హ్యాండిల్ చేద్దాం
                lon = info["lon"]
                sign = int(lon // 30)
                retro = "(R)" if info.get("retro") else ""
                
                if p == "Rahu":
                    label = "RaT" if is_transit else "Ra"
                    cells[sign][key].append(label + retro)
                    ksign = (sign + 6) % 12
                    klabel = "KeT" if is_transit else "Ke"
                    cells[ksign][key].append(klabel + retro)
                
                # ఇప్పుడు Asc కూడా 'short' లో ఉంది కాబట్టి, ఇది ఈ కింది కండిషన్ లోకి వస్తుంది
                elif p in short:
                    if p == "Asc":
                        label = "AscT" if is_transit else "Asc"
                    else:
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


if __name__ == "__main__":
    root = ctk.CTk()  # CTk మెయిన్ విండో
    app = AstroApp(root)
    root.mainloop()