import tkinter as tk
from tkinter import font

class AppConfig:
    def __init__(self, root):
        self.root = root
        # విండో సైజ్ సెటప్
        self.root.geometry("800x600")
        self.root.title("Parasara Astrology Engine")
        
        # క్రాస్-ప్లాట్‌ఫాం ఫాంట్ సెటప్ (Windows/Mac/Linux ఎక్కడైనా పనిచేస్తుంది)
        self.default_font = ("Segoe UI", 12)
        self.heading_font = ("Segoe UI", 16, "bold")
        
    def apply_fonts(self, widget):
        # అన్ని విడ్జెట్స్‌కు ఫాంట్ అప్లై చేసే ఫంక్షన్
        try:
            widget.configure(font=self.default_font)
        except:
            pass

# యూసేజ్:
# root = tk.Tk()
# config = AppConfig(root)