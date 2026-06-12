# house_logic.py

class HouseLogic:
    def __init__(self, lagna):
        self.lagna = lagna

    def analyze_yoga(self, planet, nature, house, rasi, rasi_lord):
        is_swa_kshetra = (planet == rasi_lord)
        
        # 'nature' ని బట్టి ఫలితం
        is_malefic = "Malefic" in nature
        
        if is_swa_kshetra:
            if is_malefic:
                return f"{planet} {house}వ ఇంట్లో స్వక్షేత్రంలో ఉన్నాడు. ఫలితం: కఠినమైన క్రమశిక్షణ, శ్రమతో కూడిన విజయం."
            else:
                return f"{planet} {house}వ ఇంట్లో స్వక్షేత్రంలో ఉన్నాడు. ఫలితం: చాలా శుభప్రదం మరియు సానుకూలమైనది."
        else:
            return f"{planet} {house}వ ఇంట్లో {nature} ప్రభావంతో ఉన్నాడు (సాధారణ ఫలితం)."