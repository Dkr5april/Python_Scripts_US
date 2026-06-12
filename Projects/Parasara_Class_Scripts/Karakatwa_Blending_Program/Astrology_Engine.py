import json
import time
from googlesearch import search

# Load your Data
with open('Astrology_data_corrected.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

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
    selected_planet = get_selection(planets, "Planet") # Keep it simple for now
    event = input("\nEnter event/topic (optional): ").strip()

    # Get the list of significations for each
    rasi_sigs = data['rasi_karakatwas'][selected_rasi]['significations']
    bhava_sigs = data['bhava_karakatwas'][selected_bhava]['significations']
    planet_sigs = data['graha_karakatwas'][selected_planet]['significations']

    # Combine them for the search loop
    # We will search one signification from each dimension to build the "story"
    print(f"\n--- Starting Multi-Dimensional Analysis ---")
    
    # We will loop through the first 3 items of each to keep it manageable and fast
    for i in range(3): 
        # Clean the strings (remove the Telugu text in brackets)
        r_term = rasi_sigs[i].split('(')[0].strip()
        b_term = bhava_sigs[i].split('(')[0].strip()
        p_term = planet_sigs[i].split('(')[0].strip()

        # Construct specific query
        query = f"Vedic astrology: {p_term} in {selected_bhava} {selected_rasi} rasi {r_term} {b_term}"
        if event:
            query += f" impact on {event}"
            
        print(f"\n[Analysis {i+1}]: {query}")
        try:
            # Get just 1 top result for each specific query
            results = list(search(query, num_results=1))
            if results:
                print(f"Result: {results[0]}")
            else:
                print("No deep analysis found for this specific combination.")
        except Exception as e:
            print(f"Search skipped (Network issue): {e}")
        
        time.sleep(2) # Mandatory delay to avoid being blocked by Google

if __name__ == "__main__":
    while True:
        run_engine()
        if input("\nRun another? (y/n): ").lower() != 'y': break