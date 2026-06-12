# house_engine.py

class HouseEngine:
    NATURAL_NATURE = {
        "Sun": "Natural Malefic",
        "Moon": "Natural Benefic",
        "Mars": "Natural Malefic",
        "Mercury": "Natural Benefic",
        "Jupiter": "Natural Benefic",
        "Venus": "Natural Benefic",
        "Saturn": "Natural Malefic",
        "Rahu": "Natural Malefic",
        "Ketu": "Natural Malefic"
    }

    BENEFIC_MAP = {
        "Mesha": ["Jupiter", "Mars", "Sun"],
        "Vrishabha": ["Saturn", "Mercury", "Venus"],
        "Mithuna": ["Venus", "Mercury", "Saturn"],
        "Karka": ["Mars", "Jupiter", "Moon"],
        "Simha": ["Mars", "Sun", "Jupiter"],
        "Kanya": ["Venus", "Mercury", "Saturn"],
        "Tula": ["Saturn", "Mercury", "Venus"],
        "Vrishchika": ["Moon", "Jupiter", "Mars"],
        "Dhanu": ["Sun", "Mars", "Jupiter"],
        "Makara": ["Venus", "Mercury", "Saturn"],
        "Kumbha": ["Venus", "Mercury", "Saturn"],
        "Meena": ["Moon", "Mars", "Jupiter"]
    }

    def get_natural_nature(self, planet):
        return self.NATURAL_NATURE.get(planet, "Neutral")

    def get_functional_nature(self, lagna, planet):
        benefics = self.BENEFIC_MAP.get(lagna, [])
        return "Functional Benefic" if planet in benefics else "Functional Malefic"