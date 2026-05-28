import re
from flask import Flask, request, jsonify, render_template_string
from indic_transliteration import sanscript
from indic_transliteration.sanscript import transliterate

# =========================
# GENERATE MULTIPLE PHONETIC VARIANTS
# =========================
def generate_variants(name):
    name = name.lower()

    variants = set()
    variants.add(name)

    # phonetic variations
    variants.add(name.replace("s", "sh"))
    variants.add(name.replace("sh", "s"))

    variants.add(name.replace("aa", "a"))
    variants.add(name.replace("ee", "i"))
    variants.add(name.replace("oo", "u"))

    variants.add(name.replace("ri", "ree"))
    variants.add(name.replace("ree", "ri"))

    variants.add(name.replace("sw", "shw"))
    variants.add(name.replace("shw", "sw"))

    return list(variants)


# =========================
# TRANSLITERATE EACH WORD
# =========================
def word_to_telugu(word):
    results = []

    variants = generate_variants(word)

    for v in variants:
        try:
            tel = transliterate(v, sanscript.ITRANS, sanscript.TELUGU)
            tel = re.sub(r'[a-zA-Z]', '', tel)
            if tel:
                results.append(tel)
        except:
            pass

    return list(set(results))


# =========================
# FULL NAME → MULTIPLE OPTIONS
# =========================
def to_telugu_options(name):
    words = name.split()

    all_word_options = [word_to_telugu(w) for w in words]

    # combine words (simple cartesian)
    combined = []

    def build(idx, path):
        if idx == len(all_word_options):
            combined.append(" ".join(path))
            return
        for w in all_word_options[idx]:
            build(idx + 1, path + [w])

    build(0, [])

    return combined[:10]  # limit


# =========================
# GET AKSHARA
# =========================
def get_akshara(word):
    first_word = word.split()[0]
    match = re.match(r'^([\u0C15-\u0C39][\u0C3E-\u0C4C]?|[\u0C05-\u0C14])', first_word)
    return match.group(1) if match else None


# =========================
# NAKSHATRA MAP
# =========================
NAKSHATRA = {
    "Ashwini": ["చు","చే","చో","లా"],
    "Bharani": ["లి","లు","లే","లో"],
    "Krittika": ["అ","ఈ","ఉ","ఏ"],
    "Rohini": ["ఓ","వా","వి","వు"],
    "Mrigashira": ["వే","వో","కా","కి"],
    "Arudra": ["కు","ఘ","ఙ","చ"],
    "Punarvasu": ["కే","కో","హా","హి"],
    "Pushya": ["హు","హే","హో","డా"],
    "Ashlesha": ["డి","డు","డే","డో"],
    "Magha": ["మా","మి","ము","మే"],
    "Purva Phalguni": ["మో","టా","టి","టు"],
    "Uttara Phalguni": ["టే","టో","పా","పి"],
    "Hasta": ["పు","ష","ణ","థ"],
    "Chitra": ["పే","పో","రా","రి"],
    "Swati": ["రు","రే","రో","తా"],
    "Vishakha": ["తి","తు","తే","తో"],
    "Anuradha": ["నా","ని","ను","నే"],
    "Jyeshtha": ["నో","యా","యి","యు"],
    "Moola": ["యే","యో","బా","బి"],
    "Purvashada": ["బు","ధా","భా","ధి"],
    "Uttarashada": ["భే","భో","జా","జి"],
    "Shravana": ["జు","జే","జో","ఖి"],
    "Dhanishta": ["గా","గి","గు","గే"],
    "Shatabhisha": ["గో","సా","సి","సు"],
    "Purvabhadra": ["సే","సో","దా","ది"],
    "Uttarabhadra": ["దు","థా","ఝా","నా"],
    "Revati": ["దే","దో","చా","చి"]
}


# =========================
# FIND NAKSHATRA
# =========================
def find_nakshatra(ak):
    if not ak:
        return "Unknown"

    for nak, sounds in NAKSHATRA.items():
        if ak in sounds:
            return nak

    base = ak[0]
    for nak, sounds in NAKSHATRA.items():
        for s in sounds:
            if s.startswith(base):
                return nak

    return "Unknown"


# =========================
# PROCESS
# =========================
def process(name):
    options = to_telugu_options(name)

    results = []
    for opt in options:
        ak = get_akshara(opt)
        nak = find_nakshatra(ak)

        results.append({
            "telugu": opt,
            "akshara": ak,
            "nakshatra": nak
        })

    return results


# =========================
# FLASK UI
# =========================
app = Flask(__name__)

HTML = """
<h2>Smart Nakshatra Finder (Keyboard Style)</h2>

<form method="GET" action="/nakshatra">
<input name="name" placeholder="Enter Name">
<button>Find</button>
</form>

{% if results %}
<h3>Choose Correct Telugu Name:</h3>
<ul>
{% for r in results %}
<li>
<b>{{r.telugu}}</b> → {{r.nakshatra}}
</li>
{% endfor %}
</ul>
{% endif %}
"""

@app.route("/")
def home():
    return render_template_string(HTML)

@app.route("/nakshatra")
def nak():
    name = request.args.get("name")
    results = process(name)
    return render_template_string(HTML, results=results)

@app.route("/api")
def api():
    name = request.args.get("name")
    return jsonify(process(name))


# =========================
# RUN
# =========================
if __name__ == "__main__":
    app.run(debug=True)