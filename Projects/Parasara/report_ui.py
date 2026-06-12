from config import AppConfig

class AstrologyReportUI:
    def __init__(self, data):
        self.config = AppConfig()
        self.root = tk.Tk()
        self.root.title("Parasara Astrology Engine")
        self.root.geometry("400x300")
        
        # UI లో ఫాంట్ అప్లై చేయడం
        label = tk.Label(self.root, text=data, font=self.config.get_font("default"), justify="left")
        label.pack(pady=20, padx=20)
        
        self.root.mainloop()

# Usage:
# AstrologyReportUI("గ్రహం: Saturn\nస్థితి: నీచ\nఫలితం: యోగ కారకుడు")