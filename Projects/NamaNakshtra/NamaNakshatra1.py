from aksharamukha import transliterate

# Mapping table: (Nakshatra, Pada)
# Format: { "starting_sound": ("Nakshatra", Pada) }
nakshatra_table = {
    # Ashwini
    "చు": ("Ashwini", 1), "చే": ("Ashwini", 2), "చో": ("Ashwini", 3), "లా": ("Ashwini", 4),
    # Bharani
    "లీ": ("Bharani", 1), "లూ": ("Bharani", 2), "లే": ("Bharani", 3), "లో": ("Bharani", 4),
    # Krittika
    "ఆ": ("Krittika", 1), "ఈ": ("Krittika", 2), "ఊ": ("Krittika", 3), "ఏ": ("Krittika", 4),
    # Rohini
    "ఓ": ("Rohini", 1), "వా": ("Rohini", 2), "వీ": ("Rohini", 3), "వూ": ("Rohini", 4),
    # Mrigashira
    "వే": ("Mrigashira", 1), "వో": ("Mrigashira", 2), "కా": ("Mrigashira", 3), "కీ": ("Mrigashira", 4),
    # Arudra
    "కూ": ("Arudra", 1), "ఘ": ("Arudra", 2), "ఙ": ("Arudra", 3), "ఛ": ("Arudra", 4),
    # Punarvasu
    "కే": ("Punarvasu", 1), "కో": ("Punarvasu", 2), "హా": ("Punarvasu", 3), "హీ": ("Punarvasu", 4),
    # Add more as needed...
}

def get_nama_nakshatra(input_name):
    # 1. Detect if input is English and convert to Telugu
    # We use 'IAST' or 'ISO' for clean phonetic mapping
    telugu_name = transliterate.process('autodetect', 'Telugu', input_name)
    
    # 2. Get the first phonetic unit (the 'Akshara')
    # Telugu characters are often multi-byte, so we take the first 1-2 chars
    first_char = telugu_name[0]
    if len(telugu_name) > 1 and telugu_name[1] in 'ాిీుూృౄెేైొోౌ్':
        search_key = telugu_name[:2]
    else:
        search_key = first_char

    # 3. Lookup in table
    result = nakshatra_table.get(search_key)
    
    return telugu_name, search_key, result

# Testing the script
name_input = input("Enter Name (Telugu or English): ")
t_name, key, info = get_nama_nakshatra(name_input)

print(f"\nConverted Name: {t_name}")
print(f"Starting Sound: {key}")

if info:
    print(f"Result -> Nakshatra: {info[0]}, Pada: {info[1]}")
else:
    print("Sound not found in the current mapping table.")