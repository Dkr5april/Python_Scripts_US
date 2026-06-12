# truth_database.py

EXPECTED_DATA = {
    "Aries": {
        "Sun": {"dignity": "Exalted", "relationship": "Mithra", "yoga": "Trikona Lord"},
        "Moon": {"dignity": "Neutral", "relationship": "Mithra", "yoga": "Kendra Lord"},
        "Mars": {"dignity": "Swa-Kshetra", "relationship": "Mithra", "yoga": "Kendra Lord"},
        "Mercury": {"dignity": "Neutral", "relationship": "Shatru", "yoga": "Neutral/Malefic"},
        "Jupiter": {"dignity": "Neutral", "relationship": "Mithra", "yoga": "Trikona Lord"},
        "Venus": {"dignity": "Neutral", "relationship": "Shatru", "yoga": "Kendra Lord"},
        "Saturn": {"dignity": "Debilitated", "relationship": "Shatru", "yoga": "Kendra Lord"}
    },
    "Taurus": {
        "Sun": {"dignity": "Neutral", "relationship": "Shatru", "yoga": "Kendra Lord"},
        "Moon": {"dignity": "Neutral", "relationship": "Mithra", "yoga": "Trikona Lord"},
        "Mars": {"dignity": "Neutral", "relationship": "Shatru", "yoga": "Kendra Lord"},
        "Mercury": {"dignity": "Swa-Kshetra", "relationship": "Mithra", "yoga": "Trikona Lord"},
        "Jupiter": {"dignity": "Neutral", "relationship": "Shatru", "yoga": "Neutral/Malefic"},
        "Venus": {"dignity": "Swa-Kshetra", "relationship": "Mithra", "yoga": "Kendra Lord"},
        "Saturn": {"dignity": "Swa-Kshetra", "relationship": "Mithra", "yoga": "Yogakaraka (Strongest)"}
    },
    "Gemini": {
        "Sun": {"dignity": "Neutral", "relationship": "Mithra", "yoga": "Kendra Lord"},
        "Moon": {"dignity": "Neutral", "relationship": "Shatru", "yoga": "Kendra Lord"},
        "Mars": {"dignity": "Neutral", "relationship": "Shatru", "yoga": "Neutral/Malefic"},
        "Mercury": {"dignity": "Swa-Kshetra", "relationship": "Mithra", "yoga": "Kendra Lord"},
        "Jupiter": {"dignity": "Neutral", "relationship": "Shatru", "yoga": "Kendra Lord"},
        "Venus": {"dignity": "Neutral", "relationship": "Mithra", "yoga": "Trikona Lord"},
        "Saturn": {"dignity": "Neutral", "relationship": "Mithra", "yoga": "Trikona Lord"}
    },
    "Cancer": {
        "Sun": {"dignity": "Neutral", "relationship": "Mithra", "yoga": "Kendra Lord"},
        "Moon": {"dignity": "Swa-Kshetra", "relationship": "Mithra", "yoga": "Kendra Lord"},
        "Mars": {"dignity": "Exalted", "relationship": "Mithra", "yoga": "Yogakaraka (Strongest)"},
        "Mercury": {"dignity": "Neutral", "relationship": "Shatru", "yoga": "Neutral/Malefic"},
        "Jupiter": {"dignity": "Exalted", "relationship": "Mithra", "yoga": "Trikona Lord"},
        "Venus": {"dignity": "Neutral", "relationship": "Shatru", "yoga": "Kendra Lord"},
        "Saturn": {"dignity": "Neutral", "relationship": "Shatru", "yoga": "Kendra Lord"}
    },
    "Leo": {
        "Sun": {"dignity": "Swa-Kshetra", "relationship": "Mithra", "yoga": "Kendra Lord"},
        "Moon": {"dignity": "Neutral", "relationship": "Mithra", "yoga": "Kendra Lord"},
        "Mars": {"dignity": "Neutral", "relationship": "Mithra", "yoga": "Yogakaraka (Strongest)"},
        "Mercury": {"dignity": "Neutral", "relationship": "Neutral", "yoga": "Neutral/Malefic"},
        "Jupiter": {"dignity": "Neutral", "relationship": "Mithra", "yoga": "Trikona Lord"},
        "Venus": {"dignity": "Neutral", "relationship": "Shatru", "yoga": "Kendra Lord"},
        "Saturn": {"dignity": "Neutral", "relationship": "Shatru", "yoga": "Kendra Lord"}
    },
    "Virgo": {
        "Sun": {"dignity": "Neutral", "relationship": "Mithra", "yoga": "Kendra Lord"},
        "Moon": {"dignity": "Neutral", "relationship": "Shatru", "yoga": "Kendra Lord"},
        "Mars": {"dignity": "Neutral", "relationship": "Shatru", "yoga": "Neutral/Malefic"},
        "Mercury": {"dignity": "Swa-Kshetra", "relationship": "Mithra", "yoga": "Kendra Lord"},
        "Jupiter": {"dignity": "Debilitated", "relationship": "Shatru", "yoga": "Kendra Lord"},
        "Venus": {"dignity": "Exalted", "relationship": "Mithra", "yoga": "Trikona Lord"},
        "Saturn": {"dignity": "Neutral", "relationship": "Mithra", "yoga": "Trikona Lord"}
    },
    "Libra": {
        "Sun": {"dignity": "Debilitated", "relationship": "Shatru", "yoga": "Kendra Lord"},
        "Moon": {"dignity": "Neutral", "relationship": "Shatru", "yoga": "Kendra Lord"},
        "Mars": {"dignity": "Neutral", "relationship": "Neutral", "yoga": "Kendra Lord"},
        "Mercury": {"dignity": "Neutral", "relationship": "Mithra", "yoga": "Kendra Lord"},
        "Jupiter": {"dignity": "Neutral", "relationship": "Shatru", "yoga": "Kendra Lord"},
        "Venus": {"dignity": "Swa-Kshetra", "relationship": "Mithra", "yoga": "Kendra Lord"},
        "Saturn": {"dignity": "Exalted", "relationship": "Mithra", "yoga": "Yogakaraka (Strongest)"}
    },
    "Scorpio": {
        "Sun": {"dignity": "Neutral", "relationship": "Mithra", "yoga": "Kendra Lord"},
        "Moon": {"dignity": "Neutral", "relationship": "Mithra", "yoga": "Trikona Lord"},
        "Mars": {"dignity": "Swa-Kshetra", "relationship": "Mithra", "yoga": "Kendra Lord"},
        "Mercury": {"dignity": "Neutral", "relationship": "Shatru", "yoga": "Neutral/Malefic"},
        "Jupiter": {"dignity": "Neutral", "relationship": "Mithra", "yoga": "Trikona Lord"},
        "Venus": {"dignity": "Neutral", "relationship": "Shatru", "yoga": "Kendra Lord"},
        "Saturn": {"dignity": "Neutral", "relationship": "Shatru", "yoga": "Kendra Lord"}
    },
    "Sagittarius": {
        "Sun": {"dignity": "Neutral", "relationship": "Mithra", "yoga": "Trikona Lord"},
        "Moon": {"dignity": "Neutral", "relationship": "Mithra", "yoga": "Kendra Lord"},
        "Mars": {"dignity": "Neutral", "relationship": "Mithra", "yoga": "Trikona Lord"},
        "Mercury": {"dignity": "Neutral", "relationship": "Shatru", "yoga": "Neutral/Malefic"},
        "Jupiter": {"dignity": "Swa-Kshetra", "relationship": "Mithra", "yoga": "Kendra Lord"},
        "Venus": {"dignity": "Neutral", "relationship": "Shatru", "yoga": "Kendra Lord"},
        "Saturn": {"dignity": "Neutral", "relationship": "Mithra", "yoga": "Kendra Lord"}
    },
    "Capricorn": {
        "Sun": {"dignity": "Neutral", "relationship": "Shatru", "yoga": "Kendra Lord"},
        "Moon": {"dignity": "Neutral", "relationship": "Shatru", "yoga": "Kendra Lord"},
        "Mars": {"dignity": "Exalted", "relationship": "Neutral", "yoga": "Kendra Lord"},
        "Mercury": {"dignity": "Neutral", "relationship": "Mithra", "yoga": "Trikona Lord"},
        "Jupiter": {"dignity": "Debilitated", "relationship": "Shatru", "yoga": "Kendra Lord"},
        "Venus": {"dignity": "Neutral", "relationship": "Mithra", "yoga": "Yogakaraka (Strongest)"},
        "Saturn": {"dignity": "Swa-Kshetra", "relationship": "Mithra", "yoga": "Kendra Lord"}
    },
    "Aquarius": {
        "Sun": {"dignity": "Neutral", "relationship": "Shatru", "yoga": "Kendra Lord"},
        "Moon": {"dignity": "Neutral", "relationship": "Shatru", "yoga": "Kendra Lord"},
        "Mars": {"dignity": "Neutral", "relationship": "Neutral", "yoga": "Kendra Lord"},
        "Mercury": {"dignity": "Neutral", "relationship": "Mithra", "yoga": "Trikona Lord"},
        "Jupiter": {"dignity": "Neutral", "relationship": "Shatru", "yoga": "Kendra Lord"},
        "Venus": {"dignity": "Neutral", "relationship": "Mithra", "yoga": "Yogakaraka (Strongest)"},
        "Saturn": {"dignity": "Swa-Kshetra", "relationship": "Mithra", "yoga": "Kendra Lord"}
    },
    "Pisces": {
        "Sun": {"dignity": "Neutral", "relationship": "Mithra", "yoga": "Kendra Lord"},
        "Moon": {"dignity": "Exalted", "relationship": "Mithra", "yoga": "Trikona Lord"},
        "Mars": {"dignity": "Neutral", "relationship": "Mithra", "yoga": "Trikona Lord"},
        "Mercury": {"dignity": "Debilitated", "relationship": "Shatru", "yoga": "Neutral/Malefic"},
        "Jupiter": {"dignity": "Swa-Kshetra", "relationship": "Mithra", "yoga": "Kendra Lord"},
        "Venus": {"dignity": "Exalted", "relationship": "Shatru", "yoga": "Kendra Lord"},
        "Saturn": {"dignity": "Neutral", "relationship": "Mithra", "yoga": "Kendra Lord"}
    }
}

def get_expected_data(lagna, planet):
    return EXPECTED_DATA.get(lagna, {}).get(planet, {"dignity": "Unknown", "relationship": "Unknown", "yoga": "Unknown"})