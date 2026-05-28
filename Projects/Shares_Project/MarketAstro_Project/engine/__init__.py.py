from datetime import datetime, timedelta

# Traditional Vimshottari years (Total 120 years)
VIM_YEARS = {
    "Ke": 7, "Ve": 20, "Su": 6, "Mo": 10, "Ma": 7, 
    "Ra": 18, "Ju": 16, "Sa": 19, "Me": 17
}
TOTAL_VIM_YEARS = 120
MARKET_DURATION_MINUTES = 358 # 9:32 AM to 3:30 PM is ~358 minutes

def get_current_dasa(current_dt):
    """
    Calculates the current Market Dasa Lord based on a 6-hour 'lifetime'.
    """
    # 1. Define Market 'Birth' and 'Death'
    mkt_open = current_dt.replace(hour=9, minute=32, second=0, microsecond=0)
    mkt_close = current_dt.replace(hour=15, minute=30, second=0, microsecond=0)
    
    # 2. Check if market is currently open
    if current_dt < mkt_open:
        return "Pre-Market", 0
    if current_dt > mkt_close:
        return "Post-Market", 0
        
    # 3. Calculate elapsed minutes in this 'lifetime'
    elapsed = (current_dt - mkt_open).total_seconds() / 60
    
    # 4. Determine Dasa Lord by checking elapsed time against planet proportions
    # Order: Ke, Ve, Su, Mo, Ma, Ra, Ju, Sa, Me
    dasa_order = ["Ke", "Ve", "Su", "Mo", "Ma", "Ra", "Ju", "Sa", "Me"]
    current_threshold = 0
    
    for lord in dasa_order:
        # Proportion: (Planet Years / 120) * 358 minutes
        duration = (VIM_YEARS[lord] / TOTAL_VIM_YEARS) * MARKET_DURATION_MINUTES
        if current_threshold <= elapsed < (current_threshold + duration):
            mins_remaining = (current_threshold + duration) - elapsed
            return lord, round(mins_remaining, 2)
        current_threshold += duration
        
    return "Closed", 0