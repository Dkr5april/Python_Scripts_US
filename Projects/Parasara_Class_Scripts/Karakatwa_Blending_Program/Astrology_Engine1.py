import json
import time
from googlesearch import search

# Load your Data
with open('Astrology_data_corrected.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

def get_clean_term(term):
    # This keeps only the first core concept before the comma or parenthesis
    return term.split(',')[0].split('(')[0].strip()

def get_selection(options, prompt):
    print(f"\nSelect {prompt} (Enter number):")
    for i, opt in enumerate(options, 1): print(f"{i}. {opt}")
    choice = input(">> ").strip()
    return options[int(choice) - 1] if choice.isdigit() else None

def run_engine():
    # Load Menus
    rasis = list(data['rasi_karakatwas'].keys())
    bhavas = list(data['bhava_karakatwas'].keys())
    planets = list(data['graha_karakatwas'].keys())

    # Get Inputs
    selected_rasi = get_selection(rasis, "Rasi")
    selected_bhava = get_selection(bhavas, "Bhava")
    selected_planet = get_selection(planets, "Planet")
    event = input("\nEnter event/topic (optional): ").strip()

    # Get the lists
    rasi_sigs = data['rasi_karakatwas'][selected_rasi]['significations']
    bhava_sigs = data['bhava_karakatwas'][selected_bhava]['significations']
    planet_sigs = data['graha_karakatwas'][selected_planet]['significations']

    # Combine them for the search loop
    print(f"\n--- Starting Deep Analysis ---")
    
    # We loop through the first 5 significations (to get variety without getting blocked)
    for i in range(min(5, len(rasi_sigs))): 
        # Clean the terms
        r_term = get_clean_term(rasi_sigs[i])
        b_term = get_clean_term(bhava_sigs[i])
        p_term = get_clean_term(planet_sigs[i])

        # Construct specific, short, clean query
        query = f"Vedic astrology meaning of {p_term} in {selected_bhava} {selected_rasi} {r_term} {b_term}"
        if event:
            query += f" for {event}"
            
        print(f"\n[Analysis {i+1}]: {query}")
        
        # Search and print
        try:
            results = list(search(query, num_results=1))
            if results:
                print(f"Result: {results[0]}")
            else:
                print("No deep analysis found for this specific combination.")
        except Exception as e:
            print(f"Search skipped (Network issue): {e}")
        
        time.sleep(2) # Keep this delay to avoid getting blocked by Google

if __name__ == "__main__":
    while True:
        run_engine()
        if input("\nRun another? (y/n): ").lower() != 'y': break