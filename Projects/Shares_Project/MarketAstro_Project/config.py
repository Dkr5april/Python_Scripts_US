# config.py

# --- User Location Settings ---
# You can change these whenever you move or change your focus
LATITUDE = 18.9298   # Default set to your preferred coordinate
LONGITUDE = 72.8335
TIMEZONE_OFFSET = 5.5 # e.g., +5.5 for IST, -7.0 for MST

# --- Market Timing Settings ---
MARKET_OPEN_HOUR = 9
MARKET_OPEN_MINUTE = 30
MARKET_CLOSE_HOUR = 15
MARKET_CLOSE_MINUTE = 30

# Calculate total lifetime of market day in minutes
TOTAL_LIFETIME_MINS = ((MARKET_CLOSE_HOUR * 60) + MARKET_CLOSE_MINUTE) - \
                     ((MARKET_OPEN_HOUR * 60) + MARKET_OPEN_MINUTE)