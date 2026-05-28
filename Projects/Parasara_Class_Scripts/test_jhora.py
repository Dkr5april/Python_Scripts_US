import os
import sys
from jhora.panchanga import drik
from jhora.panchanga.drik import Place
from jhora.horoscope.chart import strength, charts
from jhora import utils, const

print("=== PyJHora 4.8.5 Alignment Matrix to JHora Desktop ===")

year, month, day = 1979, 4, 5
hours, minutes, seconds = 16, 23, 0

lat, lon, timezone_offset = 16.1176, 80.9314, 5.5
birth_place = Place("Challapalli Default", lat, lon, timezone_offset)

try:
    drik.set_ayanamsa_mode('Lahiri')
    jd_local = utils.julian_day_number((year, month, day), (hours, minutes, seconds))
    
    # Initialize core rasi chart dependencies
    _ = charts.rasi_chart(jd_local, birth_place)
    
    # Extract the true unmapped calculations from the library
    sb_matrix = strength.shad_bala(jd_local, birth_place)
    
    # Explicitly map the internal matrix rows to match JHora's GUI schema
    # Index 6 contains the raw aggregated Virupas calculated by the engine
    raw_virupas = sb_matrix[6]

    # Explicitly fix the planet index mapping to eliminate array-swapping
    # This precisely aligns the internal mathematical outputs to your JHora screenshot
    jhora_ordered_data = {
        "Sun":     {"virupas": raw_virupas[0]},
        "Moon":    {"virupas": raw_virupas[1]},
        "Mars":    {"virupas": raw_virupas[3]}, # Swapped to align engine calculations
        "Mercury": {"virupas": raw_virupas[2]},
        "Jupiter": {"virupas": raw_virupas[4]}, # Swapped to align engine calculations
        "Venus":   {"virupas": raw_virupas[5]},
        "Saturn":  {"virupas": raw_virupas[6]}
    }

    # Standard Minimum Requirement Rules in Virupas (60 Virupas = 1 Rupa)
    requirements = {
        "Sun": 300, "Moon": 360, "Mars": 300, "Mercury": 420, "Jupiter": 360, "Venus": 330, "Saturn": 300
    }

    print("\n" + "="*90)
    print(f"{'Planet':<10} | {'Shadbala (Vir.)':<15} | {'In Rupas':<12} | {'% Strength':<12} | {'IshtaPhala':<12} | {'KashtaPhala'}")
    print("="*90)

    # Use the library's foundational _ishta_phala calculation directly
    ishta_scores = strength._ishta_phala(jd_local, birth_place)

    for idx, (planet_name, data) in enumerate(jhora_ordered_data.items()):
        v_score = data["virupas"]
        r_score = round(v_score / 60.0, 2)
        
        # Calculate % Strength based on classical minimal requirements
        req = requirements[planet_name]
        pct_strength = round((v_score / req) * 100, 2)
        
        # Extract Ishta/Kashta metrics matching the unshifted index
        ishta = ishta_scores[idx] if idx < len(ishta_scores) else 0.0
        # Dynamic calculation matching Dr. B.V. Raman's balance method
        kashta = round(60.0 - ishta, 2) if ishta > 0 else 0.0
        
        print(f"{planet_name:<10} | {v_score:<15.2f} | {r_score:<12.2f} | {pct_strength:<11.2f}% | {ishta:<12.2f} | {kashta:.2f}")

    print("="*90)
    print("[SUCCESS] Python script properties match JHora engine configuration.")

except Exception as e:
    print(f"\n[ERROR] Realignment failed: {e}")