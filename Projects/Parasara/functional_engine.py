class FunctionalClassifier:
    def get_planet_nature(self, planet, sun_pos=0, moon_pos=0, conjunctions=[]):
        # 1. చంద్రుని పక్ష బలం
        if planet == "Moon":
            diff = (moon_pos - sun_pos) % 360
            return "Benefic" if (90 <= diff <= 270) else "Malefic"
        
        # 2. బుధుని కంజంక్షన్ రూల్
        if planet == "Mercury":
            malefics = ["Saturn", "Mars", "Rahu", "Ketu", "Sun"]
            return "Malefic" if any(p in malefics for p in conjunctions) else "Benefic"

        # 3. నైసర్గిక స్వభావం (Static)
        base = {"Jupiter": "Benefic", "Venus": "Benefic", "Saturn": "Malefic", 
                "Mars": "Malefic", "Sun": "Malefic", "Rahu": "Malefic", "Ketu": "Malefic"}
        return base.get(planet, "Neutral")