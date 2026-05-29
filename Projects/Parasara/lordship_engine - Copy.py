# lordship_engine.py

class LordshipEngine:
    def __init__(self):
        # 12 రాశులు మరియు వాటి అధిపతుల మ్యాపింగ్
        self.lordship_map = {
            "Mesha": "Mars", "Vrishabha": "Venus", "Mithuna": "Mercury",
            "Karka": "Moon", "Simha": "Sun", "Kanya": "Mercury",
            "Tula": "Venus", "Vrishchika": "Mars", "Dhanu": "Jupiter",
            "Makara": "Saturn", "Kumbha": "Saturn", "Meena": "Jupiter"
        }

    def get_lord(self, rasi):
        """ఇచ్చిన రాశికి అధిపతిని తిరిగి ఇస్తుంది."""
        return self.lordship_map.get(rasi, "Unknown")