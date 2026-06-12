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
        self.title("Vedic Astrology Engine - Full Edition")
        self.geometry("1200x800")
        
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=3)

        self.data = self.load_data()

        # --- LEFT PANEL (Control Panel) ---
        self.left_frame = ctk.CTkScrollableFrame(self, label_text="Control Panel")
        self.left_frame.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)

        # --- RIGHT PANEL ---
        self.right_frame = ctk.CTkFrame(self)
        self.right_frame.grid(row=0, column=1, sticky="nsew", padx=10, pady=10)
        
        self.textbox = ctk.CTkTextbox(self.right_frame, font=("Arial", 13))
        self.textbox.pack(fill="both", expand=True, padx=5, pady=5)

        # Language Selection
        self.lang_switch = ctk.CTkSegmentedButton(self.left_frame, values=["English", "Telugu"])
        self.lang_switch.set("English")
        self.lang_switch.pack(pady=10)

        self.vars = {}
        categories = ["rasi_karakatwas", "bhava_karakatwas", "graha_karakatwas", "nakshatra_karakatwas"]
        if self.data:
            for category in categories:
                if category in self.data: self.create_section(category)

        self.btn = ctk.CTkButton(self.left_frame, text="EXECUTE", command=self.show_full_data, fg_color="green", font=("Arial", 14, "bold"))
        self.btn.pack(pady=20, padx=10)

    def load_data(self):
        json_path = get_resource_path('Astrology_data_updated1.json')
        try:
            with open(json_path, 'r', encoding='utf-8') as f: return json.load(f)
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
            # 1. ఒకే స్ట్రింగ్‌లో ఉన్న కామాతో వేరు చేయబడిన భాగాలను విడదీయండి
            parts = text.split(',')
            telugu_parts = []
            
            for part in parts:
                # ప్రతి భాగంలో బ్రాకెట్ లోపల ఉన్న తెలుగును వెతకండి
                match = re.search(r'\((.*?)\)', part)
                if match:
                    telugu_parts.append(match.group(1).strip())
                else:
                    # ఒకవేళ బ్రాకెట్ లేకపోతే, ఆ భాగంలో ఉన్న తెలుగు అక్షరాలను మాత్రమే తీసుకోండి
                    telugu_pattern = re.compile(r'[\u0C00-\u0C7F]+')
                    t = "".join(telugu_pattern.findall(part))
                    if t: telugu_parts.append(t.strip())
            
            # అన్ని తెలుగు పదాలను కామాతో కలిపి తిరిగి పంపండి
            return ", ".join(telugu_parts)
            
        return re.sub(r'\s*\(.*?\)', '', text).strip()

    def show_full_data(self):
        self.textbox.delete("0.0", "end")
        lang = self.lang_switch.get()
        
        for cat, items in self.vars.items():
            for item, var in items.items():
                if var.get():
                    self.textbox.insert("end", f"\n{'*'*50}\n>>> {item.upper()} <<<\n{'*'*50}\n\n")
                    data_obj = self.data[cat][item]
                    
                    for k, v in data_obj.items():
                        # KEY కి extract_lang వాడవద్దు! నేరుగా ప్రింట్ చేయండి
                        display_key = k.upper().replace("_", " ")
                        self.textbox.insert("end", f"{display_key}:\n")
                        
                        # వాల్యూస్ కి మాత్రమే extract_lang వాడండి
                        if isinstance(v, dict):
                            for dk, dv in v.items():
                                self.textbox.insert("end", f"  • {dk.upper()}: {self.extract_lang(dv, lang)}\n")
                        elif isinstance(v, list):
                            for val in v:
                                self.textbox.insert("end", f"  • {self.extract_lang(val, lang)}\n")
                        else:
                            val_text = self.extract_lang(v, lang)
                            self.textbox.insert("end", f"  {val_text}\n")
                        
                      

if __name__ == "__main__":
    app = AstrologyApp()
    app.mainloop()