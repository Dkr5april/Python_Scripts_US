class LordshipEngine:
    def __init__(self):
        # రాశి పేర్లు మరియు వాటి అధిపతులు - అన్ని ఇంగ్లీష్‌లోనే
        self.lords = {
            "Aries": "Mars", "Taurus": "Venus", "Gemini": "Mercury",
            "Cancer": "Moon", "Leo": "Sun", "Virgo": "Mercury",
            "Libra": "Venus", "Scorpio": "Mars", "Sagittarius": "Jupiter",
            "Capricorn": "Saturn", "Aquarius": "Saturn", "Pisces": "Jupiter"
        }

    def get_lord(self, rasi):
        return self.lords.get(rasi, "Unknown")