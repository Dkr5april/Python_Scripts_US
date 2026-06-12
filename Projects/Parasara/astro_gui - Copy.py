import tkinter as tk
from tkinter import ttk, messagebox
from geopy.geocoders import Nominatim

class AstroApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Astro Engine V23 - Research Portal")
        self.root.geometry("1100x750")
        
        # Initialize Geocoder
        self.geolocator = Nominatim(user_agent="astro_engine_v23")

        # 1. TOP PANEL: Input Portal
        self.input_frame = ttk.LabelFrame(root, text="Chart Entry Portal")
        self.input_frame.pack(fill="x", padx=10, pady=5)
        
        ttk.Label(self.input_frame, text="Name:").grid(row=0, column=0)
        self.ent_name = ttk.Entry(self.input_frame)
        self.ent_name.grid(row=0, column=1)

        ttk.Label(self.input_frame, text="DOB (DD/MM/YYYY):").grid(row=0, column=2)
        self.ent_dob = ttk.Entry(self.input_frame)
        self.ent_dob.grid(row=0, column=3)
        
        ttk.Label(self.input_frame, text="Time (HH:MM:SS):").grid(row=0, column=4)
        self.ent_tob = ttk.Entry(self.input_frame)
        self.ent_tob.grid(row=0, column=5)

        ttk.Label(self.input_frame, text="City:").grid(row=1, column=0)
        self.ent_city = ttk.Entry(self.input_frame)
        self.ent_city.grid(row=1, column=1)

        ttk.Button(self.input_frame, text="Generate Chart", command=self.generate_chart).grid(row=1, column=5, padx=10)

        # 2. SIDE PANEL: Dynamic Settings
        self.settings_frame = ttk.LabelFrame(root, text="Live Research Settings")
        self.settings_frame.pack(side="left", fill="y", padx=10, pady=5)

        self.ayanamsha = tk.StringVar(value="LAHIRI")
        ttk.Label(self.settings_frame, text="Ayanamsha:").pack(anchor="w")
        ttk.OptionMenu(self.settings_frame, self.ayanamsha, "LAHIRI", "LAHIRI", "RAMAN", "KP").pack(anchor="w")

        self.house_sys = tk.BooleanVar(value=True)
        ttk.Checkbutton(self.settings_frame, text="Sripati Padhathi", variable=self.house_sys).pack(anchor="w")

        # 3. MAIN CANVAS: Visualization Area
        self.canvas = tk.Canvas(root, bg="white")
        self.canvas.pack(side="right", expand=True, fill="both")

    def generate_chart(self):
        # Fetching coordinates
        city = self.ent_city.get()
        location = self.geolocator.geocode(city)
        
        if not location:
            messagebox.showerror("Error", "Could not find location coordinates!")
            return

        # Success: We have coordinates now
        lat, lon = location.latitude, location.longitude
        print(f"Generating for {self.ent_name.get()}")
        print(f"Location: {city} ({lat}, {lon})")
        print(f"Settings: {self.ayanamsha.get()} | Sripati: {self.house_sys.get()}")
        
        # Next: Here we will link to the calculation engine to draw the chart.

root = tk.Tk()
app = AstroApp(root)
root.mainloop()