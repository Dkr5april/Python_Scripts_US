import json
import time
from googlesearch import search

# 1. Load your Data
with open('Astrology_data_corrected.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

def get_clean_term(term):
    """Cleans strings to extract only the primary keyword."""
    return term.split('(')[0].split(',')[0].strip()

def get_selection(options, prompt):
    print(f"\nSelect {prompt} (Enter number):")
    for i, opt in enumerate(options, 1): print(f"{i}. {opt}")
    choice = input(">> ").strip()
    if choice.isdigit() and 1 <= int(choice) <= len(options):
        return options[int(choice) - 1]
    return None

def run_engine():
    # Load Menus from JSON keys
    rasis = list(data['rasi_karakatwas'].keys())
    bhavas = list(data['bhava_karakatwas'].keys())
    planets = list(data['graha_karakatwas'].keys())

    # Get User Inputs
    selected_rasi = get_selection(rasis, "Rasi")
    selected_bhava = get_selection(bhavas, "Bhava")
    selected_planet = get_selection(planets, "Planet")
    
    if not (selected_rasi and selected_bhava and selected_planet):
        print("Invalid selection. Please restart.")
        return

    event = input("\nEnter event/topic (optional, press Enter to skip): ").strip()

    # Retrieve significations
    rasi_sigs = data['rasi_karakatwas'][selected_rasi]['significations']
    bhava_sigs = data['bhava_karakatwas'][selected_bhava]['significations']
    planet_sigs = data['graha_karakatwas'][selected_planet]['significations']

    print(f"\n--- Starting Multi-Dimensional Analysis ---")
    print(f"Analyzing: {selected_planet} in {selected_bhava} ({selected_rasi})")
    
    # Iterate through the first 5 significations of each to build a 'blended' report
    for i in range(min(5, len(planet_sigs))): 
        p_term = get_clean_term(planet_sigs[i])
        r_term = get_clean_term(rasi_sigs[i])
        b_term = get_clean_term(bhava_sigs[i])

        # Construct specific, optimized query
        # క్వెరీని సులభతరం చేయడం (Simpler query structure)
        # అనవసరమైన పదాలను తొలగించి, కేవలం ముఖ్యమైన అంశాలను మాత్రమే ఉంచడం
        query = f"Vedic astrology: {p_term} in {selected_bhava} {selected_rasi}"
        
        if event:
            query += f" impact on {event}"
            
        print(f"\n[Analysis {i+1}]: {query}")
        
        try:
            # Perform Search
            results = list(search(query, num_results=1))
            if results:
                print(f"Result: {results[0]}")
            else:
                print("No deep analysis found for this specific combination.")
        except Exception as e:
            print(f"Search failed (Check internet connection): {e}")
        
        # Polite delay to prevent Google from blocking your IP
        time.sleep(3) 

if __name__ == "__main__":
    while True:
        run_engine()
        if input("\nRun another query? (y/n): ").lower() != 'y':
            break