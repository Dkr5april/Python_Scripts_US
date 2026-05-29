import platform

class AppConfig:
    def __init__(self):
        # ప్లాట్‌ఫామ్ బట్టి ఫాంట్ సెట్ చేయడం (System font issues రావు)
        self.os_type = platform.system()
        self.font_family = "Segoe UI" if self.os_type == "Windows" else "Helvetica"
        
        # ఫాంట్ స్టైల్స్
        self.default_font = (self.font_family, 12)
        self.bold_font = (self.font_family, 12, "bold")
        self.heading_font = (self.font_family, 16, "bold")

    def get_font(self, style="default"):
        styles = {
            "default": self.default_font,
            "bold": self.bold_font,
            "heading": self.heading_font
        }
        return styles.get(style, self.default_font)

    # విండో సెట్టింగ్స్ కోసం కూడా ఇక్కడ మెథడ్స్ రాసుకోవచ్చు
    @staticmethod
    def get_window_settings():
        return {"size": "800x600", "title": "Parasara Astrology Engine"}