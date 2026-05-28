import sys
import io
import re
from aksharamukha import transliterate

# --- WINDOWS UNICODE FIX ---
# This forces the Python output to use UTF-8 regardless of terminal settings
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.stdin = io.TextIOWrapper(sys.stdin.buffer, encoding='utf-8')

"""
REFERENCE: NAMA NAKSHATRA TELUGU TABLE (108 PADAS)
--------------------------------------------------
1.  Ashwini:      చు (Chu), చే (Che), చో (Cho), లా (La)
2.  Bharani:      లీ (Lee), లూ (Lu), లే (Le), లో (Lo)
3.  Krittika:     ఆ (A), ఈ (Ee), ఊ (U), ఏ (E)
4.  Rohini:       ఓ (O), వా (Va), వీ (Vi), వూ (Vu)
5.  Mrigashira:   వే (Ve), వో (Vo), కా (Ka), కీ (Ki)
6.  Arudra:       కూ (Ku), ఘ (Gha), ఙ (Ng), ఛ (Chha)
7.  Punarvasu:    కే (Ke), కో (Ko), హా (Ha), హీ (Hi)
8.  Pushyami:     హూ (Hu), హే (He), హో (Ho), డా (Da)
9.  Aslesha:      డీ (Dee), డూ (Du), డే (De), డో (Do)
10. Magha:        మా (Ma), మీ (Mee), మూ (Mu), మే (Me)
11. Purva Phalg:  మో (Mo), టా (Ta), టీ (Ti), టూ (Tu)
12. Uttara Phalg: టే (Te), టో (To), పా (Pa), పీ (Pi)
13. Hasta:        పూ (Pu), ష (Sha), ణ (Na), ఠ (Tha)
14. Chitra:       పే (Pe), పో (Po), రా (Ra), రీ (Ri)
15. Swati:        రూ (Ru), రే (Re), రో (Ro), తా (Ta)
16. Vishakha:     తీ (Ti), తూ (Tu), తే (Te), తో (To)
17. Anuradha:     నా (Na), నీ (Ni), నూ (Nu), నే (Ne)
18. Jyeshtha:     నో (No), యా (Ya), యీ (Yi), యూ (Yu)
19. Moola:        యే (Ye), యో (Yo), బా (Ba), బీ (Bi)
20. Purvashada:   బూ (Bu), ధా (Dha), ఫా (Pha), డా (Da)
21. Uttarashada:  బే (Be), బో (Bo), జా (Ja), జీ (Ji)
22. Shravana:     ఖీ (Khi), ఖూ (Khu), ఖే (Khe), ఖో (Kho)
23. Dhanishta:    గా (Ga), గీ (Gi), గూ (Gu), గే (Ge)
24. Shatabhisha:  గో (Go), సా (Sa), సీ (Si), సూ (Su)
25. Purvabhadra:  సే (Se), సో (So), దా (Da), దీ (Di)
26. Uttarabhadra: దూ (Du), థ (Tha), ఝ (Jha), ఞ (Na)
27. Revati:       దే (De), దో (Do), చా (Cha), చీ (Chi)
--------------------------------------------------
"""

VOWEL_MAP = {
    'ా': 'ఆ', 'ి': 'ఇ', 'ీ': 'ఈ', 'ు': 'ఉ', 'ూ': 'ఊ', 
    'ృ': 'ఋ', 'ె': 'ఎ', 'ే': 'ఏ', 'ై': 'ఐ', 'ొ': 'ఒ', 'ో': 'ఓ', 'ౌ': 'ఔ', '్': ''
}

