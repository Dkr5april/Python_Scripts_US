class PlanetaryDignity:
    def __init__(self):
        # ఉచ్చ (Exaltation) మరియు నీచ (Debilitation) రాశులు
        self.exaltation = {
            "Sun": "Aries", "Moon": "Taurus", "Mars": "Capricorn",
            "Mercury": "Virgo", "Jupiter": "Cancer", "Venus": "Pisces", "Saturn": "Libra"
        }
        
    def get_dignity(self, planet, sign):
        # 1. ఉచ్చ స్థితి చెక్
        if self.exaltation.get(planet) == sign:
            return "Uchha (Exaltation)"
        
        # 2. నీచ స్థితి చెక్ (ఉచ్చ రాశికి 7వ రాశి)
        # సాధారణ లాజిక్ కోసం ఇలా ఇస్తున్నాను
        debilitated_signs = {
            "Sun": "Libra", "Moon": "Scorpio", "Mars": "Cancer",
            "Mercury": "Pisces", "Jupiter": "Capricorn", "Venus": "Virgo", "Saturn": "Aries"
        }
        if debilitated_signs.get(planet) == sign:
            return "Neecha (Debilitation)"
        
        return "Normal/Neutral"

# టెస్టింగ్ కోసం:
dignity_engine = PlanetaryDignity()
planet = "Jupiter"
sign = "Capricorn"
result = dignity_engine.get_dignity(planet, sign)
print(f"{planet} in {sign} is: {result}")