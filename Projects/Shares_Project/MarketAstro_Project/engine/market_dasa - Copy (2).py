# engine/market_dasa.py
from datetime import timedelta

def get_market_dasa_levels(current_dt):
    """
    Calculates a 6-level Dasa system mapped to a 360-minute market day.
    Levels: Maha > Antar > Pratyantar > Sookshma > Prana > Deha
    """
    LORDS = ["Ke", "Ve", "Su", "Mo", "Ma", "Ra", "Ju", "Sa", "Me"]
    
    # Market start configuration
    market_start = current_dt.replace(hour=9, minute=30, second=0, microsecond=0)
    elapsed_delta = current_dt - market_start
    total_seconds = elapsed_delta.total_seconds()
    
    # Total market duration is 21,600 seconds (360 minutes)
    market_duration_sec = 360 * 60 
    
    # Boundary constraints
    if total_seconds < 0: total_seconds = 0
    if total_seconds >= market_duration_sec: total_seconds = market_duration_sec - 1

    # Level Timing Logic (Dividing the 360m window into 9 parts recursively)
    # Level 1: ~40.0 minutes
    l1_idx = int((total_seconds / (market_duration_sec / 9)) % 9)
    
    # Level 2: ~4.44 minutes (266.6 seconds)
    l2_idx = int((total_seconds / (market_duration_sec / 81)) % 9)
    
    # Level 3: ~29.6 seconds
    l3_idx = int((total_seconds / (market_duration_sec / 729)) % 9)
    
    # Level 4: ~3.29 seconds
    l4_idx = int((total_seconds / (market_duration_sec / 6561)) % 9)
    
    # Level 5: ~0.36 seconds
    l5_idx = int((total_seconds / (market_duration_sec / 59049)) % 9)
    
    # Level 6: ~0.04 seconds (Deha level)
    l6_idx = int((total_seconds / (market_duration_sec / 531441)) % 9)

    return [
        LORDS[l1_idx], LORDS[l2_idx], LORDS[l3_idx], 
        LORDS[l4_idx], LORDS[l5_idx], LORDS[l6_idx]
    ]