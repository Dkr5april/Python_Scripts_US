class YogaKarakaEngine:
    def __init__(self):
        # House Lordship mapping for all 12 Lagnas
        # Format: {Lagna: {HouseNumber: Lord}}
        self.lagna_map = {
            "Aries": {1: "Mars", 2: "Venus", 3: "Mercury", 4: "Moon", 5: "Sun", 6: "Mercury", 7: "Venus", 8: "Mars", 9: "Jupiter", 10: "Saturn", 11: "Saturn", 12: "Jupiter"},
            "Taurus": {1: "Venus", 2: "Mercury", 3: "Moon", 4: "Sun", 5: "Mercury", 6: "Venus", 7: "Mars", 8: "Jupiter", 9: "Saturn", 10: "Saturn", 11: "Jupiter", 12: "Mars"},
            "Gemini": {1: "Mercury", 2: "Moon", 3: "Sun", 4: "Mercury", 5: "Venus", 6: "Mars", 7: "Jupiter", 8: "Saturn", 9: "Saturn", 10: "Jupiter", 11: "Mars", 12: "Venus"},
            "Cancer": {1: "Moon", 2: "Sun", 3: "Mercury", 4: "Venus", 5: "Mars", 6: "Jupiter", 7: "Saturn", 8: "Saturn", 9: "Jupiter", 10: "Mars", 11: "Venus", 12: "Mercury"},
            "Leo": {1: "Sun", 2: "Mercury", 3: "Venus", 4: "Mars", 5: "Jupiter", 6: "Saturn", 7: "Saturn", 8: "Jupiter", 9: "Mars", 10: "Venus", 11: "Mercury", 12: "Moon"},
            "Virgo": {1: "Mercury", 2: "Venus", 3: "Mars", 4: "Jupiter", 5: "Saturn", 6: "Saturn", 7: "Jupiter", 8: "Mars", 9: "Venus", 10: "Mercury", 11: "Moon", 12: "Sun"},
            "Libra": {1: "Venus", 2: "Mars", 3: "Jupiter", 4: "Saturn", 5: "Saturn", 6: "Jupiter", 7: "Mars", 8: "Venus", 9: "Mercury", 10: "Moon", 11: "Sun", 12: "Mercury"},
            "Scorpio": {1: "Mars", 2: "Jupiter", 3: "Saturn", 4: "Saturn", 5: "Jupiter", 6: "Mars", 7: "Venus", 8: "Mercury", 9: "Moon", 10: "Sun", 11: "Mercury", 12: "Venus"},
            "Sagittarius": {1: "Jupiter", 2: "Saturn", 3: "Saturn", 4: "Jupiter", 5: "Mars", 6: "Venus", 7: "Mercury", 8: "Moon", 9: "Sun", 10: "Mercury", 11: "Venus", 12: "Mars"},
            "Capricorn": {1: "Saturn", 2: "Saturn", 3: "Jupiter", 4: "Mars", 5: "Venus", 6: "Mercury", 7: "Moon", 8: "Sun", 9: "Mercury", 10: "Venus", 11: "Mars", 12: "Jupiter"},
            "Aquarius": {1: "Saturn", 2: "Jupiter", 3: "Mars", 4: "Venus", 5: "Mercury", 6: "Moon", 7: "Sun", 8: "Mercury", 9: "Venus", 10: "Mars", 11: "Jupiter", 12: "Saturn"},
            "Pisces": {1: "Jupiter", 2: "Mars", 3: "Venus", 4: "Mercury", 5: "Moon", 6: "Sun", 7: "Mercury", 8: "Venus", 9: "Mars", 10: "Jupiter", 11: "Saturn", 12: "Saturn"}
        }

    def get_status(self, lagna, planet):
        if lagna not in self.lagna_map:
            return "Lagna not defined"
        
        ruled_houses = [h for h, lord in self.lagna_map[lagna].items() if lord == planet]
        
        kendras = {1, 4, 7, 10}
        trikonas = {1, 5, 9}
        
        rules_kendra = any(h in kendras for h in ruled_houses)
        rules_trikona = any(h in trikonas for h in ruled_houses)
        
        # Classification logic based on Parashara rules
        if rules_kendra and rules_trikona:
            return "Yogakaraka (Strongest)"
        elif rules_kendra:
            return "Kendra Lord"
        elif rules_trikona:
            return "Trikona Lord"
        else:
            return "Neutral/Malefic"