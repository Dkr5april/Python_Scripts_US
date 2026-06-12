# rule_engine.py
from dignity_engine import PlanetaryDignity as DignityEngine
from house_engine import HouseEngine  # HouseEngine ఒక ఫైల్ లో ఉంది
from house_logic import HouseLogic    # HouseLogic వేరే ఫైల్ లో ఉంది

class RuleEngine:
    def __init__(self):
        self.dignity = DignityEngine()
        self.house_engine = HouseEngine()

    def analyze_planet(self, lagna, planet, sign, degree, house_num, rasi, rasi_lord):
        # 1. డేటాను సేకరించడం
        natural = self.house_engine.get_natural_nature(planet)
        functional = self.house_engine.get_functional_nature(lagna, planet)
        dignity_status = self.dignity.get_dignity(planet, sign, degree)
        
        # 2. యోగ విశ్లేషణ
        house_logic = HouseLogic(lagna)
        yoga_result = house_logic.analyze_yoga(planet, functional, house_num, rasi, rasi_lord)
        
        # 3. రిపోర్ట్ బిల్డింగ్
        analysis_report = []
        
        # రూల్ 4: Late Bloomer లాజిక్
        if "Debilitated" in dignity_status and functional == "Functional Benefic":
            analysis_report.append("Rule 4 (Late Bloomer): ప్రారంభంలో ఆటంకాలు ఉన్నా, 30-35 ఏళ్ళ తర్వాత గొప్ప ఫలితాలు వస్తాయి.")
        
        # రూల్: కోణ స్థానాలు (1, 5, 9)
        if house_num in [1, 5, 9]:
            analysis_report.append("Result: శుభ స్థితి - కోణ ప్రభావం వల్ల యోగకారక ఫలితాలు.")
    
        # రూల్: ఉపచయ స్థానాలు (3, 6, 10, 11)
        if house_num in [3, 6, 10, 11]:
            analysis_report.append("Result: వృద్ధి స్థానం - పోటీని తట్టుకునే శక్తి, కెరీర్ వృద్ధికి అవకాశం.")

        # రూల్: జీవ/నిర్జీవ (Dignity ని బట్టి)
        if "Debilitated" in dignity_status:
            analysis_report.append("గమనిక: బలహీన స్థితిలో ఉన్నందున, సంబంధాల విషయంలో జాగ్రత్త, కానీ వృత్తిపరంగా లాభం ఉండవచ్చు.")
            
        # రూల్: దుస్థానాల ప్రభావం (6, 8, 12)
        if house_num in [6, 8, 12]:
            analysis_report.append("గమనిక: దుస్థాన ప్రభావం - శ్రమ, అనారోగ్యం లేదా అకస్మాత్తు మార్పులు ఉండవచ్చు. 6వ భావం అయితే గొడవలు, 8వ భావం అయితే అడ్డంకులు, 12వ భావం అయితే ఖర్చులు సూచిస్తుంది.")
            
        # HouseLogic నుండి వచ్చిన రిజల్ట్
        analysis_report.append(f"యోగ విశ్లేషణ: {yoga_result}")
        
        # స్థితుల సారాంశం
        analysis_report.append(f"స్వభావం: {planet} ({natural}) మరియు ఈ లగ్నానికి {functional}.")
        analysis_report.append(f"స్థితి: గ్రహం {dignity_status} స్థితిలో ఉంది.")

        return f"--- {planet} విశ్లేషణ ---\n" + "\n".join(analysis_report)