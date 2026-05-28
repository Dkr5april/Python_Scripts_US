# engine/market_dasa.py

def get_market_dasa_levels(current_dt, moon_lon, moon_lord):
    # Standard Vimshottari years & Order
    V_YEARS = {"Ke": 7, "Ve": 20, "Su": 6, "Mo": 10, "Ma": 7, "Ra": 18, "Ju": 16, "Sa": 19, "Me": 17}
    BASE_ORDER = ["Ke", "Ve", "Su", "Mo", "Ma", "Ra", "Ju", "Sa", "Me"]
    
    # 1. Calculate Consumption of the Star
    star_span = 13.33333333
    passed_in_star = moon_lon % star_span
    consumption_ratio = passed_in_star / star_span  # e.g., 0.6 means 60% of the star is gone
    
    # 2. Align the Sequence
    start_idx = BASE_ORDER.index(moon_lord)
    sequence = BASE_ORDER[start_idx:] + BASE_ORDER[:start_idx]
    
    # 3. Calculate the "Global Start Time" offset
    # We find how many 'Market Minutes' have already passed in the Saturn Dasa
    # before the market even opened.
    first_lord_total_market_mins = V_YEARS[moon_lord] * 3
    market_offset_mins = consumption_ratio * first_lord_total_market_mins
    
    # 4. Current Market Elapsed Time
    m_start = current_dt.replace(hour=9, minute=30, second=0, microsecond=0)
    market_elapsed = (current_dt - m_start).total_seconds() / 60.0
    
    # Total Time for logic = Consumption Offset + Current Market Time
    total_effective_elapsed = market_offset_mins + market_elapsed

    # 5. Proportional Recursive Logic
    def find_lord_at_time(elapsed, total_cycle_dur, current_sequence):
        accumulated = 0
        for lord in current_sequence:
            dur = (V_YEARS[lord] / 120.0) * total_cycle_dur
            if accumulated <= elapsed < (accumulated + dur):
                return lord, accumulated, dur
            accumulated += dur
        return current_sequence[-1], accumulated - dur, dur

    # The "Total Cycle" for our mapping is 360 minutes
    # Level 1: Maha
    l1, l1_start, l1_dur = find_lord_at_time(total_effective_elapsed % 360, 360, sequence)
    
    # Level 2: Antar (relative to L1)
    l2_elapsed = total_effective_elapsed - l1_start
    l2, l2_start, l2_dur = find_lord_at_time(l2_elapsed % l1_dur, l1_dur, sequence)
    
    # Level 3: Pratyantar (relative to L2)
    l3_elapsed = l2_elapsed - l2_start
    l3, l3_start, l3_dur = find_lord_at_time(l3_elapsed % l2_dur, l2_dur, sequence)
    
    # Level 4: Sookshma
    l4_elapsed = l3_elapsed - l3_start
    l4, l4_start, l4_dur = find_lord_at_time(l4_elapsed % l3_dur, l3_dur, sequence)
    
    # Level 5: Prana
    l5_elapsed = l4_elapsed - l4_start
    l5, l5_start, l5_dur = find_lord_at_time(l5_elapsed % l4_dur, l4_dur, sequence)
    
    # Level 6: Deha
    l6, _, _ = find_lord_at_time((l5_elapsed - l5_start) % l5_dur, l5_dur, sequence)

    return [l1, l2, l3, l4, l5, l6]