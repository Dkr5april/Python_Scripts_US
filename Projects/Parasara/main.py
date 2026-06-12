from dignity_engine import PlanetaryDignity
from functional_engine import FunctionalClassifier
from house_logic_engine import HouseLogic
from lordship_engine import LordshipEngine
from aspect_engine import AspectEngine
from report_ui import AstrologyReportUI

def run_analysis(lagna, planet, house, rasi, degree, sun_pos, moon_pos, conjunctions):
    # 1. ఇంజిన్స్ ఇనిషియలైజేషన్
    lord = LordshipEngine().get_lord(rasi)
    aspects = AspectEngine().get_aspects(planet, house)
    
    # 2. అనాలసిస్ (ఇక్కడ dignity కి 'rasi' పంపుతున్నాం)
    dignity_engine = PlanetaryDignity()
    dignity = dignity_engine.get_dignity(planet, rasi, degree)
    relationship = dignity_engine.get_relationship(planet, lord) # కొత్తగా మైత్రి లాజిక్
    
    nature = FunctionalClassifier().get_planet_nature(planet, sun_pos, moon_pos, conjunctions)
    yoga = HouseLogic(lagna).analyze_yoga(planet, nature, house, rasi, lord)
    
    # 3. రిపోర్ట్ ఫార్మాటింగ్
    report_text = (
        f"--- జాతక విశ్లేషణ: {planet} ---\n\n"
        f"స్థానం: {house}వ ఇల్లు ({rasi} రాశి)\n"
        f"డిగ్రీ: {degree}°\n"
        f"రాశి అధిపతి: {lord}\n"
        f"రాశి సంబంధం: {relationship}\n" # మైత్రి వివరాలు
        f"దృష్టి ఉన్న ఇళ్లు: {aspects}\n"
        f"స్థితి: {dignity}\n"
        f"స్వభావం: {nature}\n\n"
        f"ఫలితం: {yoga}"
    )
    
    AstrologyReportUI(report_text)

if __name__ == "__main__":
    run_analysis("Simha", "Saturn", 7, "Kumbha", 10, 10, 190, [])