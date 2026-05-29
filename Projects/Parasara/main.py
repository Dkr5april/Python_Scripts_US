from dignity_engine import PlanetaryDignity
from functional_engine import FunctionalClassifier
from house_logic_engine import HouseLogic
from lordship_engine import LordshipEngine # దీన్ని యాడ్ చేయండి
from report_ui import AstrologyReportUI

def run_analysis(lagna, planet, house, rasi, sun_pos, moon_pos, conjunctions):
    # 1. అధిపతిని కనుగొనడం
    lord = LordshipEngine().get_lord(rasi)
    
    # 2. అనాలసిస్
    dignity = PlanetaryDignity().get_dignity(planet, house)
    nature = FunctionalClassifier().get_planet_nature(planet, sun_pos, moon_pos, conjunctions)
    yoga = HouseLogic(lagna).analyze_yoga(planet, nature, house)
    
    # రిపోర్ట్ ఫార్మాటింగ్ - ఇక్కడ {house} ని యాడ్ చేశాను
    report_text = (
        f"--- జాతక విశ్లేషణ: {planet} ---\n\n"
        f"స్థానం: {house}వ ఇల్లు\n" # దీన్ని యాడ్ చేయండి
        f"రాశి అధిపతి: {lord}\n"
        f"స్థితి: {dignity}\n"
        f"స్వభావం: {nature}\n\n"
        f"ఫలితం: {yoga}"
    )
    
    AstrologyReportUI(report_text)

if __name__ == "__main__":
    # టెస్ట్ రన్ (ఇక్కడ 'Makara' అనే రాశిని జోడించాం)
    run_analysis("Simha", "Saturn", 5, "Makara", 10, 190, [])