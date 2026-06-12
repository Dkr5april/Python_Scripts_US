import customtkinter as ctk
import json
import re
import os
import sys

# డేటా పాత్ సెటప్
def get_resource_path(relative_path):
    try: base_path = sys._MEIPASS
    except Exception: base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

class AstrologyApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Vedic Astrology Engine")
        self.geometry("1200x800")
        
        # Grid Configuration (ముఖ్యమైనది: విండో నిలువుగా సాగడానికి)
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=3)

        self.data = self.load_data()

        # --- LEFT PANEL (Control Panel) ---
        self.left_frame = ctk.CTkScrollableFrame(self, label_text="Control Panel")
        self.left_frame.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)

        # Language & Exit Section
        self.top_controls = ctk.CTkFrame(self.left_frame, fg_color="transparent")
        self.top_controls.pack(fill="x", pady=5)
        
        ctk.CTkLabel(self.top_controls, text="Language:", font=("Arial", 12, "bold")).pack()
        self.lang_switch = ctk.CTkSegmentedButton(self.top_controls, values=["English", "Telugu"])
        self.lang_switch.set("English")
        self.lang_switch.pack(pady=5)

        self.exit_btn = ctk.CTkButton(self.top_controls, text="EXIT", command=self.destroy, fg_color="red", font=("Arial", 12, "bold"))
        self.exit_btn.pack(pady=10)

        self.vars = {}
        if self.data:
            for category in ["rasi_karakatwas", "bhava_karakatwas", "graha_karakatwas"]:
                if category in self.data: self.create_section(category)

        self.btn = ctk.CTkButton(self.left_frame, text="EXECUTE", command=self.show_full_data, fg_color="green", font=("Arial", 14, "bold"))
        self.btn.pack(pady=20, padx=10)

        # --- RIGHT PANEL (Output Area) ---
        self.right_frame = ctk.CTkFrame(self)
        self.right_frame.grid(row=0, column=1, sticky="nsew", padx=10, pady=10)
        
        self.textbox = ctk.CTkTextbox(self.right_frame, font=("Arial", 13))
        self.textbox.pack(fill="both", expand=True, padx=5, pady=5)

    def load_data(self):
        json_path = get_resource_path('Astrology_data_corrected.json')
        try:
            with open(json_path, 'r', encoding='utf-8-sig') as f: return json.load(f)
        except: return None

    def create_section(self, category):
        self.vars[category] = {}
        ctk.CTkLabel(self.left_frame, text=category.upper().replace("_", " "), font=("Arial", 11, "bold")).pack(anchor="w", pady=(10, 0), padx=10)
        for item in self.data[category].keys():
            var = ctk.BooleanVar()
            cb = ctk.CTkCheckBox(self.left_frame, text=item, variable=var)
            cb.pack(anchor="w", padx=20, pady=2)
            self.vars[category][item] = var

    def extract_lang(self, text, lang):
        text = str(text)
        if lang == "Telugu":
            match = re.search(r'\((.*?)\)', text)
            return match.group(1) if match else text
        return re.sub(r'\s*\(.*?\)', '', text).strip()

    def show_full_data(self):
        self.textbox.delete("0.0", "end")
        lang = self.lang_switch.get()
        for cat, items in self.vars.items():
            for item, var in items.items():
                if var.get():
                    self.textbox.insert("end", f"\n{'*'*50}\n>>> {item.upper()} <<<\n{'*'*50}\n\n")
                    for k, v in self.data[cat][item].items():
                        self.textbox.insert("end", f"{k.replace('_', ' ').upper()}:\n")
                        if isinstance(v, list):
                            for val in v: self.textbox.insert("end", f"  • {self.extract_lang(val, lang)}\n")
                        else: self.textbox.insert("end", f"  {self.extract_lang(v, lang)}\n")
                        self.textbox.insert("end", "\n")

app = AstrologyApp()
app.mainloop()