class InputEngine:
    def __init__(self, app_instance):
        self.app = app_instance
        self.current_mode = "day"

    def bind_inputs(self):
        # మౌస్ క్లిక్ బైండింగ్స్
        self.app.t_dob.bind("<Button-1>", lambda e: self.set_mode("day"))
        self.app.t_dob.bind("<Button-1>", lambda e: self.set_mode("month"))
        self.app.t_dob.bind("<Button-1>", lambda e: self.set_mode("year"))
        self.app.t_tob.bind("<Button-1>", lambda e: self.set_mode("hour"))
        self.app.t_dob.bind("<Button-1>", lambda e: self.set_mode("minute"))
        
        # కీబోర్డ్ బైండింగ్స్
        self.app.root.bind_all("<Up>", lambda e: self.app.adjust_transit(1))
        self.app.root.bind_all("<Down>", lambda e: self.app.adjust_transit(-1))
        self.app.root.bind_all("<Tab>", self.cycle_mode)
        self.app.root.bind_all("<Shift-Tab>", self.cycle_mode_reverse)

    def set_mode(self, mode):
        self.current_mode = mode
        self.app.root.title(f"Astro Engine V28 - [Mode: {mode.upper()}]")
        # ఆటోమేటిక్ గా ఏ బాక్సులో మార్పులు చేస్తున్నామో దాన్ని హైలైట్ చేయడం
        self.app.t_dob.config(bg="white")
        self.app.t_tob.config(bg="white")
        if mode in ["day", "month", "year"]:
            self.app.t_dob.config(bg="lightyellow") # డేట్ బాక్స్ హైలైట్
        elif mode in ["hour", "minute"]:
            self.app.t_tob.config(bg="lightyellow") # టైమ్ బాక్స్ హైలైట్
        

    def cycle_mode(self, e):
        modes = ["minute", "hour", "day", "month", "year"]
        idx = (modes.index(self.current_mode) + 1) % len(modes)
        self.current_mode = modes[idx]
        self.set_mode(modes[idx])
        self.app.root.focus_set() # కీ ప్రెస్ అయ్యాక ఫోకస్ ని విండోకి మార్చండి
        return "break"
        
    def cycle_mode_reverse(self, e):
        modes = ["minute", "hour", "day", "month", "year"]
        # మైనస్ 1 అంటే ఇండెక్స్ వెనక్కి వెళ్తుంది
        idx = (modes.index(self.current_mode) - 1) % len(modes)
        self.current_mode = modes[idx]
        self.set_mode(modes[idx])
        self.app.root.focus_set() # కీ ప్రెస్ అయ్యాక ఫోకస్ ని విండోకి మార్చండి
        return "break" # ఇది కూడా వెనక్కి వెళ్ళకుండా అడ్డుకుంటుంది
        