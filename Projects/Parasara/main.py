from dignity_engine import PlanetaryDignity
from functional_engine import FunctionalClassifier
from house_logic_engine import HouseLogic
from lordship_engine import LordshipEngine
from aspect_engine import AspectEngine  # కొత్తగా యాడ్ చేశాం
from report_ui import AstrologyReportUI

def run_analysis(lagna, planet, house, rasi, sun_pos, moon_pos, conjunctions):
    # 1. ఇంజిన్స్ ఇనిషియలైజేషన్
    lord = LordshipEngine().get_lord(rasi)
    aspects = AspectEngine().get_aspects(planet, house) # దృష్టిని లెక్కించడం
    
    # 2. అనాలసిస్
    dignity = PlanetaryDignity().get_dignity(planet, house)
    nature = FunctionalClassifier().get_planet_nature(planet, sun_pos, moon_pos, conjunctions)
    yoga = HouseLogic(lagna).analyze_yoga(planet, nature, house, rasi, lord)
    
    # 3. రిపోర్ట్ ఫార్మాటింగ్
    report_text = (
        f"--- జాతక విశ్లేషణ: {planet} ---\n\n"
        f"స్థానం: {house}వ ఇల్లు\n"
        f"రాశి అధిపతి: {lord}\n"
        f"దృష్టి ఉన్న ఇళ్లు: {aspects}\n" # దృష్టి వివరాలు
        f"స్థితి: {dignity}\n"
        f"స్వభావం: {nature}\n\n"
        f"ఫలితం: {yoga}"
    )
    
    AstrologyReportUI(report_text)

if __name__ == "__main__":
    # ఉదాహరణకు శనిని విశ్లేషిస్తున్నాం
    run_analysis("Simha", "Saturn", 5, "Makara", 10, 190, [])