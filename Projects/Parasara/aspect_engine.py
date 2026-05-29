class AspectEngine:
    def get_aspects(self, planet, house):
        aspects = []
        
        # Helper function to calculate house properly
        def get_house(add):
            res = (house + add) % 12
            return 12 if res == 0 else res

        # 1. అన్ని గ్రహాలకు 7వ దృష్టి (house + 6)
        aspects.append(get_house(6))
        
        # 2. ప్రత్యేక దృష్టి గల గ్రహాలు
        if planet == "Saturn":
            aspects.extend([get_house(2), get_house(9)]) # 3rd and 10th
        elif planet == "Jupiter":
            aspects.extend([get_house(4), get_house(8)]) # 5th and 9th
        elif planet == "Mars":
            aspects.extend([get_house(3), get_house(7)]) # 4th and 8th
            
        return sorted(list(set(aspects))) # set వాడితే డూప్లికేట్స్ రావు