NAKSHATRA_MATRIX = {
    "చ": {"ఉ": ("Ashwini", 1), "ఊ": ("Ashwini", 1), "ఎ": ("Ashwini", 2), "ఏ": ("Ashwini", 2), "ఒ": ("Ashwini", 3), "ఓ": ("Ashwini", 3), "అ": ("Revati", 3), "ఆ": ("Revati", 3), "ఇ": ("Revati", 4), "ఈ": ("Revati", 4)},
    "ల": {"అ": ("Ashwini", 4), "ఆ": ("Ashwini", 4), "ఇ": ("Bharani", 1), "ఈ": ("Bharani", 1), "ఉ": ("Bharani", 2), "ఊ": ("Bharani", 2), "ఎ": ("Bharani", 3), "ఏ": ("Bharani", 3), "ఒ": ("Bharani", 4), "ఓ": ("Bharani", 4)},
    "అ": {"అ": ("Krittika", 1), "ఆ": ("Krittika", 1), "ఇ": ("Krittika", 2), "ఈ": ("Krittika", 2), "ఉ": ("Krittika", 3), "ఊ": ("Krittika", 3), "ఎ": ("Krittika", 4), "ఏ": ("Krittika", 4)},
    "వ": {"ఒ": ("Rohini", 1), "ఓ": ("Rohini", 1), "అ": ("Rohini", 2), "ఆ": ("Rohini", 2), "ఇ": ("Rohini", 3), "ఈ": ("Rohini", 3), "ఉ": ("Rohini", 4), "ఊ": ("Rohini", 4), "ఎ": ("Mrigashira", 1), "ఏ": ("Mrigashira", 1), "ఒ": ("Mrigashira", 2), "ఓ": ("Mrigashira", 2)},
    "క": {"అ": ("Mrigashira", 3), "ఆ": ("Mrigashira", 3), "ఇ": ("Mrigashira", 4), "ఈ": ("Mrigashira", 4), "ఉ": ("Arudra", 1), "ఊ": ("Arudra", 1), "ఎ": ("Punarvasu", 1), "ఏ": ("Punarvasu", 1), "ఒ": ("Punarvasu", 2), "ఓ": ("Punarvasu", 2)},
    "హ": {"అ": ("Punarvasu", 3), "ఆ": ("Punarvasu", 3), "ఇ": ("Punarvasu", 4), "ఈ": ("Punarvasu", 4), "ఉ": ("Pushyami", 1), "ఊ": ("Pushyami", 1), "ఎ": ("Pushyami", 2), "ఏ": ("Pushyami", 2), "ఒ": ("Pushyami", 3), "ఓ": ("Pushyami", 3)},
    "ర": {"అ": ("Chitra", 3), "ఆ": ("Chitra", 3), "ఇ": ("Chitra", 4), "ఈ": ("Chitra", 4), "ఉ": ("Swati", 1), "ఊ": ("Swati", 1), "ఎ": ("Swati", 2), "ఏ": ("Swati", 2), "ఒ": ("Swati", 3), "ఓ": ("Swati", 3)},
    "న": {"అ": ("Anuradha", 1), "ఆ": ("Anuradha", 1), "ఇ": ("Anuradha", 2), "ఈ": ("Anuradha", 2), "ఉ": ("Anuradha", 3), "ఊ": ("Anuradha", 3), "ఎ": ("Anuradha", 4), "ఏ": ("Anuradha", 4)},
    "ప": {"ఎ": ("Hasta", 1), "ఏ": ("Hasta", 1), "ఒ": ("Hasta", 2), "ఓ": ("Hasta", 2), "అ": ("Uttara Phalguni", 2), "ఆ": ("Uttara Phalguni", 2), "ఇ": ("Uttara Phalguni", 3), "ఈ": ("Uttara Phalguni", 3), "ఉ": ("Uttara Phalguni", 4), "ఊ": ("Uttara Phalguni", 4)},
}

def get_nama_nakshatra(input_name):
    # Transliterate and normalize
    tel_name = transliterate.process('autodetect', 'Telugu', input_name).replace("ఱ", "ర")
    
    # Regex extraction
    match = re.match(r'^([\u0C05-\u0C39])([\u0C3E-\u0C4D]?)', tel_name)
    
    if not match:
        return tel_name, "Error", None

    char = match.group(1)
    sign = match.group(2)
    
    if '\u0C05' <= char <= '\u0C14':
        family = "అ"
        vowel_base = char
    else:
        family = char
        vowel_base = VOWEL_MAP.get(sign, "అ")

    family_data = NAKSHATRA_MATRIX.get(family)
    if family_data:
        result = family_data.get(vowel_base)
        return tel_name, f"{family} family ({vowel_base})", result
    
    return tel_name, f"{family} family", None

# --- TESTING LOOP ---
print("--- Nama Nakshatra Automated Tester ---")
print("NOTE: If you see boxes instead of Telugu, please change your CMD font to 'MS Gothic' or 'Courier New'.\n")

while True:
    try:
        name_in = input("Enter Name (or 'exit'): ")
        if name_in.lower() == 'exit': break
        
        t_name, logic_info, info = get_nama_nakshatra(name_in)
        
        print(f"Telugu: {t_name} | Logic: {logic_info}")
        if info:
            print(f"RESULT: {info[0]} Nakshatra, Pada {info[1]}")
        else:
            print("RESULT: Sound family or vowel not yet mapped.")
        print("-" * 20)
    except Exception as e:
        print(f"Error processing name: {e}")