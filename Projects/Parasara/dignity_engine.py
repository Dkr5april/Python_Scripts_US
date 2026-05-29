class PlanetaryDignity:
    def __init__(self):
        self.exaltation = {
            "Sun": "Aries", "Moon": "Taurus", "Mars": "Capricorn",
            "Mercury": "Virgo", "Jupiter": "Cancer", "Venus": "Pisces", "Saturn": "Libra"
        }
        self.debilitated_signs = {
            "Sun": "Libra", "Moon": "Scorpio", "Mars": "Cancer",
            "Mercury": "Pisces", "Jupiter": "Capricorn", "Venus": "Virgo", "Saturn": "Aries"
        }
        # గ్రహ మైత్రి (Natural Friendships)
        self.friends = {
            "Sun": ["Moon", "Mars", "Jupiter"],
            "Saturn": ["Mercury", "Venus"],
            "Jupiter": ["Sun", "Moon", "Mars"],
            # ఇలా అన్ని గ్రహాలకు పూర్తి చేయవచ్చు
        }

    def get_dignity(self, planet, sign):
        if self.exaltation.get(planet) == sign:
            return "Uchha (Exaltation)"
        if self.debilitated_signs.get(planet) == sign:
            return "Neecha (Debilitation)"
        return "Normal/Neutral"

    def get_relationship(self, planet, sign_lord):
        """గ్రహం మరియు రాశి అధిపతి మధ్య సంబంధం"""
        if planet == sign_lord:
            return "Swa-Kshetra (Own House)"
        if sign_lord in self.friends.get(planet, []):
            return "Mitra (Friend)"
        return "Sama/Satru (Neutral/Enemy)"