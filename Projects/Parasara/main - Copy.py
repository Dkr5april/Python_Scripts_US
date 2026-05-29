from dignity_engine import PlanetaryDignity
from functional_engine import FunctionalClassifier
from house_logic_engine import HouseLogic
from report_ui import AstrologyReportUI # కొత్త UI ఫైల్

def run_analysis(lagna, planet, house, sun_pos, moon_pos, conjunctions):
    # 1. అనాలసిస్ లాజిక్
    dignity = PlanetaryDignity().get_dignity(planet, house)
    nature = FunctionalClassifier().get_planet_nature(planet, sun_pos, moon_pos, conjunctions)
    yoga = HouseLogic(lagna).analyze_yoga(planet, nature, house)
    
    # 2. రిపోర్ట్ ఫార్మాటింగ్ (UI కోసం)
    report_text = (
        f"--- జాతక విశ్లేషణ: {planet} ---\n\n"
        f"స్థితి: {dignity}\n"
        f"స్వభావం: {nature}\n\n"
        f"ఫలితం: {yoga}"
    )
    
    # 3. UI ని పిలవడం
    AstrologyReportUI(report_text)

if __name__ == "__main__":
    run_analysis("Simha", "Saturn", 5, 10, 190, [])