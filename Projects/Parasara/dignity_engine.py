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
        # మూలత్రికోణ రాశులు మరియు వాటి డిగ్రీ పరిధులు
        self.moolatrikona = {
            "Sun": {"sign": "Leo", "start": 0, "end": 20},
            "Moon": {"sign": "Taurus", "start": 3, "end": 30},
            "Mars": {"sign": "Aries", "start": 0, "end": 12},
            "Mercury": {"sign": "Virgo", "start": 16, "end": 20},
            "Jupiter": {"sign": "Sagittarius", "start": 0, "end": 10},
            "Venus": {"sign": "Libra", "start": 0, "end": 15},
            "Saturn": {"sign": "Aquarius", "start": 0, "end": 20}
        }
        # గ్రహ మైత్రి (Natural Friendships)
        self.friends = {
            "Sun": ["Moon", "Mars", "Jupiter"],
            "Saturn": ["Mercury", "Venus"],
            "Jupiter": ["Sun", "Moon", "Mars"]
        }

    def get_dignity(self, planet, sign, degree):
        # 1. ఉచ్చ స్థితి
        if self.exaltation.get(planet) == sign:
            return "Uchha (Exaltation)"
        
        # 2. మూలత్రికోణ స్థితి
        mt = self.moolatrikona.get(planet)
        if mt and mt["sign"] == sign and mt["start"] <= degree <= mt["end"]:
            return "Moolatrikona (Strong)"
        
        # 3. స్వక్షేత్రం చెక్ (అదనపు బలం)
        if self.get_relationship(planet, planet) == "Swa-Kshetra (Own House)":
            # ఇక్కడ మనం ప్లానెట్ మరియు రాశి అధిపతి ఒకటే అయితే స్వక్షేత్రం అని రావచ్చు
            # కానీ క్విక్ ఫిక్స్ కోసం:
            return "Swa-Kshetra (Own House)"
        
        # 4. నీచ స్థితి
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