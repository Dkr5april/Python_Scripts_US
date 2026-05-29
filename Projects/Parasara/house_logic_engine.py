class HouseLogic:
    def __init__(self, lagna):
        self.lagna = lagna
        self.kendra_houses = [1, 4, 7, 10]
        self.kona_houses = [1, 5, 9]

    def analyze_yoga(self, planet, nature, house):
        # కేంద్రంలో శుభ గ్రహం
        if nature == "Benefic" and house in self.kendra_houses:
            return f"{planet} కేంద్రస్థిత యోగం (స్థిరత్వం)."
        # కోణంలో పాప గ్రహం
        if nature == "Malefic" and house in self.kona_houses:
            return f"{planet} కోణస్థిత యోగం (క్రమశిక్షణ/తపస్సు)."
        return "సాధారణ ఫలితం."